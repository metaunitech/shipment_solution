# encoding=utf-8
# SHIPMENTFLOW
from main import ShipmentFlow
ins = ShipmentFlow(r'configs/feishu_config.yaml')
# ins.feishu_spreadsheet_handler.batch_get_records(ins.app_token, ins.tables['ship_info'], ['recuy9qvJMDa5O'])
# ins.unit_flow(content="""标题：OPEN TONNAGE 02.01
#  FROM: "Ms Quyen- Hai Phuong Co., LTD" <quyen.chartering@haiphuongship.com.vn>
#  RECEIVE_DATE: 2025-01-02 09:10:49+07:00
#  CONTENT: Dear Sir/ Madams,
#
#            Happy New Year 2025 !
#
# Pls offer suitable cargo/ trip/ TC order for our vsls as flw:
#
#
#
#
# 　VSL
#
# DWCC
#
# 　CAPA　
#
# 　POSITION OPEN
#
# 　DATE　
#
# 　　
#
#
# 1
#
# HPC FUTURE
#
# 32,000
#
# 43,127
#
# RVT
#
#         PG- JAPAN
#
#
# 2
#
# HPC UNITY
#
# 27,800
#
# 39,995
#
# XIAMEN
#
# 19 JAN
#
# W.W  EX USA/ CANADA/ RUS/ RED SEA
#
#
# 3
#
# HSC NEW LUCKY
#
# 32,000
#
# 43,127
#
# YEOSU
#
# 11 JAN
#
# W.W  EX USA/ CANADA/ RUS/ RED SEA
#
# 1. M/V HPC FUTURE
#
# BULKER /SINGLE DECK - VIETNAM FLAG
#
# DWT 32,816.3 MTS ON 10.15M DRFT
#
# CHINA BUILT 2010. CLASS VR
#
# GRT 20767, NRT 12116
#
# LOA 179.9M, BEAM 28.4M, DEPTH 14.1M
#
# HOLDS 5, HATCHES 5. HATCH COVER: MCGREGOR, HYDRO FOLDING TYPE
#
# GRAIN 43127.43 CBM, BALE 41402.40 CBM
#
# 4 X 25T CRANES. GRAB: N.A
#
# (ADA WOG)
#
# 2. M/V HPC UNITY
#
# BULKER /SINGLE DECK - PANAMA FLAG
#
# DWT 29,033 MTS ON 10.038M DRFT
#
# CHINA BUILT 2011. CLASS NK
#
# GRT 18481, NRT 10335
#
# LOA 169.99M, BEAM 27M, DEPTH 14.2M
#
# HOLDS 5, HATCHES 5. HATCH COVER: MCGREGOR, HYDRO FOLDING TYPE
#
# GRAIN 39995.5 CBM, BALE 39070.3 CBM
#
# 4 X 25T CRANES. GRAB: N.A
#
# (ADA WOG)
#
# 3. M/V HSC NEW LUCKY ( EX NAME: HAI PHUONG 87)
#
# BULKER /SINGLE DECK - PANAMA FLAG
#
# DWT 32,816.3 MTS ON 10.15M DR
#
# CHINA BUILT 2009. CLASS NK
#
# GRT 20767, NRT 12116
#
# LOA 179.9M, BEAM 28.4M, DEPTH 14.1M
#
# HOLDS 5, HATCHES 5. HATCH COVER: MCGREGOR, HYDRO FOLDING TYPE
#
# GRAIN 43127.43 CBM, BALE 41402.40 CBM
#
# 4 X 25T CRANES. GRAB: N.A
#
# (ADA WOG)
#
# IF YOU HAVE ANY REQUIREMENT PLS CONTACT WITH ME,
#
# Thank and best regards!
#
#
#  <https://haiphuongship.vn/>
#
#
# Ms Quyen
#
#
# Chartering Department
#
#
# M: (84) 942 608670( Zalo/ whatsapp)
#
# Skype: daoquyen82
#
#
# E:  <mailto:quyen.chartering@haiphuongship.com.vn>
# quyen.chartering@haiphuongship.com.vn
#
#
# Private E:  <mailto:quyenshipping@gmail.com> quyenshipping@gmail.com
#
#
#  <http://haiphuongship.vn/> Hai Phuong Company Limited
#
#
# Hai Phong City | 180000, Viet Nam
# """,receive_id='test001', source_name='email',debug=True, skip_success=False)
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

ins.unit_flow(content="""标题：5500-6000 mts Sugar/Starch/Faba Beans/Macaroni ex Port Tawfique to Hodeidah - Mid March
 FROM: "YMY Global Navigation Ltd" <fix@ymy-navigation.com>
 RECEIVE_DATE: 2025-03-09 22:47:41+02:00
 CONTENT: Dear Sirs / Awad

Good day.

 

Please offer firm/rated tonnage for:

 

Cargo: Total abt 5500/6000 mts

 

A) 3000 MTS BGD SUGAR IN 50 KGS BAGS - SF 1.3 

+                                                    

B) 1500 MTS STARCH IN JUMBO BAGS 1 TON EACH / DIM 1.2 X 1.1 X 1.1 

+

C) ABT 282 MTS FABA BEANS INSIDE 21000 CARTON ON ABT 188 PALLETS OF 1,5 TON
( EACH PALLET 112 CARTONS ) - DIM 1.15 X 1.05 X 1.15

+

D) 1000 MTS MACARONI ON PALLETS OF 1 TON EACH - DIM 1 X 1 X 1.2

 

Load port: 1sp/1sb Port Tawfique, Egypt

Disch port: 1sp/1sb Hodeidah, Yemen

Laycan: Mid March

L/D rates: 800/800 

3.75% ttl comm

 

WCYP?

 

Thanks & Best Regards

Muhammad Awad


Mob

: +20 100 442 8889


Skype

: ymy2011

 



 


Tel/Fax

: +20 66 3251181


E-Mail  

:  <mailto:ymy@ymy-gnt.com> ymy@ymy-gnt.com /
<mailto:fix@ymy-navigation.com> fix@ymy-navigation.com

Freeport Building, 4th Floor, Office No. 412 - Nahda & Memphis St., Port
Said, Egypt

40, Heliopolis Gardens, El-Moltaqa, Autostorad Road, Cairo, Egypt

 

To unsubscribe from this group and stop receiving emails from it, send an email to operators+unsubscribe@ymy-navigation.com.

# Reason: 
邮件中包含了需要运输的货物信息，包括货物的种类、数量、包装、装运港、卸货港、交货时间、运费率等信息，因此属于货盘邮件。
# Translated: 
<货物种类>：糖/淀粉/鹰嘴豆/通心粉<数量>：约5500-6000公吨<包装>：A) 3000公吨糖，50公斤袋装；B) 1500公吨淀粉，1吨袋装；C) 约282公吨鹰嘴豆，21000纸箱装，每托盘1.5吨；D) 1000公吨通心粉，每托盘1吨<装运港>：埃及塔乌菲克港<卸货港>：也门荷台达港<交货时间>：三月中期<运费率>：L/D率800/800
===""", skip_success=False, debug=True)
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
from langchain_openai import ChatOpenAI
from pathlib import Path
import yaml
# def create_llm_instance(model_name="Doubao"):
#     with open(Path(__file__).parent / 'configs' / 'backend_configs.yaml', 'r') as f:
#         config = yaml.safe_load(f)
#     return ChatOpenAI(temperature=0.95,
#                         model=config['LLM'][model_name]['llm_params']['model_name'],
#                         openai_api_key=config['LLM'][model_name]['llm_params']['api_key'],
#                         openai_api_base=config['LLM'][model_name]['llm_params']['endpoint'])
# ins = create_llm_instance()
# res = ins.invoke("hello")
# print(res)
