import datetime
import json
import os
import traceback
from pathlib import Path
from langchain_openai import ChatOpenAI
import yaml
import tqdm
from langchain_community.document_loaders import UnstructuredEmailLoader, OutlookMessageLoader
from langchain_core.document_loaders import BaseLoader
from modules.utils.ocr_handler import OCRHandler
from modules.message_classification import MessageClassifier
from modules.message_segmentation import MessageSegmenter
from modules.key_information_extraction import TextKIE
from modules.key_information_validation import KIValidation

from modules.utils.bx_utils import BXApis
from modules.vehicle_deduplication import VehicleDeduplicator

from modules.Feishu.Feishu_spreadsheet import FeishuSpreadsheetHandler
from modules.Feishu.Feishu_messages import FeishuMessageHandler
from glob import glob
from loguru import logger

from langchain_core.documents import Document
from typing import Union
from retrying import retry

MODEL_NAME = 'glm-4-flash'
API_TOKEN = 'a9d2815b090f143cdac247d7600a127f.WSDK8WqwJzZtCmBK'


class StringListLoader(BaseLoader):
    def __init__(self, strings: list) -> None:
        self.strings = strings

    def lazy_load(self):
        for string in self.strings:
            yield Document(page_content=string)


class ShipmentFlow:
    def __init__(self, feishu_config_path):
        self.ocr_engine = OCRHandler()
        self.message_classifier = MessageClassifier()
        self.message_segmenter = MessageSegmenter()
        self.email_storage_path = Path(__file__).parent / 'src' / 'all_mixed_emails'
        self.rule_config_path = Path(__file__).parent / 'extraction_rules'
        llm_ins = self.create_llm_instance()
        self.kie_instance = TextKIE(llm_ins)
        self.ki_validator = KIValidation()
        self.feishu_spreadsheet_handler = FeishuSpreadsheetHandler(feishu_config_path)
        self.feishu_message_handler = FeishuMessageHandler(feishu_config_path)
        self.bx_handler = BXApis()
        self.shipment_dedup = VehicleDeduplicator()

        with open(feishu_config_path, 'r') as f:
            configs = yaml.load(f, Loader=yaml.FullLoader)
        self.tables = configs.get('table', {})
        self.templates = configs.get('template', {})
        self.chat_ids = configs.get('chat_id', {})

    def process_msg_dicts(self, msg_dicts):
        msgs = []
        for msg_dict in msg_dicts:
            event = msg_dict.get('event', {})
            event_id = msg_dict.get('header', {}).get('event_id')
            current_date = datetime.datetime.now().strftime("%Y-%m-%d")

            target_folder = Path(__file__).parent.parent / 'src' / 'input' / current_date / event_id
            if target_folder.exists():
                logger.warning("event_id exists.")
                continue
            os.makedirs(target_folder, exist_ok=True)
            message = event.get('message', {})
            chat_type = message.get('chat_type')
            message_type = message.get('message_type')
            logger.info([event, event_id, chat_type, message_type])
            if not chat_type:
                logger.error("Chat type is not mentioned.")
                continue
            if chat_type == 'p2p':
                sender_id = event.get('sender', {}).get('sender_id', {}).get('open_id')
                receive_id = sender_id
                receive_type = 'chat_id'
            elif chat_type == 'group':
                receive_id = message.get('chat_id')
                receive_type = 'chat_id'
                mentions = message.get('mentions', [])
                if message_type == 'text' and '16c5228b4a88575e' not in [i.get('tenant_key', '') for i in mentions]:
                    logger.error(f"Not mention current bot. Skipped.{[i.get('name', 'Unknown') for i in mentions]}")
                    continue
            elif chat_type == 'post':
                receive_id = message.get('chat_id')
                receive_type = 'chat_id'

            else:
                logger.error(f"Unknown chat_type: {chat_type}")
                continue

            if message_type == 'text':
                content_str = message.get('content')
                content = json.loads(content_str) if content_str else {}
                content = content.get('text')
                with open(target_folder / 'input_text.txt', 'w', encoding='utf-8') as f:
                    f.write(content)

                res = self.unit_flow(document_path=None, content=content, receive_id=receive_id,
                                     receive_type=receive_type)
                if res:
                    msgs.append(res)
            elif message_type == 'file':
                message_id = message.get('message_id')
                content_str = message.get('content')
                content = json.loads(content_str) if content_str else {}
                file_key = content.get('file_key')
                # target_folder = Path(__file__).parent.parent / 'src' / 'input' / current_date / event_id
                # os.makedirs(target_folder, exist_ok=True)
                file_path = self.feishu_message_handler.retrieve_file(message_id, file_key, target_folder)
                logger.info(f"Document {file_path.name} received.")
                # current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # rich_text_log = (
                #     f'<b>【上传文件接收成功】</b>\n'
                #     f'<b><font color="green"><b>{file_path.name}接收成功</b></font>\n'
                #     f'<b>【时间】</b>: {current_time}'
                # )
                # self.feishu_message_handler.send_message_by_template(receive_id=receive_id,
                #                                                      template_id='AAq7OhvOhSJB2',
                #                                                      template_variable={'log_rich_text': rich_text_log},
                #                                                      receive_id_type=receive_type)
                res = self.unit_flow(document_path=str(file_path), content=None, receive_id=receive_id,
                                     receive_type=receive_type)
                if res:
                    msgs.append(res)
            elif message_type == 'image':
                message_id = message.get('message_id')
                content_str = message.get('content')
                content = json.loads(content_str) if content_str else {}
                file_key = content.get('image_key')
                # target_folder = Path(__file__).parent.parent / 'src' / 'input' / current_date / event_id
                # os.makedirs(target_folder, exist_ok=True)
                file_path = self.feishu_message_handler.retrieve_file(message_id, file_key, target_folder,
                                                                      file_type='image')
                logger.info(f"Document {file_path.name} received.")
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                rich_text_log = (
                    f'<b>【上传文件接收成功】</b>\n'
                    f'<b><font color="green"><b>{file_path.name}接收成功</b></font>\n'
                    f'<b>【时间】</b>: {current_time}'
                )
                self.feishu_message_handler.send_message_by_template(receive_id=receive_id,
                                                                     template_id='AAq7OhvOhSJB2',
                                                                     template_variable={'log_rich_text': rich_text_log},
                                                                     receive_id_type=receive_type)
                res = self.unit_flow(document_path=str(file_path), content=None, receive_id=receive_id,
                                     receive_type=receive_type)
                if res:
                    msgs.append(res)
            else:
                logger.error(f"Unknown message_type: {message_type}")
                continue
        return msgs

    @staticmethod
    def create_llm_instance(model_name=MODEL_NAME):
        return ChatOpenAI(temperature=0.95,
                          model=model_name,
                          openai_api_key=API_TOKEN,
                          openai_api_base="https://open.bigmodel.cn/api/paas/v4/")

    def collect_emails(self):
        messages = glob(str(self.email_storage_path / '**' / '*.eml'), recursive=True)
        return messages

    def load_document(self, document_path: Path, content: Union[str, None]):
        if document_path:
            logger.info(f"->     Starts to load document from {document_path}.")
            if document_path.suffix == '.eml':
                logger.success("Loaded by Email format")
                return UnstructuredEmailLoader(str(document_path))
            if document_path.suffix == '.msg':
                logger.success("Loaded by OutlookEmail format")
                return OutlookMessageLoader(str(document_path))
            if document_path.suffix in ['.png', '.jpg']:
                logger.success("Loaded by image format")
                raw_contents = self.ocr_engine.get_ocr_result_by_block(document_path, if_debug=True, crop_method=0)
                return StringListLoader(raw_contents)
        elif content:
            logger.success("Loaded by text format")
            return StringListLoader([content])
        else:
            logger.error(f"Unknown input :{document_path} {content}")
            return None

    @staticmethod
    def get_data_loader_context(document_loader):
        data = document_loader.load()
        contents_list = [i.__dict__ for i in data]
        metadata_set = set(Path(i.__dict__.get('metadata', {}).get('source')).stem for i in data if
                           i.__dict__.get('metadata', {}).get('source'))
        return contents_list, list(metadata_set) + [i.__dict__.get('page_content') for i in data if
                                                    i.__dict__.get('page_content')] + list(metadata_set)

    @retry(stop_max_attempt_number=2, wait_fixed=2000)
    def classify_document(self, document_loader):
        data = document_loader.load()
        contents_list = [json.dumps(i.__dict__, ensure_ascii=False, indent=2) for i in data]
        content_str = '\n'.join(contents_list)
        document_type, reason, entry_count = self.message_classifier.classify(content_str)

        return document_type, reason, entry_count

    def extract_key_information(self, document_loader, document_type, entry_count: int, extra_info: str):
        logger.info(f"->     Starts to extract key information from {document_type}.")
        if document_type == 'others':
            logger.warning("Message type is OTHER. DO NOT PARSE. SKIPPED.")
            return None
        elif document_type == 'ship_info':
            config_path = self.rule_config_path / 'ship_related_default.yaml'
        elif document_type == 'cargo_info':
            config_path = self.rule_config_path / 'cargo_offer_default.yaml'
        logger.info(f"Config_path: {config_path}")
        # Message Segmentation
        # data = document_loader.load()
        _, contents_list = self.get_data_loader_context(document_loader)
        # contents_list = [json.dumps(i.__dict__, ensure_ascii=False, indent=2) for i in data]
        content_str = '\n'.join(contents_list)
        content_str += f'\n原文得一些总结和分析：{extra_info}'
        if entry_count == 1:
            vessel_info_chunks, mutual_info, comment = [content_str], '', 'Only one entry'
        else:
            try:
                vessel_info_chunks, mutual_info, comment = self.message_segmenter.segment(content_str, document_type,
                                                                                          entry_count)
            except Exception as e:
                logger.error(
                    f"[Segmentation]    Failed to segment message, will treat as single paragraph. Note: {str(e)}")
                vessel_info_chunks = [content_str]
                mutual_info = ''
                # comment = f"[Segmentation]    Failed to segment message, will treat as single paragraph. Note: {str(e)}"
        # Do extraction:
        ## By serial
        outs = []
        for vessel_info_chunk in tqdm.tqdm(vessel_info_chunks):
            text_lines = ["参考原文：" + content_str,
                          '本次提取任务重点放在下面的部分: ' + vessel_info_chunk] if entry_count > 1 else [content_str]
            modified_outputs = self.kie_instance(rule_config_path=str(config_path),
                                                 file_type=document_type,
                                                 # text_lines=[mutual_info, vessel_info_chunk]
                                                 text_lines=text_lines
                                                 )
            outs.append([modified_outputs[0], vessel_info_chunk, mutual_info])
        logger.success(json.dumps(outs, indent=2, ensure_ascii=False))
        return outs

    @retry(stop_max_attempt_number=2, wait_fixed=2000)
    def validate_key_information(self, document_type, extraction_res):
        logger.info("Starts to Validate results.")
        modified_res = self.ki_validator.validate(document_type=document_type,
                                                  extraction_res=extraction_res)
        logger.info("=>         Validation finished.")
        return modified_res

    def debug_batch(self, document_paths=None, steps=None):
        if not document_paths:
            document_paths = self.collect_emails()
        for document_path in tqdm.tqdm(document_paths):
            document_loader = self.load_document(Path(document_path))
            document_type, reason, entry_count = self.classify_document(document_loader)
            logger.success(
                f"=>     Classify {document_path}: TYPE:{document_type}, ENTRY_COUNT: {entry_count} REASON:{reason}")
            if '船舶数据' in document_path and document_type == 'ship_info':
                logger.success("CORRECT")
            elif '货盘数据' in document_path and document_type == 'cargo_info':
                logger.success('CORRECT')
            else:
                logger.error(f"FALSE: {document_path}: TYPE:{document_type}, REASON:{reason}")
            if steps and 2 not in steps:
                continue

    def add_todo(self):
        pass

    def mark_finish(self):
        pass

    # def insert_data_to_spreadsheet(self, document_path: Union[Path, None], document_type, extraction_res, event_id=None,
    #                                raw_text=None):
    #     data_to_insert = []
    #     for data in extraction_res:
    #         cur_res = data[0]
    #         if raw_text and '备注-REMARK' in cur_res:
    #             cur_res['备注-REMARK'] = raw_text
    #         cur_res['原文依据'] = '\n'.join([data[1] if data[1] else '', data[2] if data[2] else ''])
    #         if raw_text:
    #             cur_res['原文依据'] = raw_text
    #         if event_id:
    #             cur_res['source_name'] = event_id
    #         else:
    #             cur_res['source_name'] = document_path.name if document_path else 'PureText'
    #         data_to_insert.append(cur_res)
    #
    #     logger.info(f"Inserting {data_to_insert}")
    #     if document_type == 'ship_info':
    #         table_id = 'tbly9gtTypeOLQ8Q'
    #     elif document_type == 'cargo_info':
    #         table_id = 'tblSsCLLIEXguHpk'
    #     else:
    #         return
    #     self.feishu_spreadsheet_handler.add_records(app_token='B7XnbQTtLapDfDsJj27c7ZgQnLd',
    #                                                 table_id=table_id,
    #                                                 records=data_to_insert)
    #     logger.success(f"Inserted for {document_path}")

    def insert_data_to_spreadsheet(self, document_path: Union[Path, None], document_type, extraction_res, event_id=None,
                                   raw_text=None):
        if document_type == 'ship_info':
            data_to_insert = []
            for data in extraction_res:
                cur_res = data[0]
                vessel_name = cur_res.get('船舶英文名称-ENGLISH-NAME')
                vid = self.shipment_dedup.main(vessel_name)
                if not vid:
                    cur_res['船舶代码-ID'] = vessel_name
                    logger.error(traceback.format_exc())

                else:
                    vessel_code = self.bx_handler.get_vessel(vid).get('job_info', {}).get('VesselCode')
                    logger.success(f"{vessel_code} already exists")
                    cur_res['船舶代码-ID'] = vessel_code
                if raw_text and '备注-REMARK' in cur_res:
                    cur_res['备注-REMARK'] = raw_text
                cur_res['原文依据'] = '\n'.join([data[1] if data[1] else '', data[2] if data[2] else ''])
                if raw_text:
                    cur_res['原文依据'] = raw_text
                if event_id:
                    cur_res['source_name'] = event_id
                else:
                    cur_res['source_name'] = document_path.name if document_path else 'PureText'
                data_to_insert.append(cur_res)
            self.feishu_spreadsheet_handler.add_records(app_token='B7XnbQTtLapDfDsJj27c7ZgQnLd',
                                                        table_id='tbly9gtTypeOLQ8Q',
                                                        records=data_to_insert)
        elif document_type == 'cargo_info':
            data_to_insert = []
            for data in extraction_res:
                cur_res = data[0]
                if raw_text and '备注-REMARK' in cur_res:
                    cur_res['备注-REMARK'] = raw_text
                cur_res['原文依据'] = '\n'.join([data[1] if data[1] else '', data[2] if data[2] else ''])
                if raw_text:
                    cur_res['原文依据'] = raw_text
                if event_id:
                    cur_res['source_name'] = event_id
                else:
                    cur_res['source_name'] = document_path.name if document_path else 'PureText'
                data_to_insert.append(cur_res)
            self.feishu_spreadsheet_handler.add_records(app_token='B7XnbQTtLapDfDsJj27c7ZgQnLd',
                                                        table_id='tblSsCLLIEXguHpk',
                                                        records=data_to_insert)
        else:
            return

        logger.success(f"Inserted for {document_path}")

    def insert_data_to_bx(self, document_path: Union[Path, None], document_type, extraction_res, event_id=None,
                          raw_text=None):
        # logger.info(f"Inserting {data_to_insert}")

        if document_type == 'ship_info':
            for data in extraction_res:
                cur_res = data[0]
                data = cur_res
                vessel_name = data.get('船舶英文名称-ENGLISH-NAME')
                vid = self.shipment_dedup.main(vessel_name)
                if not vid:
                    # NEW
                    try:
                        payload = {
                            "VesselCode": vessel_name,
                            "VesselName": vessel_name,
                            "VesselNamec": data.get('船舶中文名称-CHINESE-NAME'),
                            # "IMOCode": None,
                            "VslType": data.get('船舶类型-TYPE'),
                            "VslCreateYear": data.get('建造年份-BUILT-YEAR'),
                            "CarryTonSJ": data.get('载货吨-DWCC', 0),
                            "CarryTon": data.get('载重吨-DWT', 0),
                            "Tons": data.get('总吨位-GRT', 0),
                            "NetTon": data.get('净吨位-NRT', 0),
                            "HoldCapacity2": 0.000000,
                            # "GoodsVolumeSZ": data.get('船舶中文名称-CHINESE-NAME'),
                            # "DSKX": data.get('夏季海水吃水-DRAFT'),
                            "Length": data.get('船长-LOA', 0),
                            "Width": data.get('船宽-BM', 0),
                            "XDeep": data.get('型深-DEPTH', 0),
                            "Step": data.get('船级-CLASS'),
                            "HoldSize": data.get('舱口数量-HATCH', 0),
                            "CabinCount": data.get('舱位数量-HOLD', 0),
                            "Crane": data.get('吊机-GEAR'),
                            "Grab": data.get('抓斗-GRAB'),
                            "FFill": data.get('夏季海水吃水-DRAFT', 0),
                            "DeckCount": data.get('甲板数-DECK', 0),
                            "PAndI": data.get('P&I'),
                            "Carrier": data.get('船东-OWNER'),
                            "Remark": raw_text
                        }
                        for keyname in ["CarryTonSJ", "CarryTon", "Tons", "NetTon", "Length", "Width", "XDeep"
                                        "FFill"]:
                            try:
                                payload[keyname] = float(payload[keyname])
                            except:
                                payload[keyname] = None
                        for keyname in ["HoldSize", "CabinCount"]:
                            try:
                                payload[keyname] = int(payload[keyname])
                            except:
                                payload[keyname] = None
                        res = self.bx_handler.add_vessel(payload)
                        logger.success(res)
                        payload2 = {'VesselCode': vessel_name,
                                    'PortNameE': data.get('空船港口-OPEN-PORT'),
                                    'DTDate': data.get('空船日期-OPEN-DATE')}
                        res = self.bx_handler.add_vessel_voy_dt(payload2)
                        logger.success(f"voy_dt ADD to BX: {res}")
                    except:
                        logger.error(traceback.format_exc())

                else:
                    vessel_code = self.bx_handler.get_vessel(vid).get('job_info', {}).get('VesselCode')
                    logger.success(f"{vessel_code} already exists")
                    payload = {'VesselCode': vessel_code,
                               'PortNameE': data.get('空船港口-OPEN-PORT'),
                               'DTDate': data.get('空船日期-OPEN-DATE')}
                    res = self.bx_handler.add_vessel_voy_dt(payload)
                    logger.success(f"voy_dt ADD to BX: {res}")
        elif document_type == 'cargo_info':
            for data in extraction_res:
                cur_res = data[0]
                data = cur_res
                try:
                    payload = {'GoodsName': data.get('货物名称-CARGO-NAME'),
                               'Package': data.get('积载包装-SF-PACKAGE'),
                               'PortLoading': data.get('装货港口-L-PORT'),
                               'PortDischarge': data.get('卸货港口-D-PORT'),
                               'ZL': data.get('装率-L-RATE'),
                               'XL': data.get('卸率-D-RATE'),
                               'WeightHT2': data.get('最小货量-QUANTITY', 0),
                               'BeginDate': data.get('装运开始日期-LAY-DATE',
                                                     datetime.datetime.now().strftime('%Y-%m-%d')),
                               'EndDate': data.get('装运结束日期-CANCELING-DATE',
                                                   datetime.datetime.now().strftime('%Y-%m-%d')),
                               'YJBL': float(data.get('佣金-COMM')),
                               'BPCompany': data.get('报盘公司-COMPANY'),
                               'Remark_DZ': raw_text}
                    res = self.bx_handler.add_sa_job(payload=payload)
                    logger.success(f"sa_job ADD to BX: {res}")

                except:
                    logger.error(traceback.format_exc())

        else:
            return

        logger.success(f"Inserted for {document_path}")

    def debug_data_insert(self, data):
        self.insert_data_to_spreadsheet(Path('demo'), 'ship_info', data)

    @staticmethod
    def json_to_code_block(json_data):
        formatted_json = json.dumps(json_data, indent=2, ensure_ascii=False)
        return f'```JSON\n{formatted_json}\n```'

    @staticmethod
    def json_to_html_table(json_data):
        def to_html_table(data):
            if isinstance(data, dict):
                table = '<table border="1">\n'
                table += '  <tr><th>Key</th><th>Value</th></tr>\n'
                for key, value in data.items():
                    table += f'  <tr><td>{key}</td><td>{value}</td></tr>\n'
                table += '</table>\n'
                return table
            elif isinstance(data, list):
                tables = ''
                for item in data:
                    tables += to_html_table(item)
                return tables
            else:
                return str(data)

        return to_html_table(json_data)

    def unit_flow(self, document_path: Union[str, None] = None, content=None, receive_id=None, receive_type=None,
                  task_id=None):
        document_loader = self.load_document(document_path=Path(document_path) if document_path else None,
                                             content=content)
        # current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        task_status_chat_id = self.chat_ids.get("task_status")
        template_id = self.templates.get('rich_text_general_id')
        message_id = None

        # if receive_type and receive_id:
        #     total, content = self.get_data_loader_context(document_loader)
        # rich_text_log = (
        #     f'<b>【task_id: {task_id}】</b>\n'
        #     f'{self.json_to_code_block(total)}\n'
        # )
        # for idx, c in enumerate(content):
        #     rich_text_log += f'\n' + c
        # message_id = self.feishu_message_handler.send_message_by_template(receive_id=task_status_chat_id,
        #                                                                   template_id=template_id,
        #                                                                   template_variable={
        #                                                                       'log_rich_text': rich_text_log},
        #                                                                   receive_id_type=receive_type)

        # Classify
        try:
            document_type, reason, entry_count = self.classify_document(document_loader)
            logger.success(
                f"=>     Classify {document_path if document_path else 'text'}: TYPE:{document_type}, ENTRY_COUNT: {entry_count} REASON:{reason}")
            if receive_type and receive_id:
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                rich_text_log = (
                    f'<b>【邮件主体分类成功】</b>\n'
                    # f'<i>{document_path if document_path else content[:50] + "..."}</i>\n'
                    f'<b>邮件分类：<font color="green"><b>{document_type}</b></font>\n'
                    f'<b>分类原因：<font color="grey"><b>{reason}</b></font>\n'
                    f'<b>正在进行步骤：<font color="blue"><b>关键信息提取</b></font></b>\n'
                    f'<b>【时间】</b>: {current_time}'
                )
                # self.feishu_spreadsheet_handler.add_records()
                self.feishu_message_handler.reply_message_by_template(message_id=message_id,
                                                                      template_id=template_id,
                                                                      template_variable={
                                                                          'log_rich_text': rich_text_log},
                                                                      in_thread=True
                                                                      )
        except Exception as e:
            logger.error(traceback.format_exc())
            if receive_type and receive_id:
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                rich_text_log = (
                    f'<b>【邮件主体分类失败】</b>\n'
                    # f'<i>{document_path if document_path else content[:50] + "..."}</i>\n'
                    f'<b>失败原因：<font color="red"><b>{str(e)}</b></font></b>\n'
                    f'<b>【时间】</b>: {current_time}'
                )
                self.feishu_message_handler.reply_message_by_template(message_id=message_id,
                                                                      template_id=template_id,
                                                                      template_variable={
                                                                          'log_rich_text': rich_text_log},
                                                                      in_thread=True
                                                                      )
            return

        # Extraction
        extraction_res = self.extract_key_information(document_loader=document_loader,
                                                      document_type=document_type,
                                                      entry_count=entry_count,
                                                      extra_info=reason)
        if not extraction_res:
            return
        extraction_res = [] if not extraction_res else extraction_res
        # Validation
        extraction_res = self.validate_key_information(document_type, extraction_res)
        # Display
        logger.success(f"=>      KIE Extraction results: {json.dumps(extraction_res, ensure_ascii=False, indent=2)}")
        if receive_type and receive_id:
            rich_text_log = f'<b>【邮件关键信息提取成功】</b>\n'
            for idx, i in enumerate(extraction_res):
                rich_text_log += f'---------片段 {idx}---------' + '\n' + i[2] + "\n" + i[1]
                rich_text_log += "\n\n" + self.json_to_code_block(i[0])
            logger.warning(rich_text_log)

            self.feishu_message_handler.reply_message_by_template(message_id=message_id,
                                                                  template_id=template_id,
                                                                  template_variable={
                                                                      'log_rich_text': rich_text_log},
                                                                  in_thread=True
                                                                  )

        # INSERTION
        try:
            total, content = self.get_data_loader_context(document_loader)
            self.insert_data_to_spreadsheet(Path(document_path) if document_path else None,
                                            document_type,
                                            extraction_res,
                                            raw_text='\n'.join(content))
            self.insert_data_to_bx(Path(document_path) if document_path else None,
                                   document_type,
                                   extraction_res,
                                   raw_text='\n'.join(content))
            logger.success(f"=>      Data Inserted.")
            # if receive_type and receive_id:
            #     current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            #     rich_text_log = (
            #         f'<b>【关键信息插入多维表成功】</b>\n'
            #         f'<b><font color="green"><b>关键信息插入成功</b></font>\n'
            #         f'<b>【时间】</b>: {current_time}'
            #     )
            #     self.feishu_message_handler.reply_message_by_template(message_id=message_id,
            #                                                           template_id=template_id,
            #                                                           template_variable={
            #                                                               'log_rich_text': rich_text_log},
            #                                                           in_thread=True
            #                                                           )
        except Exception as e:
            logger.error(traceback.format_exc())
            if receive_type and receive_id:
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                rich_text_log = (
                    f'<b>【分类数据插入失败】</b>\n'
                    # f'<i>{document_path if document_path else content[:50] + "..."}</i>\n'
                    f'<b>失败原因：<font color="red"><b>{str(e)}</b></font>\n'
                    f'<b>【时间】</b>: {current_time}'
                )
                self.feishu_message_handler.reply_message_by_template(message_id=message_id,
                                                                      template_id=template_id,
                                                                      template_variable={
                                                                          'log_rich_text': rich_text_log},
                                                                      in_thread=True
                                                                      )
            return
        self.mark_finish()
        return extraction_res

    def main(self, document_paths=None):
        if not document_paths:
            document_paths = self.collect_emails()
        for document_path in tqdm.tqdm(document_paths):
            self.unit_flow(document_path)


if __name__ == "__main__":
    ins = ShipmentFlow(r'W:\Personal_Project\NeiRelated\projects\shipment_solution\configs\feishu_config.yaml')
    ins.unit_flow(
        r'W:\Personal_Project\NeiRelated\projects\shipment_solution\src\emails\货盘数据\tct order(1).eml')
