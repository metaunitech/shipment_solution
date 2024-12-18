# encoding=utf-8
# SHIPMENTFLOW
from main import ShipmentFlow
ins = ShipmentFlow(r'W:\Personal_Project\NeiRelated\projects\shipment_solution\configs\feishu_config.yaml')
ins.unit_flow(content="""YONG DING HE 22K BLT 2008 OPEN KEMAMAN SPOT""",receive_id='test001', receive_type='email',debug=False)
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