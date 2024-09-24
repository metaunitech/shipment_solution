import datetime
import json
import os
import traceback
from pathlib import Path
from langchain_openai import ChatOpenAI

import tqdm
from langchain_community.document_loaders import UnstructuredEmailLoader, OutlookMessageLoader
from langchain_core.document_loaders import BaseLoader
from modules.utils.ocr_handler import OCRHandler
from modules.message_classification import MessageClassifier
from modules.message_segmentation import MessageSegmenter
from modules.key_information_extraction import TextKIE
from modules.Feishu.Feishu_spreadsheet import FeishuSpreadsheetHandler
from modules.Feishu.Feishu_messages import FeishuMessageHandler
from glob import glob
from loguru import logger

from langchain_core.documents import Document
from typing import Union

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
        self.feishu_spreadsheet_handler = FeishuSpreadsheetHandler(feishu_config_path)
        self.feishu_message_handler = FeishuMessageHandler(feishu_config_path)

    def process_msg_dicts(self, msg_dicts):
        msgs = []
        for msg_dict in msg_dicts:
            event = msg_dict.get('event', {})
            event_id = msg_dict.get('header', {}).get('event_id')
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
                receive_type = 'open_id'
            elif chat_type == 'group':
                receive_id = message.get('chat_id')
                receive_type = 'chat_id'
                mentions = message.get('mentions', [])
                if message_type == 'text' and '16c5228b4a88575e' not in [i.get('tenant_key', '') for i in mentions]:
                    logger.error(f"Not mention current bot. Skipped.{[i.get('name', 'Unknown') for i in mentions]}")
                    continue
            else:
                logger.error(f"Unknown chat_type: {chat_type}")
                continue
            if message_type == 'text':
                content_str = message.get('content')
                content = json.loads(content_str) if content_str else {}
                content = content.get('text')
                res = self.unit_flow(document_path=None, content=content, receive_id=receive_id,
                                     receive_type=receive_type)
                if res:
                    msgs.append(res)
            elif message_type == 'file':
                message_id = message.get('message_id')
                content_str = message.get('content')
                content = json.loads(content_str) if content_str else {}
                file_key = content.get('file_key')
                current_date = datetime.datetime.now().strftime("%Y-%m-%d")
                target_folder = Path(__file__).parent.parent / 'src' / 'input' / current_date / event_id
                os.makedirs(target_folder, exist_ok=True)
                file_path = self.feishu_message_handler.retrieve_file(message_id, file_key, target_folder)
                logger.info(f"Document {file_path.name} received.")
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                rich_text_log = (
                    f'<b>【上传文件接收成功】</b>\n'
                    f'<b><font color="green"><b>{file_path.name}接收成功</b></font>\n'
                    f'<b>【时间】</b>: {current_time}'
                )
                self.feishu_message_handler.send_message_by_template(receive_id=receive_id,
                                                                     template_id='AAq7OhvOhSJB2',  # Hardcoded.
                                                                     template_variable={'log_rich_text': rich_text_log},
                                                                     receive_id_type=receive_type)
                res = self.unit_flow(document_path=str(file_path), content=None, receive_id=receive_id,
                                     receive_type=receive_type)
                if res:
                    msgs.append(res)
            elif message_type == 'image':
                message_id = message.get('message_id')
                content_str = message.get('content')
                content = json.loads(content_str) if content_str else {}
                file_key = content.get('image_key')
                current_date = datetime.datetime.now().strftime("%Y-%m-%d")
                target_folder = Path(__file__).parent.parent / 'src' / 'input' / current_date / event_id
                os.makedirs(target_folder, exist_ok=True)
                file_path = self.feishu_message_handler.retrieve_file(message_id, file_key, target_folder, file_type='image')
                logger.info(f"Document {file_path.name} received.")
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                rich_text_log = (
                    f'<b>【上传文件接收成功】</b>\n'
                    f'<b><font color="green"><b>{file_path.name}接收成功</b></font>\n'
                    f'<b>【时间】</b>: {current_time}'
                )
                self.feishu_message_handler.send_message_by_template(receive_id=receive_id,
                                                                     template_id='AAq7OhvOhSJB2',  # Hardcoded.
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

    def create_llm_instance(self, model_name=MODEL_NAME):
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

    def classify_document(self, document_loader):
        data = document_loader.load()
        contents_list = [json.dumps(i.__dict__, ensure_ascii=False, indent=2) for i in data]
        content_str = '\n'.join(contents_list)
        document_type, reason = self.message_classifier.classify(content_str)

        return document_type, reason

    def extract_key_information(self, document_loader, document_type):
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
        data = document_loader.load()
        contents_list = [json.dumps(i.__dict__, ensure_ascii=False, indent=2) for i in data]
        content_str = '\n'.join(contents_list)
        try:
            vessel_info_chunks, mutual_info, comment = self.message_segmenter.segment(content_str, document_type)
        except Exception as e:
            logger.error(f"[Segmentation]    Failed to segment message, will treat as single paragraph. Note: {str(e)}")
            vessel_info_chunks = [content_str]
            mutual_info = ''
            # comment = f"[Segmentation]    Failed to segment message, will treat as single paragraph. Note: {str(e)}"
        # Do extraction:
        ## By serial
        outs = []
        for vessel_info_chunk in tqdm.tqdm(vessel_info_chunks):
            modified_outputs = self.kie_instance(rule_config_path=str(config_path),
                                                 file_type=document_type,
                                                 text_lines=[vessel_info_chunk, mutual_info])
            outs.append([modified_outputs[0], vessel_info_chunk, mutual_info])
        logger.success(json.dumps(outs, indent=2, ensure_ascii=False))
        return outs

    def debug_batch(self, document_paths=None, steps=None):
        if not document_paths:
            document_paths = self.collect_emails()
        for document_path in tqdm.tqdm(document_paths):
            document_loader = self.load_document(Path(document_path))
            document_type, reason = self.classify_document(document_loader)
            logger.success(f"=>     Classify {document_path}: TYPE:{document_type}, REASON:{reason}")
            if '船舶数据' in document_path and document_type == 'ship_info':
                logger.success("CORRECT")
            elif '货盘数据' in document_path and document_type == 'cargo_info':
                logger.success('CORRECT')
            else:
                logger.error(f"FALSE: {document_path}: TYPE:{document_type}, REASON:{reason}")
            if steps and 2 not in steps:
                continue

    def mark_finish(self):
        pass

    def insert_data_to_spreadsheet(self, document_path: Union[Path, None], document_type, extraction_res):
        data_to_insert = []
        for data in extraction_res:
            cur_res = data[0]
            cur_res['原文依据'] = '\n'.join([data[1] if data[1] else '', data[2] if data[2] else ''])
            cur_res['source_name'] = document_path.name if document_path else 'PureText'
            data_to_insert.append(cur_res)
        logger.info(f"Inserting {data_to_insert}")
        if document_type == 'ship_info':
            table_id = 'tbly9gtTypeOLQ8Q'
        elif document_type == 'cargo_info':
            table_id = 'tblSsCLLIEXguHpk'
        else:
            return
        self.feishu_spreadsheet_handler.add_records(app_token='B7XnbQTtLapDfDsJj27c7ZgQnLd',
                                                    table_id=table_id,
                                                    records=data_to_insert)
        logger.success(f"Inserted for {document_path}")

    def debug_data_insert(self, data):
        self.insert_data_to_spreadsheet(Path('demo'), 'ship_info', data)

    @staticmethod
    def json_to_code_block(json_data):
        formatted_json = json.dumps(json_data, indent=2)
        return f'```json\n{formatted_json}\n```'

    def unit_flow(self, document_path: Union[str, None] = None, content=None, receive_id=None, receive_type=None):
        document_loader = self.load_document(document_path=Path(document_path) if document_path else None,
                                             content=content)
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if receive_type and receive_id:
            rich_text_log = (
                f'<b>【邮件主体收到】</b>\n'
                f'<i>{document_path if document_path else content[:50] + "..."}</i>\n'
                f'<b>正在进行步骤：<font color="blue"><b>邮件分类</b></font></b>\n'
                f'<b>【时间】</b>: {current_time}'
            )
            self.feishu_message_handler.send_message_by_template(receive_id=receive_id,
                                                                 template_id='AAq7OhvOhSJB2',  # Hardcoded.
                                                                 template_variable={'log_rich_text': rich_text_log},
                                                                 receive_id_type=receive_type)
        # Classify
        try:
            document_type, reason = self.classify_document(document_loader)
            logger.success(
                f"=>     Classify {document_path if document_path else content[:50] + '...'}: TYPE:{document_type}, REASON:{reason}")
            if receive_type and receive_id:
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                rich_text_log = (
                    f'<b>【邮件主体分类成功】</b>\n'
                    f'<i>{document_path if document_path else content[:50] + "..."}</i>\n'
                    f'<b>邮件分类：<font color="green"><b>{document_type}</b></font>\n'
                    f'<b>分类原因：<font color="grey"><b>{reason}</b></font>\n'
                    f'<b>正在进行步骤：<font color="blue"><b>关键信息提取</b></font></b>\n'
                    f'<b>【时间】</b>: {current_time}'
                )
                self.feishu_message_handler.send_message_by_template(receive_id=receive_id,
                                                                     template_id='AAq7OhvOhSJB2',  # Hardcoded.
                                                                     template_variable={'log_rich_text': rich_text_log},
                                                                     receive_id_type=receive_type)
        except Exception as e:
            logger.error(traceback.format_exc())
            if receive_type and receive_id:
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                rich_text_log = (
                    f'<b>【邮件主体分类失败】</b>\n'
                    f'<i>{document_path if document_path else content[:50] + "..."}</i>\n'
                    f'<b>失败原因：<font color="red"><b>{str(e)}</b></font></b>\n'
                    f'<b>【时间】</b>: {current_time}'
                )
                self.feishu_message_handler.send_message_by_template(receive_id=receive_id,
                                                                     template_id='AAq7OhvOhSJB2',  # Hardcoded.
                                                                     template_variable={'log_rich_text': rich_text_log},
                                                                     receive_id_type=receive_type)
            return

        extraction_res = self.extract_key_information(document_loader=document_loader,
                                                      document_type=document_type)
        if not extraction_res:
            return
        extraction_res = [] if not extraction_res else extraction_res
        logger.success(f"=>      KIE Extraction results: {json.dumps(extraction_res, ensure_ascii=False, indent=2)}")
        if receive_type and receive_id:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            rich_text_log = (
                f'<b>【邮件关键信息提取成功】</b>\n'
                f'{self.json_to_code_block([i[0] for i in extraction_res])}\n'
                f'<b>正在进行步骤：<font color="blue"><b>插入多维表</b></font>\n'
                f'<b>【时间】</b>: {current_time}'
            )
            self.feishu_message_handler.send_message_by_template(receive_id=receive_id,
                                                                 template_id='AAq7OhvOhSJB2',  # Hardcoded.
                                                                 template_variable={'log_rich_text': rich_text_log},
                                                                 receive_id_type=receive_type)
        try:
            self.insert_data_to_spreadsheet(Path(document_path) if document_path else None, document_type, extraction_res)
            logger.success(f"=>      Data Inserted.")
            if receive_type and receive_id:
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                rich_text_log = (
                    f'<b>【关键信息插入多维表成功】</b>\n'
                    f'<b><font color="green"><b>关键信息插入成功</b></font>\n'
                    f'<b>【时间】</b>: {current_time}'
                )
                self.feishu_message_handler.send_message_by_template(receive_id=receive_id,
                                                                     template_id='AAq7OhvOhSJB2',  # Hardcoded.
                                                                     template_variable={'log_rich_text': rich_text_log},
                                                                     receive_id_type=receive_type)
        except Exception as e:
            logger.error(traceback.format_exc())
            if receive_type and receive_id:
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                rich_text_log = (
                    f'<b>【分类数据插入失败】</b>\n'
                    f'<i>{document_path if document_path else content[:50] + "..."}</i>\n'
                    f'<b>失败原因：<font color="red"><b>{str(e)}</b></font>\n'
                    f'<b>【时间】</b>: {current_time}'
                )
                self.feishu_message_handler.send_message_by_template(receive_id=receive_id,
                                                                     template_id='AAq7OhvOhSJB2',  # Hardcoded.
                                                                     template_variable={'log_rich_text': rich_text_log},
                                                                     receive_id_type=receive_type)
            return
        self.mark_finish()
        return extraction_res

    def main(self, document_paths=None):
        if not document_paths:
            document_paths = self.collect_emails()
        for document_path in tqdm.tqdm(document_paths):
            self.unit_flow(document_path)


if __name__ == "__main__":
    ins = ShipmentFlow()
    # ins.unit_flow(
    #     r'W:\Personal_Project\NeiRelated\projects\shipment_solution\src\emails\船舶数据\HAITIN TRACO - OPEN TONNAGE 06 SEP 2024.eml')
    # data = [
    #     [
    #         {
    #             "船舶代码-ID": "9371139",
    #             "船舶类型-TYPE": "MULTI-PURPOSE VESSEL/ SINGLE DECK",
    #             "船舶英文名称-ENGLISH-NAME": "GREEN PACIFIC",
    #             "建造年份-BUILT-YEAR": "2005",
    #             "载重吨-DWT": "4200.00 MT",
    #             "总吨位-GRT": "2581",
    #             "净吨位-NRT": "1445",
    #             "船长-LOA": "79.95 M",
    #             "船宽-BM": "13.80",
    #             "型深-DEPTH": "11.6 M",
    #             "船级-CLASS": "NR",
    #             "舱口数量-HATCH": "2HA",
    #             "舱位数量-HOLD": "2HO/2HA",
    #             "吊机-GEAR": "2 X 15 MT",
    #             "夏季海水吃水-DRAFT": "7.45M",
    #             "甲板数-DECK": "SINGLE DECK",
    #             "P&I": "P&I CLUB : MARITIME MUTUAL NZ",
    #             "船舶名称-VSL-NAME": "MV. GREEN PACIFIC",
    #             "空船港口-OPEN-PORT": "BACOLOD, PHILIPPINES",
    #             "空船日期-OPEN-DATE": "MID OCTOBER 2024"
    #         },
    #         "{\n  \"id\": null,\n  \"metadata\": {\n    \"source\": \"W:\\\\Personal_Project\\\\NeiRelated\\\\projects\\\\shipment_solution\\\\src\\\\emails\\\\船舶数据\\\\HAITIN TRACO - OPEN TONNAGE 06 SEP 2024.eml\"\n  },\n  \"page_content\": \"DEAR SIRS/MADAMS,\\n\\nGD DAY!\\n\\n \\n\\nPLS ARRANGE SUITABLE CGO FOR THE FLW TONNAGE:          \\n\\n \\n\\nMV. GREEN PACIFIC - DWT: 4200.00 MT  – BACOLOD,  PHILIPPINES  / MID OCTOBER 2024\\n\\nMV.  LUCKY STAR 6  - DWT: 7,869.21 MT – NORTH PHILIPPINES  / MID SEPTEMBER 2024\\n\\nMV. GREEN STAR      - DWT: 3,142.1 MT   – BUTUAN PHILIPPINES / EARLY OCTOBER 2024\\n\\nMV. GREEN SKY        - DWT: 5,170.0 MT   – SORONG, INDONESIA / 10TH- 15TH SEPTEMBER2024\\n\\n1/ MV. GREEN PACIFIC – BACOLOD,  PHILIPPINES  / MID OCTOBER 2024\\n\\nTYPE OF SHIP: MULTI-PURPOSE VESSEL/ SINGLE DECK\\n\\nPORT OF REGISTRY: ST. MAARTEN,  CLASS : NR\\n\\nIMO NUMBER: 9371139 / CALL SIGN: 8PJC6 \\n\\nYEAR BUILT: 2005\\n\\nDWT/ GRT/NRT: 4200/2581/1445\\n\\nLENGTH/BM/DRAFT: 79.95/ 13.80/ 7.45M\\n\\nHOLD/HATCH: 2HO/2HA\\n\\nVSL'S GEAR: 01X15 MT\\n\\n2/ MV. LUCKY STAR 6 – NORTH PHILIPPINES, MID SEPTEMBER 2024\\n\\n \\n\\nTYPE OF SHIP: M.BULK CARRIER / TWEEN  DECK\\n\\nGENERAL CGO/BULK VSL YEAR BUILT: 1996\\n\\nCLASSIFICATION: PMDS\\n\\nIMO/CALL SIGN: 9146912/3EPB3\\n\\nPORT OF REGISTRY : PANAMA\\n\\nNEVIGATION : OCEAN GOING\\n\\nHOLDS: 2 / HATCHES: 2, STEEL MACGEGOR HATCH COVERS\\n\\nGRT/NRT/DWT: 4738/2196/ 7869.21 MT\\n\\nLOA/BM/DEPTH: 96.7/ 17,4M/ 11,6 M\\n\\nHOLD/HATCH: 2HO/2HA,(TWEEN DECK/ PONTOOO)\\n\\nHOLD GRAIN / BALE: 10595.63/10102.54 CBM \\n\\nHATCH SIZE (L X B)  No 1 H/C 14.7 X 12.6 // No2  H/C 28.0 X 12,6 MTRS\\n\\nDERRICKS 25 TONES X 3 SETS, P&I CLUB : MARITIME MUTUAL NZ\\n\\n \\n\\n3/ MV. GREEN STAR – BUTUAN PHILIPPINES / EARLY OCTOBER 2024\\n\\n \\n\\nTYPE OF SHIP: M.BULK CARRIER / SINGLE DECK\\n\\nVIETNAM FLAG, GENERAL CGO VSL YEAR BUILT: 2009\\n\\nCLASS: VR (Vietnam Register )\\n\\nHOLDS: 2 / HATCHES: 2, STEEL MACGEGOR HATCH COVERS\\n\\nGRT/NRT/DWT: 1.596/1023/ 3,113.80 MT\\n\\nLOA/BM/DRAFT: 78.630/ 12.624/ 5,220M\\n\\nHOLD/HATCH: 2HO/2HA\\n\\nHOLD GRAIN/BALE: 3709.7/3635.5\\n\\nHold dimensions (L x B x H )  No.1 = 25.80 x 12.60  x 5.03M  No.2 = 25.80 x 12.60  x 5.00 M Hatches size(L x B x H ):No.1 = 19.80 x 8.40 x  1.38 M  No.2 = 19.32 x 8.40 x  1.40 M\\n\\nVSL'S GEAR: 1 X 10 MT, P& I CLB WOE   \\n\\n4/ MV. GREEN SKY -  SORONG, INDONESIA    /  10TH- 15TH SEPTEMBER   2024\\n\\nTYPE OF SHIP: M.BULK CARRIER / SINGLE DECK\\n\\nVIETNAM FLAG, GENERAL CGO VSL YEAR BUILT: 2012\\n\\nDWT/GRT/NRT : 5,170.0/2,999/1,860\\n\\nLOA 91.94, LBP 15.3 DRAFT: 6.3 M\\n\\nHOLD/HATCH: 2HO/2HA\\n\\nHOLD GRAIN / BALE: 6959/6750 CBM  \\n\\nHold dimensions ( L x B X H ) : No.1 = 29.4 x 15.3  x 6.8M ;  No.2 = 28.4 x 15.3 x 6.8 M\\n\\nHatches size (L x B x H ) : No.1 = 21.0 x 10.0 x 1.5 M ;  No.2 = 20.0 x 10.0 x 1.5 M4.\\n\\nVSL'S GEAR: 2 X 15 MT\\n\\n     \\n\\nPls to hear in shortly,\\n\\n--\\n\\nTHANKS & BEST REGARDS,\\n\\n \\n\\nMobile:    Mr. Kevin.Thanh      +84.982148569\\n\\n                 Mr. Kiem                  +84.904642998\\n\\n                 Mr. Sun. Nhat           +84.967032873\\n\\n                 Ms. Helen.Ha           +84.912698858\\n\\n (Zalo/Viber/Whatsapp)\\n\\n--------------------------------------------------------------------------------------------\\n\\nHAI TIN INTERNATIONAL TRANSPORT TRADING COMPANY LIMITED\\n\\nHead office add:  No. 37, Street No. 17, Ward 11, Go Vap District, Ho Chi Minh City, Vietnam\\n\\nBranch office add: 574 Nguyen Cong Hoan Street, Dong Khe Ward, Ngo Quyen  District, Hai Phong, Vietnam\\n\\nEmail : haitintracoship@gmail.com    www.haitintraco.com\",\n  \"type\": \"Document\"\n}",
    #         ""
    #     ]
    # ]
    # ins.debug_data_insert(data)
    ins.main()
