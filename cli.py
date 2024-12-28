# encoding=utf-8
# SHIPMENTFLOW
from main import ShipmentFlow
ins = ShipmentFlow(r'configs/feishu_config.yaml')
# ins.feishu_spreadsheet_handler.batch_get_records(ins.app_token, ins.tables['ship_info'], ['recuy9qvJMDa5O'])
ins.unit_flow(content="""1.                 MV HAI AU 58// DWCC 3900MT – OPEN LHOKSUMAWE, INDO 07-12TH JAN

 

2.                 MV SEAGULL 09//DWCC 4900MT – OPEN BACOLOD, PHILS ON PPT – HOT TO FIX

 

3.                 MV HAI DANG 168/ DWCC 4900 MT  - OPEN BATAAN, PHILS ON 15-20TH JAN

 

4.                 MV HAI AU 28/GEARLESS//DWCC 4950MT –  OPEN MAKASSAR, INDO ON 05-10TH JAN

 

5.                 MV VIEN DONG 151//GEARLESS//DWCC 6300 MT – TO BE DRY DOCKING- REVERTING

 

6.                 MV VIEN DONG 09/DWCC 6100 MT  - OPEN MUARA, BRUNEI ON 08 – 10TH JAN

 

7.                 MV SEAGULL VICTORY// DWCC 11.400 MT – FIXED TC 6 MONTHS- OPEN REVERTING IN MAR 2025

 

8.         MV SEAGULL DIAMOND// DWCC 23.000 MT – OPEN HAI PHONG EARLY OF JAN

++

MV HAI DANG 168

IMO 9663386, BUILT 2012, VIETNAM FLAG, VR CLASS

DWT/GT/NT : 5,098.6  / 2,999/ 1,849

LOA/BEAM/ SUMMER DRAFT: 91.94 / 15.30 / 6.3 M

SINGLE DECK, 2 HOLDS/2 HATCHES , G/B CAPA : 6,579.66/ 5,931CBM

HOLD 1/2:  28.90 X 14,3 X 6.20 / 28.40 X 14,3 X 6.20 M

HATCH COAMING : 20.00 X 10.00 X 2.20 / 21.00 X 10.00 X 2.20 M

TYPE OF HATCH COVER: MAGEGOR

PNI: WOE / 2 CRANES X 5 MT WOG

 

MV HAI AU STAR

IMO 9658226, BUILT 2014, VIETNAM FLAG, VR CLASS

DWT/GT/NT : 5,142.40  / 2,999/ 1,852

LOA/BEAM/ SUMMER DRAFT: 91.94 / 15.30 / 6.3 M

SINGLE DECK, 2 HOLDS/2 HATCHES , G/B CAPA : 6,590/5930 CBM

HOLD 1/2:  28.00 X 14 X 6.9 / 29.00 X 14 X 6.9 M

HATCH COAMING : 21.00 X 10.00 X 1.50 / 20.00 X 10.00 X 1.50 M

TYPE OF HATCH COVER: MAGEGOR

PNI: WOE / 2 DERRICKS X 5 MT

ADWOG

 

MV SEAGULL 09

IMO 9581722, BUILT 2010, VIETNAM FLAG, VR CLASS

DWT/GT/NT : 5,095.40  / 2,999/ 1,848

LOA/BEAM/ SUMMER DRAFT: 91.94 / 15.30 / 6.3 M

SINGLE DECK, 2 HOLDS/2 HATCHES , G/B CAPA : 6,683/6,021 CBM

HOLD 1/2:  28.00 X 14 X 6.2 / 29.00 X 14 X 6.2 M

HATCH COAMING : 21.00 X 10.00 X 2.20 / 20.00 X 10.00 X 2.20 M

TYPE OF HATCH COVER: MAGEGOR

PNI: WOE / 2 DERRICKS X 5 MT

ADWOG

 

MV HAI AU 58

IMO 9564102, BUILT 2011, VIETNAM FLAG, VR CLASS

DWT/GT/NT : 4,095.7  / 2,363/ 1,449

LOA/BEAM/ SUMMER DRAFT: 87.50 / 13.60 / 5.9 M

SINGLE DECK, 2 HOLDS/2 HATCHES , G/B CAPA : 5,165/4,649 CBM

HOLD 1/2:  19.20 X 13 X 5.97 / 35.95 X 13 X 5.97 M

HATCH COAMING : 12.60 X 8.00 X 2.03 / 26.15 X 8.00 X 2.03 M

TYPE OF HATCH COVER: MAGEGOR

PNI: WOE / 2 CRANES X 5 MT WOG

 

MV HAI AU 28

IMO 9608611, BUILT 2012, VIETNAM FLAG, VR CLASS

DWT/GT/NT : 5,235.9  / 2,995/ 1,860

LOA/BEAM/ SUMMER DRAFT: 91.94 / 15.30 / 6.3 M

SINGLE DECK, 2 HOLDS/2 HATCHES , G/B CAPA : 6,590/5930 CBM

HOLD 1/2:  28.00 X 14 X 6.8 / 29.00 X 14 X 6.8 M

HATCH COAMING : 21.00 X 10.00 X 1.50 / 20.00 X 10.00 X 1.50 M

TYPE OF HATCH COVER: MAGEGOR

PNI: WOE / GEARLESS

ADWOG

 

MV HAI AU SKY

IMO 9625695, BUILT 2013, VIETNAM FLAG, VR CLASS

DWT/GT/NT : 5,236.3  / 2,995/ 1,860

LOA/BEAM/ SUMMER DRAFT: 91.94 / 15.30 / 6.3 M

SINGLE DECK, 2 HOLDS/2 HATCHES , G/B CAPA : 6,590/5930 CBM

HOLD 1/2:  28.00 X 14 X 6.8 / 29.00 X 14 X 6.8 M

HATCH COAMING : 21.00 X 10.00 X 1.50 / 20.00 X 10.00 X 1.50 M

TYPE OF HATCH COVER: MAGEGOR

PNI: WOE / GEARLESS

ADWOG

 

MV VIEN DONG 09

IMO 9276212, BUILT 2002, VIETNAM FLAG, VR CLASS

DWT/GT/NT : 6,595.8 / 4,089/ 2,448

LOA/BEAM/ SUMMER DRAFT: 102.79 / 17.00 / 6.9 M

SINGLE DECK, 2 HOLDS/2 HATCHES , G/B.CAPA : 8,610/8,159 CBM

HOLD 1/2:  33.50 X 16 X 6.8 / 34.00 X 16 X 6.8 M

HATCH COAMING : 23.35 X 10.00 X 1.50 / 25.90 X 10.00 X 1.50 M

TYPE OF HATCH COVER: PONTOON

PNI: QBE / 4 DERRICK X 5 MT WOG

 

MV VIEN DONG 151

IMO 9391555, BUILT 2006, VIETNAM FLAG, VR CLASS

DWT/GT/NT : 6,724.64 / 4,033/ 2,391

LOA/BEAM/ SUMMER DRAFT: 102.79 / 17.00 / 7.1 M

SINGLE DECK, 2 HOLDS/2 HATCHES , G/B.CAPA : 8,610/8,159 CBM

HOLD 1/2:  33.40 X 16 X 6.8 / 34.30 X 16 X 6.8 M

HATCH COAMING : 23.35 X 10.90 X 1.70 / 23.80 X 10.90 X 1.70 M

TYPE OF HATCH COVER: MAGEGOR

PNI: QBE / GEARLESS

ADWOG

 

MV SEAGULL VICTORY

PANAMA FLAG, BUILT 2011, KR CLASS

DWT/GT/NT: 12,138 DWT/8576 / 4000 ON 9.20 M DRAFT

LOA 118.35M BEAM 19.40M DEPTH 14.1 M

TWEEN DECK, HOLD/HATCHE 2/2 BOX SHAPED, GRAIN/BALE 17,657/16,350 CBM

HOLD 1: LOWER: 39,1 X 17,3 X 6,5M/ UPPER: 39,1 X 17,3 X 4,6 M

HOLD 2: LOWER: 33,5 X 17,3 X 6,5M/ UPPER: 40,5 X 17,3 X 4,6 M

HATCH COAMING : 26.6 X 14 X 1.70 / 26.80 X 14.30 X 1.70 M

CRANES 2X30T (COMBINABLE) + DERRICK 2X25T

TYPE OF HATCH COVERS: WEATHER DECK: SIGNLE PULLED BY CHAIN;

PNI: WOE

ADWOG

 

MV SEAGULL DIAMOND

VIETNAM FLAG, BUILT 1996, VR CLASS

DWT/GT/NT: 24,034 DWT/14,397/ 8314 ON 9.50 M DRAFT IN SUMMER

LOA 153.50M BEAM 25.80M DEPTH 13.3 M

SINGLE DECK, HOLD/HATCHE 4/4, GRAIN/BALE 31,101/30,101 CBM

HOLD 1: 29,6 X 25,0 X 11,8M/ HATCH COAMING: 20 X 12,8 X 4,6 M/ BALE/GRAIN 6598/6829 CBM

HOLD 2: 28,8 X 25,0 X 11,8M/ HATCH COAMING: 20 X 17,6 X 4,6 M/ BALE/GRAIN 7973/8276 CBM

HOLD 3: 28,8 X 25,0 X 11,8M/ HATCH COAMING: 20 X 17,6 X 4,6 M/ BALE/GRAIN 7979/8279 CBM

HOLD 4: 28,8 X 25,0 X11,8M/ HATCH COAMING: 20 X 17,6 X 4,6 M/ BALE/GRAIN 7551/7717 CBM

TYPE OF HATCH COVERS: STEEL END FOLDING

PNI: WOE/ CRANE 4 X 20MT

ADWOG""",receive_id='test001', source_name='email',debug=True, skip_success=False)
# ins.update_jobs('demo', 'dd', 'dd', status='结果校验中')
#####
# ins.debug_data_insert(data=[{"货物名称-CARGO-NAME": "hot rolled coils", "最大货量-QUANTITY": "2200.0", "装货港口-L-PORT": "SON DUONG, VIETNAM", "卸货港口-L-PORT": "BELAWAN, INDONESIA", "装运开始日期-LAY-DATE": "2024-09-01", "佣金-COMM": "2.5", "运费单价-FRT-RATE": "80000.0", "原文依据": "need named vsl to fix\n\n—freight $ 80k\n—2,200mt hot rolled coils, 10pct molco\n—son duong, vietnam / belawan, indonesa\n—laycan:ppt onwards\n—invite bst fio or filo\n—cqd term\n—com 2.5\n\n\n\n—freight $ 20 pmt\n—5,000mt bulk clay\n—p.kelang / taipei, taiwan\n—dec 15-20 try vsl date\n—invite bst fio\n—com 2.5", "source_name": "PureText"}])
# from modules.key_information_extraction import TextKIE
# from langchain_openai import ChatOpenAI
#
# MODEL_NAME = 'glm-4-flash'
# API_TOKEN = "7d020833a52b08e7251707288af8d20d.JmuseA1s6dTDSyt7"
#
# llm_ins = ChatOpenAI(temperature=0.95,
#                      model=MODEL_NAME,
#                      openai_api_key=API_TOKEN,
#                      openai_api_base="https://open.bigmodel.cn/api/paas/v4/")
#
#
#
#
# input_text = """50/55,000 MT SILICA SAND AND MINERAL GYPSUM
# ***NEED GRABBER
# ***HAVE 3 CONSECUTIVE VOYAGES PLUS OPTIONAL 3 AS EXTRA
# L/P : AQABA, R. SEA
# D/P : VIZAG, INDIA
# SPOT/PPT
# L/R : 8,000 MT
# D/R : 6,000 MT
# 1.25% PUS
# """
#
# import json
# from loguru import logger
# ins = TextKIE(llm_instance=llm_ins)
# res = ins(
#     rule_config_path=r'W:\Personal_Project\NeiRelated\projects\shipment_solution\extraction_rules\cargo_offer_default.yaml',
#     file_tyle='cargo offer',
#     text_lines=input_text.split('\n'))
# logger
#
# import json
#
# import lark_oapi as lark
# from lark_oapi.api.im.v1 import *
#
#
# # SDK 使用说明: https://github.com/larksuite/oapi-sdk-python#readme
# # 以下示例代码是根据 API 调试台参数自动生成，如果存在代码问题，请在 API 调试台填上相关必要参数后再使用
# # 复制该 Demo 后, 需要将 "YOUR_APP_ID", "YOUR_APP_SECRET" 替换为自己应用的 APP_ID, APP_SECRET.
# def main():
#     # 创建client
#     client = lark.Client.builder() \
#         .app_id("cli_a67a6821cb7e100d") \
#         .app_secret("ewQv9QsRP82WsHATIHS8egqVvcTSNlc8") \
#         .log_level(lark.LogLevel.DEBUG) \
#         .build()
#
#     # 构造请求对象
#     request: ReplyMessageRequest = ReplyMessageRequest.builder() \
#         .message_id("om_1983a6b3c57dc920f3e01dff031db413") \
#         .request_body(ReplyMessageRequestBody.builder()
#             .content("{\"text\":\"test contentaaa\"}")
#             .msg_type("text")
#             .reply_in_thread(True)
#             .uuid("选填dasdf9e20-1dd1-458b-k525-dfeca4015204")
#             .build()) \
#         .build()
#
#     # 发起请求
#     response: ReplyMessageResponse = client.im.v1.message.reply(request)
#
#     # 处理失败返回
#     if not response.success():
#         lark.logger.error(
#             f"client.im.v1.message.reply failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}")
#         return
#
#     # 处理业务结果
#     lark.logger.info(lark.JSON.marshal(response.data, indent=4))
#     return response.data.message_id
#

# from modules.Feishu.Feishu_messages import FeishuMessageHandler
#
# ins = FeishuMessageHandler(config_yaml_path=r'W:\Personal_Project\NeiRelated\projects\shipment_solution\configs\feishu_config.yaml',
#                            )
# ins.send_message_by_template('oc_a139f3e04b26d37d347a4736bbaa0b0a',
#                              'AAq7OhvOhSJB2',
#
#                              {'log_rich_text': 'h'})
#
# # if __name__ == "__main__":
# #     main()
# API Test
import json

import requests

# res = requests.get('http://47.106.198.93:8080/Api/token?appid=bx48H864BV4Z2NX8X8&secret=A9C0DA0868E94F9680444103FF98ACC8')
# res = requests.get('http://47.106.198.93:8080/api/api/Vessel/GetVesselList', headers={
#     'token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhcHBpZCI6ImJ4NDhIODY0QlY0WjJOWDhYOCIsInNlY3JldCI6IkE5QzBEQTA4NjhFOTRGOTY4MDQ0NDEwM0ZGOThBQ0M4IiwidXNlcmlkIjoiNEFERDYzNUY1RDJENDlGRDgyMEUyRTIyNEE4NTM0RkQiLCJleHAiOjE3MzE5MDI4NzguMH0.nKiLTcWEIgycRsqZZ3rqwt2VUV2KwNzetaAQva1JkBw',
#     'Content-Type': 'application/json',
#     'User-Agent': 'My User Agent 1.0'
# })
# print(res.text)
# res = requests.post('http://47.113.144.105:6164/api/add_bx', headers={'Content-Type': 'application/json','User-Agent': 'My User Agent 1.0'}, data={'ddd': 'aaa'})
# print(res.text)