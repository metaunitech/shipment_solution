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

from modules.Feishu.Feishu_messages import FeishuMessageHandler

ins = FeishuMessageHandler(config_yaml_path=r'W:\Personal_Project\NeiRelated\projects\shipment_solution\configs\feishu_config.yaml',
                           )
ins.send_message_by_template('oc_a139f3e04b26d37d347a4736bbaa0b0a',
                             'AAq7OhvOhSJB2',

                             {'log_rich_text': 'h'})

# if __name__ == "__main__":
#     main()
