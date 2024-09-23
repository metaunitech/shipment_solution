from modules.key_information_extraction import TextKIE
from langchain_openai import ChatOpenAI

MODEL_NAME = 'glm-4-flash'
API_TOKEN = "7d020833a52b08e7251707288af8d20d.JmuseA1s6dTDSyt7"

llm_ins = ChatOpenAI(temperature=0.95,
                     model=MODEL_NAME,
                     openai_api_key=API_TOKEN,
                     openai_api_base="https://open.bigmodel.cn/api/paas/v4/")




input_text = """50/55,000 MT SILICA SAND AND MINERAL GYPSUM
***NEED GRABBER
***HAVE 3 CONSECUTIVE VOYAGES PLUS OPTIONAL 3 AS EXTRA
L/P : AQABA, R. SEA
D/P : VIZAG, INDIA
SPOT/PPT
L/R : 8,000 MT 
D/R : 6,000 MT
1.25% PUS
"""

import json
from loguru import logger
ins = TextKIE(llm_instance=llm_ins)
res = ins(
    rule_config_path=r'W:\Personal_Project\NeiRelated\projects\shipment_solution\extraction_rules\cargo_offer_default.yaml',
    file_tyle='cargo offer',
    text_lines=input_text.split('\n'))
logger.success(json.dumps(res[0], indent=4, ensure_ascii=False))