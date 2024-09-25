from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from langchain_core.pydantic_v1 import BaseModel, Field, ConstrainedList
from typing import Union
from langchain_openai import ChatOpenAI
from pathlib import Path
from loguru import logger
from retrying import retry

MODEL_NAME = 'glm-4-flash'
API_TOKEN = 'a9d2815b090f143cdac247d7600a127f.WSDK8WqwJzZtCmBK'


class DocumentChunk(BaseModel):
    document_chunk_body: str = Field(
        description='原文片段内容'
    )


class DocumentChunkResults(BaseModel):
    vessel_info_chunks: ConstrainedList[DocumentChunk] = Field(
        description='原文根据单位（需求或供应）船舶为单位的原文内容，如果邮件内容仅有一艘船舶，返回长度为1的列表。',
    )
    mutual_info: Union[str, None] = Field(
        description='适用于所有原文chunk的信息，通常是卖家/买家信息，greeting等共有信息。'
    )
    comment: str = Field(
        description='上面对于原文进行切片的结果的判断逻辑，用中文。'
    )


class MessageSegmenter:
    def __init__(self):
        self.__prompt_base_dir = Path(__file__).parent / 'prompts'

    def create_llm_instance(self, model_name=MODEL_NAME):
        return ChatOpenAI(temperature=0.95,
                          model=model_name,
                          openai_api_key=API_TOKEN,
                          openai_api_base="https://open.bigmodel.cn/api/paas/v4/")
    @retry(stop_max_attempt_number=2, wait_fixed=2000)
    def segment(self, content, content_type):
        prompt_path = self.__prompt_base_dir / 'chunk_document_parts.txt'
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()

        llm_ins = self.create_llm_instance()
        parser = PydanticOutputParser(pydantic_object=DocumentChunkResults)
        retry_parser = OutputFixingParser.from_llm(parser=parser, llm=llm_ins)

        format_instruction = parser.get_format_instructions()

        message_type = "未知邮件"
        message_type = '货盘邮件' if content_type == 'cargo_info' else message_type
        message_type = '船舶邮件' if content_type == 'ship_info' else message_type

        prompt = prompt_template.format(message_type=message_type,
                                        format_instruction=format_instruction,
                                        input_content=content)
        logger.debug(prompt)
        res_raw = llm_ins.invoke(prompt)
        res_content = res_raw.content
        logger.debug(res_content)
        answer_instance = retry_parser.parse(res_content)
        mutual_info = answer_instance.mutual_info
        vessel_info_chunks = [i.document_chunk_body for i in answer_instance.vessel_info_chunks]
        comment = answer_instance.comment
        return vessel_info_chunks, mutual_info, comment


if __name__ == "__main__":
    ins = MessageSegmenter()
    ins.segment(
        "'/THANH,\n\nPLEASE PPS FOR:\n\nABT 8,500MT MANGANGESE ORE PELLET IN TON BAGS BAYUQUAN / CIGADING 2,000MT / 2,000MT PWWD SHINC 02ND - 05TH OCT. 2024 FIOST BSS 1/1 2.50% PUS\n\nBest regards, Daisy (Ms) | Mobile: +84 9 6307 8281 | Skype: +84 9 6307 8281\n\nIvan (Mr) | Mobile: +84 9 3697 7218 | Skype: +84 9 3697 7218\n\nBroly (Mr) | Mobile: +84 9 3655 8557 | Skype: +84 9 3655 8557\n\nJuan (Mr) | Mobile: +84 7 7538 8898 | Skype: tunghoang1310\n\nThanh (Ms) | Mobile: +84 9 3425 6282 | Skype: thanhngomship\n\nVivian (Ms) | Mobile: +84 9 0322 4396 | Skype: vtrang.1104\n\nLinh Luc (Ms) | Mobile: +84 9 0159 9555 | Skype: luc.thuy.linh\n\nHarry (Mr) | Mobile: +84 9 7621 6688 | Skype: toanship\n\nDavid (Mr) | Mobile: +84 9 7744 5485 | Skype: david.hhd\n\nKhoi Vu (Mr) | Mobile: +84 9 0476 7886 | Skype: khoitoms\n\nMinh Le (Mr) | Mobile: +84 9 3624 8489 | Skype: minh_vnlhp\n\nEmail: trust@ascentbulk.com\n\nWebsite: https://ascentbulk.com/'",
        'cargo_info')
