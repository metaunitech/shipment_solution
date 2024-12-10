# SHIPMENTFLOW
from main import ShipmentFlow
ins = ShipmentFlow(r'/Users/anthonyf/Desktop/MetaInFlow/shipment_solution/configs/feishu_config.yaml')
ins.unit_flow(content="""FM: GRAIN COMPASS KFT

TO: CHARTERING DEPARTMENT



M/V EURO BAND /'09/BC/58K DWT/ 30MT+GR - OPEN WARF INT CONAKRY 16-25 DEC 2024 AGW WP UCE


GOOD DAY,
DEAR COLLEAGUES,



M/V EURO BAND /'09/BC/58K DWT/ 30MT+GR - OPEN WARF INT CONAKRY 16-25 DEC 2024 AGW WP UCE



- FLEXIBLE CARGO/TRADING
- BSEA HRA/GOA/WAFR HRA/VENEZVELA OK
- 2*25, DECK, HBI OK
- NO USA/EU PORTS



VESSEL’S DESCRIPTION

MV EURO BAND
TYPE OF VESSEL: BULK CARRIER
BUILT: APRIL 2009, FLAG: PANAMA
DWT / DRAFT: SUMMER SALT WATER: 58,761 MT / 12.828 M
GROSS TONNAGE: 32,379 NET TONNAGE: 19,353
LOA: 189.99 M BEAM: 32.26 M LBP: 185.60 M DEPTH MOULDED: 18.00 M
CARGO GEAR: YES X 4 X 30 MT SWL
CARGO GEAR WITH GRABS: 4X 24 MT SWL
GRABS: YES

GRAIN CAPACITY:
NO. 1: 12,361.2 CBM
NO. 2: 15,976.4 CBM
NO. 3: 14,510.6 CBM
NO. 4: 15,971.0 CBM
NO. 5: 13,541.1 CBM
BALE CAPACITY:
NO. 1: 11,900.5 CBM
NO. 2: 15,625.2 CBM
NO. 3: 14,163.7 CBM
NO. 4: 15,608.8 CBM
NO. 5: 13,259.6 CBM

SPEED / CONSUMPTION:

LADEN VOYAGE
11.00 KNOTS ON 20.0 MT VLSFO + 0.1 MT LSMGO
12.00 KNOTS ON 24.0 MT VLSFO + 0.1 MT LSMGO

BALLAST VOYAGE
12.00 KNOTS ON 18.0 MT VLSFO + 0.1 MT LSMGO
13.00 KNOTS ON 21.0 MT VLSFO + 0.1 MT LSMGO

IDLE: 2.5 MT/DAY VLSFO + 0.1 MT/DAY LSMGO
WORKING: 5.5 MT/DAY VLSFO + 0.5 MT/DAY LSMGO
ALL DETAILS ABOUT WOG



LOOKING FORWARD TO YOUR FIRM OFFERS.

KIND AND BEST REGARDS

ANDRII POGORELOV
VOLODYMYR LYTVYNENKO

CHARTERING DEPARTMENT
(AS AGENTS ONLY)
FOR AND ON BEHALF OF
============================================
GRAIN COMPASS KFT
E-MAIL: chartering@graincom-shipping.com
============================================


Click here to leave mailing list""",receive_id='om_752d3a80e23d19daf5bda61e2473eef5', receive_type='chat_id')

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
