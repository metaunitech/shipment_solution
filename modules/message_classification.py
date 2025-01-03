from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
import yaml
import json
from pathlib import Path
from loguru import logger

MODEL_NAME = 'glm-4-flash'
API_TOKEN = 'a9d2815b090f143cdac247d7600a127f.WSDK8WqwJzZtCmBK'


class DocumentType(BaseModel):
    document_type: str = Field(
        description='收到消息的种类，从如下三种里选择：ship_info, cargo_info, others.',
        options=['ship_info', 'cargo_info', 'others']
    )
    entry_count: int = Field(
        description="若document_type是船盘，返回当前邮件中可供出租的船的数量，一般出现新的船名就是一个可供出租的船舶；若document_type是货盘，返回邮件中需要租赁的需求数量，一般出现一个新的商品就是一个需要租赁的需求；若是其他邮件返回0"
    )
    reason: str = Field(
        description='做出消息分类的原因。'
    )
    translated_content: str = Field(
        description='根据船舶相关基础知识和提供的Knowledge精简地总结消息中包含的货盘（同样的货物）/船盘（同样的船名）的所有参数信息（可能分散在消息不同位置），数量和entry_count一致。'
    )


class MessageClassifier:
    def __init__(self):
        self.__prompt_base_dir = Path(__file__).parent / 'prompts'
        self.__example_base_dir = Path(__file__).parent / 'knowledges'

    def create_llm_instance(self, model_name=MODEL_NAME):
        return ChatOpenAI(temperature=0.95,
                          model=model_name,
                          openai_api_key=API_TOKEN,
                          openai_api_base="https://open.bigmodel.cn/api/paas/v4/")

    def classify(self, content, extra_knowledge=None):
        logger.info(f"Starts to use extra_knowledge: {extra_knowledge}")
        prompt_path = self.__prompt_base_dir / 'classify_document_type.txt'
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()

        examples_map_path = self.__example_base_dir / 'document_type_examples.yaml'
        with open(examples_map_path, 'r', encoding='utf-8') as f:
            examples = yaml.load(f, Loader=yaml.FullLoader)

        ship_info_examples = examples.get('ship_info')
        ship_info_examples_str = '暂无' if not ship_info_examples else json.dumps(ship_info_examples, indent=2,
                                                                                  ensure_ascii=False)
        cargo_info_examples = examples.get('cargo_info')
        cargo_info_examples_str = '暂无' if not cargo_info_examples else json.dumps(cargo_info_examples, indent=2,
                                                                                    ensure_ascii=False)
        other_examples = examples.get('others')
        other_examples_str = '暂无' if not other_examples else json.dumps(other_examples, indent=2,
                                                                          ensure_ascii=False)
        llm_ins = self.create_llm_instance()
        parser = PydanticOutputParser(pydantic_object=DocumentType)
        retry_parser = OutputFixingParser.from_llm(parser=parser, llm=llm_ins)

        format_instruction = parser.get_format_instructions()

        prompt = prompt_template.format(ship_info_type_examples=ship_info_examples_str,
                                        cargo_info_type_examples=cargo_info_examples_str,
                                        other_type_examples=other_examples_str,
                                        format_instruction=format_instruction,
                                        input_content=content,
                                        extra_knowledge='' if not extra_knowledge else extra_knowledge)
        # logger.debug(prompt)
        res_raw = llm_ins.invoke(prompt)
        res_content = res_raw.content
        logger.debug(res_content)
        answer_instance = retry_parser.parse(res_content)
        document_type = answer_instance.document_type
        entry_count = answer_instance.entry_count
        reason = answer_instance.reason
        translated_content = answer_instance.translated_content
        logger.success(f'Content type: {document_type}. Entry count: {entry_count} Reason: {reason}. Translated: {translated_content}')
        # RULES:
        cargo_keywords = ['CQD', ' SF ']
        ship_keywords = []
        if any([i in content for i in cargo_keywords]) and document_type != 'cargo_info':
            document_type = 'cargo_info'
            reason = 'force to 货盘邮件'
        if any([i in content for i in ship_keywords]) and document_type != 'ship_info':
            document_type = 'ship_info'
            reason = 'force to 船盘'
        return document_type, reason, entry_count, translated_content


if __name__ == '__main__':
    ins = MessageClassifier()
    ins.classify(
        '/THANH,\n\nPLEASE PPS FOR:\n\nABT 8,500MT MANGANGESE ORE PELLET IN TON BAGS BAYUQUAN / CIGADING 2,000MT / 2,000MT PWWD SHINC 02ND - 05TH OCT. 2024 FIOST BSS 1/1 2.50% PUS\n\nBest regards, Daisy (Ms) | Mobile: +84 9 6307 8281 | Skype: +84 9 6307 8281\n\nIvan (Mr) | Mobile: +84 9 3697 7218 | Skype: +84 9 3697 7218\n\nBroly (Mr) | Mobile: +84 9 3655 8557 | Skype: +84 9 3655 8557\n\nJuan (Mr) | Mobile: +84 7 7538 8898 | Skype: tunghoang1310\n\nThanh (Ms) | Mobile: +84 9 3425 6282 | Skype: thanhngomship\n\nVivian (Ms) | Mobile: +84 9 0322 4396 | Skype: vtrang.1104\n\nLinh Luc (Ms) | Mobile: +84 9 0159 9555 | Skype: luc.thuy.linh\n\nHarry (Mr) | Mobile: +84 9 7621 6688 | Skype: toanship\n\nDavid (Mr) | Mobile: +84 9 7744 5485 | Skype: david.hhd\n\nKhoi Vu (Mr) | Mobile: +84 9 0476 7886 | Skype: khoitoms\n\nMinh Le (Mr) | Mobile: +84 9 3624 8489 | Skype: minh_vnlhp\n\nEmail: trust@ascentbulk.com\n\nWebsite: https://ascentbulk.com/')
