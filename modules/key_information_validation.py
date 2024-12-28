import datetime
import time

from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from langchain_core.pydantic_v1 import BaseModel, Field
import yaml
import json
from loguru import logger
from pathlib import Path
from retrying import retry
from typing import Dict
import re

MODEL_NAME = 'glm-4-flash'
API_TOKEN = 'a9d2815b090f143cdac247d7600a127f.WSDK8WqwJzZtCmBK'


class Date(BaseModel):
    formatted_date: datetime.datetime = Field(
        description='格式化的日期'
    )
    reason: str = Field(
        description='修改格式的原因'
    )


class RefinedDict(BaseModel):
    refined_dict: Dict = Field(
        description='按照要求修改过值的dict'
    )


class KIValidation:
    def __init__(self):
        validation_requirements_path = Path(__file__).parent / 'knowledges' / 'validation_requirements.yaml'
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
            f'# TASK: \n我需要你帮我把我的类似日期的字符串输入校验并变成一个格式化的日期字符串，格式为%Y-%m-%d. 如果输入没有年份，默认今天的年份。根据FORMAT_SCHEMA返回我JSON格式的字典结果，字典里包含：formatted_date和reason\n'
            f"注：今天是{datetime.datetime.now().strftime('%YY-%MM-%DD')}，"
            f'{comments if comments else ""}\n'
            f'# FORMAT_SCHEMA:\n'
            f"{format_instruction}\n"
            "# EXAMPLES:\n"
            "以下是例子，其中key是输入，输出是对应的value.\n"
            f"{json.dumps(examples, indent=2, ensure_ascii=False) if examples else ''}\n"
            f"# INPUT:\n"
            f"输入：{input}\n"
            f'# FORMAT_SCHEMA:\n'
            f"{format_instruction}\n"
            f"YOUR ANSWER(Result string in JSON Format only):\n"
            f"TS:{str(time.time() * 1000)}")
        logger.debug(prompt)
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

    def parse_rates(self, rate_string):
        # 将字符串转换为大写并去除多余空格
        rate_string = ' '.join(rate_string.upper().split())
        logger.info(f"Parsing : {rate_string}")

        # 正则表达式定义
        pattern1 = re.compile(r'(\d+ MT)\s*/\s*CQD')
        pattern2 = re.compile(r'CQD\s*/\s*(\d+ MT)')

        # 检查是否包含 CQD BENDS
        if 'CQD BENDS' in rate_string:
            return 'CQD', 'CQD'

        # 尝试匹配第一个模式：<数字> MT / CQD
        match1 = pattern1.search(rate_string)
        if match1:
            return match1.group(1), 'CQD'

        # 尝试匹配第二个模式：CQD / <数字> MT
        match2 = pattern2.search(rate_string)
        if match2:
            return 'CQD', match2.group(1)

        # 如果不符合任何条件，则返回 None, None
        return None, None

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def unit_bulk_validate(self, document_type, res, content=None, mutual_content=None, current_missing=None, note=None,
                           extra_knowledge=None):
        logger.info(f"Starts to use extra_knowledge: {extra_knowledge}")
        current_missing = [] if current_missing is None else current_missing
        llm_ins = self.create_llm_instance()
        parser = PydanticOutputParser(pydantic_object=RefinedDict)
        retry_parser = OutputFixingParser.from_llm(parser=parser, llm=llm_ins)
        key_requirement_parts_texts = []
        mandatory_keys = [i for i in self.requirements[document_type] if
                          self.requirements[document_type][i].get('mandatory') == 1]
        for key in self.requirements.get(document_type, {}).keys():
            details_vals = self.requirements.get(document_type, {})[key]
            text = f'字段<{key}>,需要的字段类型是:<{details_vals["type"]}>.'
            comments = details_vals.get('comments')
            examples = details_vals.get('examples')
            if comments:
                text += f'对于该字段，{comments}'
            if examples:
                text += f'我会用一组字典列表给你一些例子，其中的字典（key是输入，value是修改后的结果）：{str(examples)}'
            key_requirement_parts_texts.append(text)
        key_requirement_text = "\n".join(key_requirement_parts_texts)
        format_instruction = parser.get_format_instructions()
        missing_force_prompt = "" if not current_missing else f"当前的提取结果中缺少{current_missing}这几个字段，请从原文依据中提出。"
        prompt = (
            f'# TASK: \n我现在有一个输入字典需要通过API上传，但是字典里有的字段的值不满足字段格式要求。我需要你按照字段的格式要求将我的字典值进行修正，字段名都保持不变\n'
            f'原文中常用的数据展示形式为：<字段A>/<字段B>/<字段C> <ValueA>/<ValueB>/<ValueC>，请仔细检查提取出来的字段是否和表现形式一一对应。\n'
            f'注意：对于KeyValueRequirements提到必须提取到值的字段{str(mandatory_keys)}，如果当前字典中为None或者字典中不存在，则从原文依据中重新提取字段值并加入字典。同时也要校验所有值为空的字段，在文中尝试提取并加入字典。返回我JSON格式。\n'
            f"今天的日期是：{datetime.datetime.now().strftime('%Y-%m-%d')}，仅供参考，校验日期的时候可以借鉴。"
            f'\n# Knowledge:\n'
            f'{"" if not extra_knowledge else extra_knowledge}'
            f'\n# KeyValueRequirements:\n{key_requirement_text}\n'
            f"\n# INPUT:\n"
            f"\n原文依据: \n{str(content) + ';' + (mutual_content if mutual_content else '')}\n"
            f"输入字典：\n{json.dumps(res, indent=2, ensure_ascii=False)}\n"
            f"\n{missing_force_prompt}"
            f"\n{note}"
            f"YOUR ANSWER:\n"
            f"请按照如下格式要求返回我JSON（注意字段名不要发生变动）\n"
            f"{format_instruction}\n"
            f"TS:{str(time.time() * 1000)}")
        try:
            # Invoke the LLM and parse the result
            logger.debug(prompt)
            res_raw = llm_ins.invoke(prompt)
            res_content = res_raw.content
            logger.debug(res_content)
            answer_instance = retry_parser.parse(res_content)
            refined_dict = answer_instance.refined_dict
            to_remove_keyname = []
            for i in refined_dict:
                if refined_dict[i] is None:
                    to_remove_keyname.append(i)
                elif i not in self.requirements[document_type].keys() and i not in res.keys():
                    to_remove_keyname.append(i)

            for i in to_remove_keyname:
                logger.error(f"{i} value {refined_dict[i]} need to be removed. It is not in res.")
                del refined_dict[i]

            for j in res:
                if j not in refined_dict:
                    logger.error(f"{j} value {res[j]} need to be added. It is not in res.")
                    refined_dict[j] = res[j]
            # RULES:
            rate_string = str(content) + ';' + str(mutual_content)
            if document_type == 'ship_info':
                if not refined_dict.get('载重吨-DWT'):
                    refined_dict['载重吨-DWT'] = refined_dict.get('载货吨-DWCC')
                if 'SINGLE DECK' in rate_string:
                    refined_dict['甲板数-DECK'] = 'SD'
                for mv_part in ['MV.', 'M/V.', 'M/V', 'MV', 'M.V']:
                    if mv_part in refined_dict.get('船舶英文名称-ENGLISH-NAME'):
                        vsl_name = re.sub(rf'{mv_part}', '', refined_dict['船舶英文名称-ENGLISH-NAME'])
                        logger.warning(f'Removed {mv_part} in name. Current: {vsl_name}')
                        # vsl_name = refined_dict['船舶英文名称-ENGLISH-NAME'].sub(mv_part, '')
                        refined_dict['船舶英文名称-ENGLISH-NAME'] = vsl_name
                if not refined_dict.get('船舶中文名称-CHINESE-NAME'):
                    refined_dict['船舶中文名称-CHINESE-NAME'] = refined_dict['船舶英文名称-ENGLISH-NAME']
                if 'PPT' in rate_string:
                    logger.warning("PPT found in rate_string.")
                    refined_dict['空船日期-OPEN-DATE'] = datetime.datetime.now().strftime('%Y-%m-%d')
                try:
                    if res.get('空船日期-OPEN-DATE') and datetime.datetime.strptime(res.get('空船日期-OPEN-DATE'), '%Y-%m-%d')-datetime.timedelta(days=1) >= datetime.datetime.now():
                        logger.warning("Reformat to previous extraction result for OPEN-DATE")
                        refined_dict['空船日期-OPEN-DATE'] = res.get('空船日期-OPEN-DATE')
                except:
                    pass

            if document_type == "cargo_info":
                l_rate, d_rate = self.parse_rates(rate_string=rate_string)
                logger.info(f"LDRATE: {l_rate} {d_rate}")
                if l_rate:
                    refined_dict['装率-L-RATE'] = l_rate
                if d_rate:
                    refined_dict['卸率-D-RATE'] = d_rate
                if 'PPT' in rate_string:
                    refined_dict['装运开始日期-LAY-DATE'] = datetime.datetime.now().strftime('%Y-%m-%d')
                    refined_dict['装运结束日期-CANCELING-DATE'] = (datetime.datetime.now()+datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            note = ''
            for k in ['装运开始日期-LAY-DATE', '装运结束日期-CANCELING-DATE', '空船日期-OPEN-DATE']:
                if k in refined_dict.keys():
                    try:
                        date_val = datetime.datetime.strptime(refined_dict[k], "%Y-%m-%d")
                        if date_val + datetime.timedelta(days=1) < datetime.datetime.now():
                            refined_dict[k] = None
                            note += f"{k} should be later than {datetime.datetime.now().strftime('%Y-%m-%d')}\n"
                            logger.error(f"{k} should be later than {datetime.datetime.now().strftime('%Y-%m-%d')}")
                    except:
                        note+= f"Current {k}:{refined_dict[k]} not in datetime format. Need reformat.\n"
                        logger.error(f"Current {k}:{refined_dict[k]} not in datetime format. Need reformat.")
                        refined_dict[k] = None

            # Check if the keys are modified
            # if any([i not in res.keys() for i in refined_dict.keys()]):
            #     raise ValueError(
            #         f"Fields modified. {set(refined_dict.keys()) - set(res.keys())}, {set(res.keys()) - set(refined_dict.keys())}")

            return refined_dict, note

        except Exception as e:
            logger.error(f"Error during validation: {e}")
            raise

    def check_if_mandatory_fit(self, document_type, refined_dict):
        out = []
        logger.info(f"Current dict: {json.dumps(refined_dict, indent=2, ensure_ascii=False)}")
        mandatory_keys = [i for i in self.requirements[document_type] if
                          self.requirements[document_type][i].get('mandatory') == 1]
        for k in mandatory_keys:
            if k not in refined_dict:
                out.append(k)
        return out

    def bulk_validate(self, document_type, extraction_res, extra_knowledge=None):
        output_res = []

        for res_all in extraction_res:
            res, body, mutual_body = tuple(res_all)
            missing_keys = None
            note = None
            refined_dict = res
            for i in range(5):
                refined_dict, note = self.unit_bulk_validate(document_type, refined_dict, current_missing=missing_keys,
                                                             content=body, mutual_content=mutual_body, note=note, extra_knowledge=extra_knowledge)
                missing_keys = self.check_if_mandatory_fit(document_type, refined_dict)

                if not missing_keys:
                    logger.success("No missing keys")
                    break
                else:
                    logger.info(f"Missing keys {missing_keys}, attempt: {i}")
            output_res.append([refined_dict, body, mutual_body])
        return output_res

    def validate(self, document_type, extraction_res):
        output_res = []
        todo_keys = list(self.requirements.get(document_type, {}).keys())
        for res_all in extraction_res:
            res, body, mutual_body = tuple(res_all)
            cur_res = {}
            for key in res:
                if key in todo_keys and self.requirements.get(document_type, {}).get(key, {}).get('function'):
                    logger.info(f"Validate: {key}")
                    validate_method_name = self.requirements[document_type][key].get('function')
                    comments = self.requirements[document_type][key].get('comments')
                    examples = self.requirements[document_type][key].get('examples')

                    validate_method = getattr(self, validate_method_name, None)
                    if not validate_method:
                        logger.error(f"VALIDATION METHOD: {validate_method_name} not Exist.")
                        cur_res[key] = res[key]
                        continue
                    for i in range(4):
                        try:
                            modified_value = validate_method(input=res[key], comments=comments, examples=examples)
                            break
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
    res = ins.parse_rates(
        "20,000 MT STEEL COILS\nBAHODOPI /TIANJIN\n30 DEC-05 JAN\n7000 MT /CQD\nFIO\nADCOM: 2.5% PUS\n原文得一些总结和分析：邮件内容提到了需要运输的货物，包括20,000MT钢卷，并指定了装运港（BAHODOPI /TIANJIN）和日期（30 DEC-05 JAN），同时提到了卸货量（7000 MT）和FIO条款，符合货盘邮件的特征。")
    print(res)
