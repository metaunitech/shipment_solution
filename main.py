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
import hashlib

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
        self.views = configs.get('view', {})
        self.templates = configs.get('template', {})
        self.chat_ids = configs.get('chat_id', {})
        self.app_token = configs.get('app_token')
        extra_knowledge_path = Path(__file__).parent / 'modules' / 'knowledges' / 'uploaded_knowledge.json'
        if extra_knowledge_path.exists():
            with open(extra_knowledge_path, 'r', encoding='utf-8') as f:
                self.extra_knowledge = json.load(f)
        else:
            self.extra_knowledge = {}

    @staticmethod
    def generate_md5_hash(input_data):
        """
        根据文本内容或文件路径生成唯一的 MD5 哈希字符串。

        参数:
        - input_data (str or Path): 输入的文本或文件路径。

        返回:
        - str: 生成的 MD5 哈希值（十六进制字符串）。
        """
        hasher = hashlib.md5()

        if isinstance(input_data, (str, Path)):
            # 如果输入是文件路径，则直接对路径字符串进行哈希
            path_str = str(input_data)
            hasher.update(path_str.encode('utf-8'))
        else:
            # 如果输入是文本，则直接计算文本的哈希
            if isinstance(input_data, str):
                input_data = input_data.encode('utf-8')
            hasher.update(input_data)

        return hasher.hexdigest()

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
            task_id_components = [chat_type, message_type]
            logger.info([event, event_id, chat_type, message_type])
            if not chat_type:
                logger.error("Chat type is not mentioned.")
                continue
            if chat_type == 'p2p':
                sender_id = event.get('sender', {}).get('sender_id', {}).get('open_id')
                receive_id = sender_id
                receive_type = 'open_id'
            elif chat_type == 'group':
                receive_id = message.get('chat_id')
                receive_type = 'chat_id'
                mentions = message.get('mentions', [])
                if message_type == 'text' and '1303f8a4a54f575f' not in [i.get('tenant_key', '') for i in mentions]:
                    logger.error(f"Not mention current bot. Skipped.{[i.get('name', 'Unknown') for i in mentions]}")
                    continue
            elif chat_type == 'post':
                receive_id = event.get('sender', {}).get('sender_id', {}).get('open_id')
                receive_type = 'open_id'
                logger.error(f'{receive_id} {receive_type}')

            else:
                logger.error(f"Unknown chat_type: {chat_type}")
                continue

            if message_type == 'text':
                content_str = message.get('content')
                content = json.loads(content_str) if content_str else {}
                content = content.get('text')
                with open(target_folder / 'input_text.txt', 'w', encoding='utf-8') as f:
                    f.write(content)
                content_hash = self.generate_md5_hash(content)
                task_id_components.append(content_hash)
                res = self.unit_flow(document_path=None, content=content, receive_id=receive_id,
                                     receive_type=receive_type, task_id='_'.join(task_id_components))
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
                #                                                      template_id=self.templates['rich_text_general_id'],
                #                                                      template_variable={'log_rich_text': rich_text_log},
                #                                                      receive_id_type=receive_type)
                file_path_hash = self.generate_md5_hash(file_path)
                task_id_components.append(file_path_hash)
                res = self.unit_flow(document_path=str(file_path), content=None, receive_id=receive_id,
                                     receive_type=receive_type, task_id='_'.join(task_id_components))
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
                # current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # rich_text_log = (
                #     f'<b>【上传文件接收成功】</b>\n'
                #     f'<b><font color="green"><b>{file_path.name}接收成功</b></font>\n'
                #     f'<b>【时间】</b>: {current_time}'
                # )
                # self.feishu_message_handler.send_message_by_template(receive_id=receive_id,
                #                                                      template_id=self.templates['rich_text_general_id'],
                #                                                      template_variable={'log_rich_text': rich_text_log},
                #                                                      receive_id_type=receive_type)
                file_path_hash = self.generate_md5_hash(file_path)
                task_id_components.append(file_path_hash)
                res = self.unit_flow(document_path=str(file_path), content=None, receive_id=receive_id,
                                     receive_type=receive_type, task_id='_'.join(task_id_components))
                if res:
                    msgs.append(res)
            elif message_type == 'post':
                content_str = message.get('content')
                content = json.loads(content_str) if content_str else {}
                content_parts = content.get('content')
                message_id = message.get('message_id')
                content = []
                contain_img = False
                for part in content_parts:
                    img_keys = [i.get('image_key', None) for i in part if i.get('tag') == 'img']
                    if img_keys:
                        contain_img = True
                        file_path = self.feishu_message_handler.retrieve_file(message_id, img_keys[0], target_folder,
                                                                              file_type='image')
                        logger.info(f"Document {file_path.name} received.")
                        file_path_hash = self.generate_md5_hash(file_path)
                        _task_id_components = task_id_components + [file_path_hash]
                        res = self.unit_flow(document_path=str(file_path), content=None, receive_id=receive_id,
                                             receive_type=receive_type, task_id='_'.join(_task_id_components))
                        if res:
                            msgs.append(res)
                    else:
                        content.append(' '.join([i.get('text', '') for i in part]))
                if contain_img:
                    continue
                content = '\n'.join(content)
                with open(target_folder / 'input_text.txt', 'w', encoding='utf-8') as f:
                    f.write(content)
                content_hash = self.generate_md5_hash(content)
                task_id_components.append(content_hash)
                res = self.unit_flow(document_path=None, content=content, receive_id=receive_id,
                                     receive_type=receive_type, task_id='_'.join(task_id_components))
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
        # contents_list = [json.dumps(i.__dict__, ensure_ascii=False, indent=2) for i in data]
        # content_str = '\n'.join(contents_list)
        contents_list = [i.page_content for i in data]
        content_str = '\n'.join(contents_list)
        extra_knowledge_list = []
        if self.extra_knowledge.get('Step_邮件分类'):
            extra_knowledge_list.append(self.extra_knowledge.get('Step_邮件分类'))
        if self.extra_knowledge.get('General_专业名词'):
            extra_knowledge_list.append(self.extra_knowledge.get('General_专业名词'))

        extra_knowledge = '\n'.join(extra_knowledge_list) if extra_knowledge_list else None
        document_type, reason, entry_count = self.message_classifier.classify(content_str,
                                                                              extra_knowledge=extra_knowledge)

        return document_type, reason, entry_count

    def extract_key_information(self, document_loader, document_type, entry_count: int, extra_info: str):
        logger.info(f"->     Starts to extract key information from {document_type}.")
        extra_knowledge_list = []
        if document_type == 'others':
            logger.warning("Message type is OTHER. DO NOT PARSE. SKIPPED.")
            return None
        elif document_type == 'ship_info':
            config_path = self.rule_config_path / 'ship_related_default.yaml'
            if self.extra_knowledge.get('Step_船盘提取'):
                extra_knowledge_list.append(self.extra_knowledge.get('Step_船盘提取'))
            if self.extra_knowledge.get('General_专业名词'):
                extra_knowledge_list.append(self.extra_knowledge.get('General_专业名词'))
        elif document_type == 'cargo_info':
            config_path = self.rule_config_path / 'cargo_offer_default.yaml'
            if self.extra_knowledge.get('Step_货盘提取'):
                extra_knowledge_list.append(self.extra_knowledge.get('Step_货盘提取'))
            if self.extra_knowledge.get('General_专业名词'):
                extra_knowledge_list.append(self.extra_knowledge.get('General_专业名词'))
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

        extra_knowledge = '\n'.join(extra_knowledge_list) if extra_knowledge_list else None
        for vessel_info_chunk in tqdm.tqdm(vessel_info_chunks):
            text_lines = [
                "参考原文：" + content_str,
                '本次提取任务从原文中以下部分提取一个: \n' + vessel_info_chunk
            ] if entry_count > 1 else [content_str]
            modified_outputs = self.kie_instance(rule_config_path=str(config_path),
                                                 file_type=document_type,
                                                 # text_lines=[mutual_info, vessel_info_chunk]
                                                 text_lines=text_lines,
                                                 extra_knowledge=extra_knowledge
                                                 )
            outs.append([modified_outputs[0], vessel_info_chunk, mutual_info])
        logger.success(json.dumps(outs, indent=2, ensure_ascii=False))
        return outs

    @retry(stop_max_attempt_number=2, wait_fixed=2000)
    def validate_key_information(self, document_type, extraction_res):
        logger.info("Starts to Validate results.")
        extra_knowledge_list = []
        if document_type == 'others':
            logger.warning("Message type is OTHER. DO NOT PARSE. SKIPPED.")
            return None
        elif document_type == 'ship_info':
            if self.extra_knowledge.get('Step_船盘校验'):
                extra_knowledge_list.append(self.extra_knowledge.get('Step_船盘校验'))
            if self.extra_knowledge.get('General_专业名词'):
                extra_knowledge_list.append(self.extra_knowledge.get('General_专业名词'))
        elif document_type == 'cargo_info':
            if self.extra_knowledge.get('Step_货盘校验'):
                extra_knowledge_list.append(self.extra_knowledge.get('Step_货盘校验'))
            if self.extra_knowledge.get('General_专业名词'):
                extra_knowledge_list.append(self.extra_knowledge.get('General_专业名词'))
        modified_res = self.ki_validator.bulk_validate(document_type=document_type,
                                                       extraction_res=extraction_res,
                                                       extra_knowledge='\n'.join(extra_knowledge_list))
        modified_res = self.ki_validator.validate(document_type=document_type,
                                                  extraction_res=modified_res)
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

    def add_job(self, job_id, msg_body, source, force_new=False):
        logger.info(f"Adding job: {job_id}")
        n_records = {
            'id': job_id,
            '消息主体': msg_body,
            '数据源': source,
            '状态': '未运行',
        }
        if not force_new:
            records, _ = self.feishu_spreadsheet_handler.get_records(self.app_token, self.tables['inputs_status'],
                                                                     view_id=self.views['inputs_status'],
                                                                     show_fields=['状态'], id=job_id)
            if not records:
                logger.info("Initializing new records.")
                self.feishu_spreadsheet_handler.add_records(self.app_token, self.tables['inputs_status'], [n_records])
                logger.success(f"Added {job_id}")
                return
            else:
                logger.warning(f"Job exists. {records}")
                return records[0]
        else:
            # NEW RECORDS
            logger.info("Initializing new records.")
            self.feishu_spreadsheet_handler.add_records(self.app_token, self.tables['inputs_status'], [n_records])
            logger.success(f"Added {job_id}")
            return

    def update_jobs(self, job_id, msg_body, source, status, records_ids=None, logs=None, force_new=False):
        n_records = {
            'id': job_id,
            '消息主体': msg_body,
            '数据源': source,
            '状态': status,
            'logs': logs if logs else ""
        }
        if records_ids:
            n_records['消息记录'] = '<hr>'.join(records_ids)
        if not force_new:
            records, _ = self.feishu_spreadsheet_handler.get_records(self.app_token, self.tables['inputs_status'],
                                                                     view_id=self.views['inputs_status'], id=job_id)
            if not records:
                logger.info("Initializing new records.")
                self.feishu_spreadsheet_handler.add_records(self.app_token, self.tables['inputs_status'], n_records)
            else:
                record_ids = [i['record_id'] for i in records]
                for record_id in record_ids:
                    self.feishu_spreadsheet_handler.update_records(self.app_token,
                                                                   self.tables['inputs_status'],
                                                                   record_id,
                                                                   n_records)

        else:
            # NEW RECORDS
            logger.info("Initializing new records.")
            self.feishu_spreadsheet_handler.add_records(self.app_token, self.tables['inputs_status'], n_records)

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
                                   raw_text=None, source_name="PureText"):
        if document_type == 'ship_info':
            data_to_insert = []
            for data in extraction_res:
                cur_res = data[0]
                logger.warning(f"Starts to insert: {cur_res}")
                vessel_name = cur_res.get('船舶英文名称-ENGLISH-NAME', '')
                try:
                    vid = self.shipment_dedup.main(vessel_name)
                except:
                    vid = None
                if not vid:
                    cur_res['船舶代码-ID'] = vessel_name
                    logger.error(traceback.format_exc())
                    cur_res['备注-REMARK'] = '\n==='.join([data[1] if data[1] else '', data[2] if data[2] else ''])

                else:
                    vessel_code = self.bx_handler.get_vessel(vid).get('job_info', {}).get('VesselCode')
                    logger.success(f"{vessel_code} already exists")
                    cur_res['船舶代码-ID'] = vessel_code
                    cur_res['备注-REMARK'] = f'无需新建船舶，{vessel_code}已存在。'
                if raw_text:
                    cur_res['原文依据'] = raw_text

                # if raw_text:
                #     cur_res['原文依据'] = raw_text
                if event_id:
                    cur_res['source_name'] = event_id
                else:
                    cur_res['source_name'] = document_path.name if document_path else source_name
                for k in cur_res:
                    cur_res[k] = str(cur_res[k])
                data_to_insert.append(cur_res)
            records_ids = self.feishu_spreadsheet_handler.add_records(app_token=self.app_token,
                                                                      table_id=self.tables['ship_info'],
                                                                      records=data_to_insert)
        elif document_type == 'cargo_info':
            data_to_insert = []
            for data in extraction_res:
                cur_res = data[0]
                if raw_text:
                    cur_res['原文依据'] = raw_text
                cur_res['备注-REMARK'] = '\n==='.join([data[1] if data[1] else '', data[2] if data[2] else ''])
                # if raw_text:
                #     cur_res['原文依据'] = raw_text
                if event_id:
                    cur_res['source_name'] = event_id
                else:
                    cur_res['source_name'] = document_path.name if document_path else 'PureText'
                for k in cur_res:
                    cur_res[k] = str(cur_res[k])
                data_to_insert.append(cur_res)
            records_ids = self.feishu_spreadsheet_handler.add_records(app_token=self.app_token,
                                                                      table_id=self.tables['cargo_info'],
                                                                      records=data_to_insert)
        else:
            return

        logger.success(f"Inserted for {document_path}. Records_ids: {records_ids}")
        return records_ids

    def insert_data_to_bx(self, document_path: Union[Path, None], document_type, extraction_res, event_id=None,
                          raw_text=None):
        # logger.info(f"Inserting {data_to_insert}")

        if document_type == 'ship_info':
            for data in extraction_res:
                cur_res = data[0]
                data = cur_res
                vessel_name = data.get('船舶英文名称-ENGLISH-NAME')
                try:
                    vid = self.shipment_dedup.main(vessel_name)
                except:
                    vid = None
                if not vid:
                    # NEW
                    try:
                        payload = {
                            "VesselCode": vessel_name,
                            "VesselName": vessel_name,
                            "VesselNamec": data.get('船舶中文名称-CHINESE-NAME'),
                            "IMOCode": data.get('IMO-CODE'),
                            "VslType": data.get('船舶类型-TYPE'),
                            "VslCreateYear": data.get('建造年份-BUILT-YEAR'),
                            "CarryTonSJ": data.get('载货吨-DWCC', 0),
                            "CarryTon": data.get('载重吨-DWT', 0),
                            "Tons": data.get('总吨位-GRT', 0),
                            "NetTon": data.get('净吨位-NRT', 0),
                            "HoldCapacity2": data.get('散装舱容-GRAIN-CAPACITY', 0),
                            "GoodsVolumeSZ": data.get('包装舱容-BALE-CAPACITY', 0),
                            # "DSKX": data.get('夏季海水吃水-DRAFT', 0),
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
                            "Remark": data.get('备注-REMARK')
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
                        return {"status": 'error', "log": str(traceback.format_exc())}

                else:
                    vessel_code = self.bx_handler.get_vessel(vid).get('job_info', {}).get('VesselCode')
                    logger.success(f"{vessel_code} already exists")
                    payload = {'VesselCode': vessel_code,
                               'PortNameE': data.get('空船港口-OPEN-PORT'),
                               'DTDate': data.get('空船日期-OPEN-DATE')}
                    res = self.bx_handler.add_vessel_voy_dt(payload)
                    logger.success(f"voy_dt ADD to BX: {res}")
                    return res
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
                               'WeightHT4': data.get('最大货量-QUANTITY', 0),
                               'BeginDate': data.get('装运开始日期-LAY-DATE',
                                                     datetime.datetime.now().strftime('%Y-%m-%d')),
                               'EndDate': data.get('装运结束日期-CANCELING-DATE',
                                                   (datetime.datetime.now() + datetime.timedelta(days=5)).strftime(
                                                       '%Y-%m-%d')),
                               'YJBL': data.get('佣金-COMM'),
                               'BPCompany': data.get('报盘公司-COMPANY'),
                               'CarrierPrice': data.get('运费单价-FRT-RATE', 0),
                               'Remark_DZ': data.get('备注-REMARK')}
                    for keyname in ['YJBL', 'WeightHT2', 'WeightHT4', 'CarrierPrice']:
                        try:
                            payload[keyname] = float(payload[keyname])
                        except:
                            payload[keyname] = payload[keyname]

                    res = self.bx_handler.add_sa_job(payload=payload)
                    logger.success(f"sa_job ADD to BX: {res}")
                    return res

                except:
                    logger.error(traceback.format_exc())
                    return {"status": 'error', "log": str(traceback.format_exc())}
        else:
            return

        logger.success(f"Inserted for {document_path}")

    def debug_data_insert(self, data):
        self.insert_data_to_spreadsheet(Path('demo'), 'cargo_offer', data)

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
                  task_id=None, debug=False, skip_success=True, document_type=None):
        logger.info(f"Current receive_type: {receive_type} receive_id: {receive_id}")
        logger.error(f'{receive_id} {receive_type}')
        document_loader = self.load_document(document_path=Path(document_path) if document_path else None,
                                             content=content)
        data = document_loader.load()
        contents_list = [i.page_content for i in data]
        content_str = '\n'.join(contents_list)
        job_id = task_id if task_id else f"{receive_type}_{receive_id}"
        existing_job = self.add_job(job_id=job_id, msg_body=content_str, source=receive_type)
        if existing_job:
            if skip_success and existing_job['fields']['状态'] == '成功':
                logger.error(f"Job exists and success. Skipped")
                return
        # Classify
        if document_type:
            logger.info(f"Skip classification. Document type: {document_type}")
            document_type, reason, entry_count = document_type, '', 1
        else:
            try:
                self.update_jobs(job_id=job_id,
                                 msg_body=content_str,
                                 source=receive_type,
                                 status='分类中',
                                 logs=f"开始邮件分类")
                document_type, reason, entry_count = self.classify_document(document_loader)
                logger.success(
                    f"=>     Classify {document_path if document_path else 'text'}: TYPE:{document_type}, ENTRY_COUNT: {entry_count} REASON:{reason}")
                self.update_jobs(job_id=job_id,
                                 msg_body=content_str,
                                 source=receive_type,
                                 status='分类中',
                                 logs=f"=>     Classify {document_path if document_path else 'text'}: TYPE:{document_type}, ENTRY_COUNT: {entry_count} REASON:{reason}")

            except Exception as e:
                document_type = None
                logger.error(traceback.format_exc())
                self.update_jobs(job_id=job_id,
                                 msg_body=content_str,
                                 source=receive_type,
                                 status='异常',
                                 logs=traceback.format_exc())
                return
        # Extraction
        if document_type == 'others':
            self.update_jobs(job_id=job_id,
                             msg_body=content_str,
                             source=receive_type,
                             status='成功',
                             logs=f"不属于船盘/货盘邮件")
            return
        self.update_jobs(job_id=job_id,
                         msg_body=content_str,
                         source=receive_type,
                         status='提取中',
                         logs=f"开始邮件信息提取")
        extraction_res = self.extract_key_information(document_loader=document_loader,
                                                      document_type=document_type,
                                                      entry_count=entry_count,
                                                      extra_info=reason)
        if not extraction_res:
            self.update_jobs(job_id=job_id,
                             msg_body=content_str,
                             source=receive_type,
                             status='分类中',
                             logs=f"未曾成功提取出结果。{extraction_res}")
            return
        extraction_res = [] if not extraction_res else extraction_res
        self.update_jobs(job_id=job_id,
                         msg_body=content_str,
                         source=receive_type,
                         status='分类中',
                         logs=f"=>     初次提取成功：{extraction_res}")
        # Validation
        self.update_jobs(job_id=job_id,
                         msg_body=content_str,
                         source=receive_type,
                         status='结果校验中',
                         logs=f"开始校验结果")
        extraction_res = self.validate_key_information(document_type, extraction_res)
        self.update_jobs(job_id=job_id,
                         msg_body=content_str,
                         source=receive_type,
                         status='结果校验中',
                         logs=f"=>     结果校验成功：{extraction_res}")

        # INSERTION
        if not debug:
            try:
                self.update_jobs(job_id=job_id,
                                 msg_body=content_str,
                                 source=receive_type,
                                 status='插入数据',
                                 logs=f"开始插入数据")
                total, content = self.get_data_loader_context(document_loader)
                records_ids = self.insert_data_to_spreadsheet(Path(document_path) if document_path else None,
                                                              document_type,
                                                              extraction_res,
                                                              raw_text='\n'.join(content))
                self.update_jobs(job_id=job_id,
                                 msg_body=content_str,
                                 source=receive_type,
                                 records_ids = records_ids,
                                 status='插入数据',
                                 logs=f"数据成功插入飞书表")

                logger.success(f"=>      Data Inserted.")
            except Exception as e:
                logger.error(traceback.format_exc())
                self.update_jobs(job_id=job_id,
                                 msg_body=content_str,
                                 source=receive_type,
                                 status='插入数据',
                                 logs=f"飞书表插入失败，失败报错：{traceback.format_exc()}")

                return
        else:
            logger.success(json.dumps(extraction_res, indent=4, ensure_ascii=False))
        self.update_jobs(job_id=job_id,
                         msg_body=content_str,
                         source=receive_type,
                         status='成功',
                         logs=json.dumps(extraction_res, indent=2, ensure_ascii=False))
        return extraction_res, records_ids

    def main(self, document_paths=None):
        if not document_paths:
            document_paths = self.collect_emails()
        for document_path in tqdm.tqdm(document_paths):
            res = self.unit_flow(document_path)
            if res is False:
                logger.error("Job exists.")
                continue


if __name__ == "__main__":
    ins = ShipmentFlow(r'W:\Personal_Project\NeiRelated\projects\shipment_solution\configs\feishu_config.yaml')
    ins.unit_flow(
        r'W:\Personal_Project\NeiRelated\projects\shipment_solution\src\emails\货盘数据\tct order(1).eml')
