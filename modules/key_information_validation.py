import datetime

from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from langchain_core.pydantic_v1 import BaseModel, Field
import yaml
import json
from loguru import logger
from pathlib import Path
from retrying import retry


MODEL_NAME = 'glm-4-flash'
API_TOKEN = 'a9d2815b090f143cdac247d7600a127f.WSDK8WqwJzZtCmBK'


class Date(BaseModel):
    formatted_date: datetime.datetime = Field(
        description='格式化的python Datetime 输出。'
    )
    reason: str = Field(
        description='格式化的原因'
    )


class KIValidation:
    def __init__(self):
        validation_requirements_path = Path(__file__).parent/'knowledges'/'validation_requirements.yaml'
        with open(validation_requirements_path, 'r', encoding='utf-8') as f:
            self.requirements = yaml.load(f, Loader=yaml.FullLoader)

    def create_llm_instance(self, model_name=MODEL_NAME):
        return ChatOpenAI(temperature=0.95,
                          model=model_name,
                          openai_api_key=API_TOKEN,
                          openai_api_base="https://open.bigmodel.cn/api/paas/v4/")
    @retry(stop_max_attempt_number=2, wait_fixed=2000)
    def validate_date(self, input, comments=None, examples=None):
        comments = '' if not comments else comments
        try:
            formatted_date = datetime.datetime.strptime(input, '%Y-%m-%d')
            return formatted_date.strftime('%Y-%m-%d')
        except Exception as e:
            comments += f"\n{str(e)}"

        llm_ins = self.create_llm_instance()
        parser = PydanticOutputParser(pydantic_object=Date)
        retry_parser = OutputFixingParser.from_llm(parser=parser, llm=llm_ins)

        format_instruction = parser.get_format_instructions()
        prompt = (
            f'#TASK: 我需要你帮我把我的输入变成一个日期，格式为%Y-%m-%d. 如果输入没有年份，默认今天的年份。\n'
            f'{comments if comments else ""}\n'
            "EXAMPLES:\n"
            "以下是例子，以JSON的格式给你，其中key是输入，输出是对应的value.\n"
            f"{json.dumps(examples, indent=2, ensure_ascii=False) if examples else ''}\n"
            f"# INPUT:\n"
            f"输入：{input}\n"
            f"注：今天是{datetime.datetime.now().strftime('%YY-%MM-%DD')}，"
            f"YOUR ANSWER:\n"
            f"请按照如下格式要求返回我JSON\n"
            f"{format_instruction}")
        res_raw = llm_ins.invoke(prompt)
        res_content = res_raw.content
        logger.debug(res_content)
        answer_instance = retry_parser.parse(res_content)
        formatted_date = answer_instance.formatted_date
        return formatted_date.strftime('%Y-%m-%d')

    def validate_literal(self, input, comments=None):
        pass

    def validate_number(self, input, comments=None):
        pass

    def validate(self, document_type, extraction_res):
        output_res = []
        todo_keys = [list(self.requirements.get(document_type, {}).keys())[0] for i in self.requirements.get(document_type, {}).keys()]
        for res_all in extraction_res:
            res, body, mutual_body = tuple(res_all)
            cur_res = {}
            for key in res:
                if key in todo_keys:
                    validate_method_name = self.requirements[document_type][key].get('function')
                    comments = self.requirements[document_type][key].get('comments')
                    examples = self.requirements[document_type][key].get('examples')

                    validate_method = getattr(self, validate_method_name, None)
                    if not validate_method:
                        logger.error(f"VALIDATION METHOD: {validate_method_name} not Exist.")
                        cur_res[key] = res[key]
                        continue
                    try:
                        modified_value = validate_method(input=res[key], comments=comments, examples=examples)
                    except Exception as e:
                        logger.error(f"Not modified. ERROR: {str(e)}")
                        modified_value = res[key]
                    logger.success(f"{key}: {res[key]}->{modified_value}")
                    cur_res[key] = modified_value
                else:
                    cur_res[key] = res[key]
            output_res.append([cur_res, body, mutual_body])
        return output_res

if __name__ == "__main__":
    ins = KIValidation()
    ins.validate_date('3-5 SEPT 2024')
