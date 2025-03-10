import datetime
import random
import re
import traceback

from nltk.corpus import crubadan
from retrying import retry
from langchain_openai import ChatOpenAI
from modules.models.output_parser import KeyValuePairList, KeyValuePair, KeyValuePairDict
from langchain.output_parsers import PydanticOutputParser
from loguru import logger
import json
from pathlib import Path
import concurrent.futures
from typing import List, Dict, Any, Optional

import yaml


class KIEException(Exception):
    pass


class TextKIE:
    def __init__(self, llm_instance: ChatOpenAI):
        self.llm_engine = llm_instance
        self.content_slices = []
        self.extraction_history = {}

    @staticmethod
    def default_parse(input_str, target_keys):
        input_str = re.sub('\n', ' ', input_str)
        match = re.search(r'(\{.*})', input_str)
        if not match:
            return {}
        input_str = match.group(1)
        res = json.loads(input_str)
        output = []
        if isinstance(res, dict):
            if len(res.keys()) > 1:
                for k in target_keys:
                    if res.get(k):
                        # output[k] = res.get(k)
                        output.append({k: res.get(k)})
            else:
                for k in target_keys:
                    _res = res[list(res.keys())[0]]
                    if _res.get(k):
                        # output[k] = _res.get(k)
                        output.append({k: _res.get(k)})
        elif isinstance(res, list):
            for l in res:
                if isinstance(l, dict):
                    if len(l.keys()) == 1 and list(l.keys())[0] in target_keys:
                        output.append(l)

        processed_outs = {}
        for i in output:
            processed_outs.update(i)

        return processed_outs

    @staticmethod
    def default_parse_2(input_str, target_keys):
        raw_pairs = re.findall(r'"(.*?)"\s{0,1}:\s{0,1}"(.*?)"', input_str)
        output = {}
        for pair in raw_pairs:
            output[pair[0]] = pair[1]
        return output

    def brief_validation(self, file_type, keys, current_results, raw_text):
        final_res = True
        notes = []
        for key in keys:
            if key in ['报盘公司-COMPANY', '备注-REMARK', '船舶中文名称-CHINESE-NAME', '船东-OWNER']:
                if isinstance(current_results.get(key), str):
                    chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
                    if bool(chinese_pattern.search(current_results[key])):
                        notes.append([f'注意：{key}的结果应该是英文'])
                        final_res = False
        for k in ['装运开始日期-LAY-DATE', '装运结束日期-CANCELING-DATE', '空船日期-OPEN-DATE']:
            if k in keys:
                try:
                    date_val = datetime.datetime.strptime(current_results[k], "%Y-%m-%d")
                    if current_results[k] == datetime.datetime.now().strftime('%Y-%m-%d'):
                        final_res = False
                except:
                    notes.append(f"注意：{k} 的结果格式应为%Y-%m-%d")
                    final_res = False
        return final_res, notes

    def explain_before_extraction(self, file_type, raw_text):
        prompt_path = Path(__file__).parent/'prompts'/f'explain_raw_text_{file_type}.txt'
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
        prompt = prompt_template.format(input_content=raw_text)
        res = self.llm_engine.predict(prompt)
        return res

    @retry(stop_max_attempt_number=3, wait_fixed=0.5)
    def extract_unit(self, file_type, raw_text, keys, key_definitions=None, extraction_method=None,
                     background_infos=None):
        # parser = PydanticOutputParser(pydantic_object=KeyValuePairList)
        # parser2 = PydanticOutputParser(pydantic_object=KeyValuePair)
        parser3 = PydanticOutputParser(pydantic_object=KeyValuePairDict)
        parser = parser3

        key_definitions = {} if not key_definitions else key_definitions
        key_definitions_str = ''

        for k in key_definitions:
            key_definitions_str += f"字段[{k}]指的是：{key_definitions[k][0]}\n返回的格式是:{key_definitions[k][1]}\n" if isinstance(
                key_definitions[k], list) and len(
                key_definitions[k]) >= 2 else f"字段[{k}]指的是：{key_definitions[k]}\n"
        if extraction_method is None:
            extraction_method = {}
        raw_file_type = extraction_method.get('raw_file_type')
        extraction_method_str = extraction_method.get("extraction_method")
        extraction_result_description = extraction_method.get('extraction_result_description')
        extraction_method_description = f'该文件是{raw_file_type}格式的，我通过{extraction_method_str}的方式从文件中提取出了原文。{extraction_result_description}' if extraction_method else ''

        if background_infos is None:
            background_infos = []

        today_ts = datetime.datetime.now().strftime('%Y-%m-%d')

        background_info_str = "\n".join(background_infos)

        format_instructions = parser.get_format_instructions()
        random.shuffle(keys)
        required_key_info = str(keys)

        if key_definitions:
            prompt = f"""# TASK： 我会给你一段{file_type}的内容，
{extraction_method_description}
我需要你帮我从内容中根据我提供的信息做关键信息提取的任务。
            
我所需要的关键信息字段如下：
{required_key_info}。

# BACKGROUND
今天日期：{today_ts}

原文中的一些背景知识如下：
{background_info_str}

对于需要提取的字段的定义如下：
{key_definitions_str}
帮我从文中提取：{required_key_info}
            
如果需要提取的字段没有给你定义，请按照你的常识进行提取。
# INPUT
你所需要处理的文件内容为：
[文件内容开始]
{raw_text}
[文件内容结束]

注意：
1）不要杜撰，请从文件内提取出关键信息，可以换一种说法，但不能凭空捏造。
2）如果原文中没有包含目标字段的关键信息，请不要在结果的JSON中包含该字段
3）如果原文中出现背景信息中的词汇，请务必结合背景知识的语义以及原文来推测是否包含目标字段信息。
4）原文中的人名，地名，公司名等名词请保留其原有的语言，不要进行翻译。
5）对于数字，比例等具体的值必须在原文中出现才提取出来，不要自己捏造。
6）并不是所有字段都能在原文中找到，对于文中没有提及的字段，返回None
7）原文中常用的数据展示形式为：<字段A>/<字段B>/<字段C> <ValueA>/<ValueB>/<ValueC>，表示<字段A>=<ValueA>, <字段B>=<ValueB>, <字段C>=<ValueC>.以此类推
8）所有的提取内容除了“船舶中文名称”都必须是英文，全部输出英文！
请结合注意事项、背景知识、目标字段的解释 Step by Step从我提供的原文中提取出目标字段。


你做的关键信息提取的结果以JSON格式返回给我。 {format_instructions}
YOUR ANSWER:
            """
            logger.debug(prompt)
            res_content = self.llm_engine.predict(prompt)
        else:
            prompt = f"""# TASK： 我会给你一段{file_type}类型文件的内容，我需要你帮我从内容中根据我提供的信息做关键信息提取的任务。
{extraction_method_description}
我需要你帮我从内容中根据我提供的信息做关键信息提取的任务。

# BACKGROUND       
今天日期：{today_ts}
     
原文中的一些背景知识如下：
{background_info_str}

我所需要的关键信息字段如下：
{required_key_info}。
帮我从文中提取：{required_key_info}


# INPUT
你所需要处理的文件内容为：
[文件内容开始]
{raw_text}
[文件内容结束]

注意：
1）不要杜撰，请从文件内提取出关键信息，可以换一种说法，但不能凭空捏造。
2）如果原文中没有包含目标字段的关键信息，请不要在结果的JSON中包含该字段
3）如果原文中出现背景信息中的词汇，请务必结合背景知识的语义以及原文来推测是否包含目标字段信息。
4）原文中的人名，地名，公司名等名词请保留其原有的语言，不要进行翻译。
5）对于数字，比例等具体的值必须在原文中出现才提取出来，不要自己捏造。
6）并不是所有字段都能在原文中找到，对于文中没有提及的字段，返回‘无’
7）原文中常用的数据展示形式为：<字段A>/<字段B>/<字段C> <ValueA>/<ValueB>/<ValueC>，表示<字段A>=<ValueA>, <字段B>=<ValueB>, <字段C>=<ValueC>.以此类推
8）所有的提取内容除了“船舶中文名称”都必须是英文，全部输出英文！

请结合注意事项、背景知识、目标字段的解释 Step by Step从我提供的原文中提取出目标字段。

你做的关键信息提取的结果以JSON格式返回给我。 {format_instructions}
YOUR ANSWER:
            """
            # logger.debug(prompt)
            res_content = self.llm_engine.predict(prompt)
        logger.info(res_content)
        pairs = {}
        for par in [parser]:
            # for par in [parser, parser2, parser3]:
            try:
                pairs = par.parse(res_content)
                logger.success("Parse success")
                pairs = pairs.key_value_pairs
                break
            except:
                logger.warning(traceback.format_exc())
                pass
        if not pairs:
            try:
                pairs = self.default_parse(input_str=res_content,
                                           target_keys=keys)
            except:
                logger.debug(traceback.format_exc())
                try:
                    pairs = self.default_parse_2(input_str=res_content,
                                                 target_keys=keys)
                except:
                    logger.error(traceback.format_exc())
                    pass

        pairs = {i: pairs[i] for i in pairs.keys() if
                 pairs[i] not in ['NAN', 'N/A', '无', '未提及', '未定义', '未提供', 'plaintext', '未知', '无明确描述', 'Not specified', '无明确说明', 'YES', 'None'] and pairs[
                     i] != i}

        for i in pairs:
            if not isinstance(pairs[i], str):
                pairs[i] = str(pairs[i])
                # raise KIEException(f"Output should be string. {pairs[i]}")

        logger.success("Pairs extracted.")
        logger.success(json.dumps(pairs, ensure_ascii=False, indent=4))

        return pairs

    def extract(self, file_type, raw_text_lines, target_key_raw,
                key_definition_max_length=15,
                text_line_max=50,
                method_description_dict=None, background_infos=None, explain_mode_on=False):
        output = {}
        conflict_outs = {}
        if explain_mode_on:
            logger.info("Using explained mode.")
            translated_text = self.explain_before_extraction(file_type, '\n'.join(raw_text_lines))
            raw_text_lines = translated_text.split('\n')
            logger.info(f"Explained content: \n{translated_text}")
        # Split text lines
        part_count = len(raw_text_lines) // text_line_max + 1
        parts = []
        for i in range(part_count):
            if (i + 1) * text_line_max >= len(raw_text_lines):
                parts.append(raw_text_lines[i * text_line_max:])
            else:
                parts.append(raw_text_lines[i * text_line_max: (i + 1) * text_line_max])
        self.content_slices = parts
        # Slice target keys
        key_parts = []
        key_part_count = len(target_key_raw) // key_definition_max_length + 1
        for i in range(key_part_count):
            if (i + 1) * key_definition_max_length > len(target_key_raw):
                cur_parts = target_key_raw[i * key_definition_max_length:]
            else:
                cur_parts = target_key_raw[i * key_definition_max_length: (i + 1) * key_definition_max_length]
            if not cur_parts:
                continue
            key_parts.append(cur_parts)
        # Loop over slices & keys
        for idx1, txt_part in enumerate(parts):
            txt_part = [i for i in txt_part if i]
            txt = '\n'.join(txt_part)
            for idx2, key_part in enumerate(key_parts):
                todo_keys = []
                key_definitions = {}
                to_remove_key_parts = []
                for i in key_part:
                    # Hot fix: added keyword mode.
                    key_possible_area_keywords = []
                    if isinstance(i, dict):
                        _target_key = list(i.keys())[0]
                        key_details = i[_target_key]
                        for ele in key_details:
                            if isinstance(ele, dict):
                                mandatory_keywords = ele.get('mandatory', [])
                                optional_keywords = ele.get('optional', [])
                                txt = txt.upper()
                                if mandatory_keywords:
                                    for w in mandatory_keywords:
                                        w = w.upper()
                                        if not re.search(rf"\n*.*?{w}.*?\n", txt):
                                            # if w not in txt:
                                            logger.warning(
                                                f"{w} is a mandatory word for {_target_key}. Missing thus skipped.")
                                            to_remove_key_parts.append(_target_key)
                                for w in optional_keywords:
                                    w = w.upper()
                                    search_res = re.search(rf"\n*(.*?{w}.*)\n*?", txt,flags=re.MULTILINE)
                                    logger.debug(rf"\n*(.*?{w}.*)\n*?")
                                    logger.debug(txt)
                                    logger.debug(search_res)
                                    if search_res:
                                        key_possible_area_keywords.append(search_res.group(1))
                                        logger.success(
                                            f"{w} is a optional regex for {_target_key}. Possibly in {search_res.group(1)}")
                    # Add keyword and key def.
                    if isinstance(i, str):
                        todo_keys.append(i)
                    elif isinstance(i, dict):
                        _target_key = list(i.keys())[0]
                        if _target_key in to_remove_key_parts:
                            logger.warning(f'{_target_key} missing mandatory keywords')
                            continue
                        key_details = i[_target_key]
                        key_possible_area_keywords = list(set(key_possible_area_keywords))
                        if key_possible_area_keywords:
                            logger.warning(f"Found key_possible_area:{key_possible_area_keywords}")
                            i[_target_key][
                                0] += f'\n{_target_key}可能出现在如下句子附近（也有可能不存在，请结合上下文理解并提取）：{";".join(key_possible_area_keywords)}'
                        todo_keys.append(_target_key)
                        key_definitions.update({_target_key: key_details[0]})

                logger.info(f"Starts to do txt part {idx1}[{parts}]; Keys part: {idx2} [{todo_keys}]")
                try:
                    notes = []
                    cur_res = {}
                    for attempt in range(5):
                        if not notes:
                            cur_background_infos = background_infos
                        else:
                            if background_infos is None:
                                cur_background_infos = notes
                            else:
                                cur_background_infos = background_infos + notes
                        cur_res = self.extract_unit(file_type, txt, todo_keys, key_definitions,
                                                    extraction_method=method_description_dict,
                                                    background_infos=cur_background_infos)
                        # Add check cur_res
                        if_valid_res, notes = self.brief_validation(file_type, todo_keys, cur_res, txt)
                        if if_valid_res:
                            logger.success("Current result is valid.")
                            break
                        else:
                            notes_str = '\n'.join(notes)
                            logger.warning(f"[Attempt {attempt}] Current result not valid. {notes_str}")

                    for k in cur_res:
                        self.extraction_history[k + (cur_res[k])] = idx1
                    logger.success(f"{idx1}&{idx2}")
                except:
                    logger.error(traceback.format_exc())
                    cur_res = {}
                cur_conflicts = {i: cur_res[i] for i in cur_res if i in output and output[i] != cur_res[i]}
                conflict_outs.update(cur_conflicts)
                cur_res_good = {i: cur_res[i] for i in cur_res if i not in output}
                output.update(cur_res_good)

        all_keys = []
        for i in target_key_raw:
            if isinstance(i, str):
                all_keys.append(i)
            if isinstance(i, dict):
                all_keys.append(list(i.keys())[0])

        modified_outputs = {i: output.get(i) for i in all_keys if output.get(i)}
        modified_conflicts = {i: conflict_outs.get(i) for i in all_keys if conflict_outs.get(i)}
        return modified_outputs, modified_conflicts
    # def extract(self, file_type: str, raw_text_lines: List[str], target_key_raw: List[str],
    #             key_definition_max_length: int = 15, text_line_max: int = 50,
    #             method_description_dict: Optional[Dict[str, str]] = None,
    #             background_infos: Optional[Dict[str, Any]] = None, if_parallel: bool = False) -> Dict[str, Any]:
    #     """
    #     Extract information from text with optional parallel processing.
    #
    #     :param file_type: Type of the file.
    #     :param raw_text_lines: List of text lines from the file.
    #     :param target_key_raw: List of target keys to extract.
    #     :param key_definition_max_length: Max number of keys per extraction batch.
    #     :param text_line_max: Max number of lines per text slice.
    #     :param method_description_dict: Optional descriptions for extraction methods.
    #     :param background_infos: Additional context for extraction.
    #     :param if_parallel: Whether to process slices in parallel.
    #     :return: Dictionary of extracted key-value pairs.
    #     """
    #     # Split text into slices
    #     text_slices = [
    #         "\n".join(raw_text_lines[i:i + text_line_max])
    #         for i in range(0, len(raw_text_lines), text_line_max)
    #     ]
    #
    #     # Split keys into smaller groups
    #     key_groups = [
    #         target_key_raw[i:i + key_definition_max_length]
    #         for i in range(0, len(target_key_raw), key_definition_max_length)
    #     ]
    #
    #     results = {}
    #
    #     def process_slice_and_keys(slice_text, keys):
    #         return self.extract_unit(
    #             file_type=file_type,
    #             raw_text=slice_text,
    #             keys=keys,
    #             key_definitions=method_description_dict,
    #             background_infos=background_infos
    #         )
    #
    #     if if_parallel:
    #         # Parallel execution
    #         with concurrent.futures.ThreadPoolExecutor() as executor:
    #             future_to_slice = {
    #                 executor.submit(process_slice_and_keys, slice_text, keys): (slice_text, keys)
    #                 for slice_text in text_slices for keys in key_groups
    #             }
    #             for future in concurrent.futures.as_completed(future_to_slice):
    #                 try:
    #                     result = future.result()
    #                     results.update(result)
    #                 except Exception as e:
    #                     print(f"Error processing slice: {e}")
    #     else:
    #         # Sequential execution
    #         for slice_text in text_slices:
    #             for keys in key_groups:
    #                 result = process_slice_and_keys(slice_text, keys)
    #                 results.update(result)
    #
    #     return results

    @staticmethod
    def parse_extraction_rule_configs(config_file_path):
        """

        :param config_file_path:
        :return: keys_raw, backgrounds
        """
        with open(config_file_path, 'r', encoding='utf-8') as f:
            config_data = yaml.load(f, Loader=yaml.FullLoader)
        return config_data.get('keys', []), config_data.get('background', [])

    def clear_memory(self):
        self.content_slices = []
        self.extraction_history = {}

    def __call__(self, *args, **kwargs):
        """

        :param args: rule_config_path: [str/pathlike], text_lines: list[str]
        :param kwargs: rule_config_path: [str/pathlike], text_lines: list[str], key_definition_max_length, method_description_dict
        :return:
        """
        rule_config_path = kwargs.get('rule_config_path') if not args else args[0]
        if not rule_config_path:
            raise KIEException('rule_config_path is not provided.')
        target_key_raw, background_infos = self.parse_extraction_rule_configs(rule_config_path)
        text_lines = kwargs.get("text_lines") if not args else args[1]

        extra_knowledge = kwargs.get('extra_knowledge', None)
        logger.info(f"Starts to use extra_knowledge: {extra_knowledge}")
        if extra_knowledge:
            background_infos.append(extra_knowledge)
        modified_outputs, modified_conflicts = self.extract(
            file_type=kwargs.get("file_type"),
            raw_text_lines=text_lines,
            target_key_raw=target_key_raw,
            key_definition_max_length=kwargs.get('key_definition_max_length',
                                                 10),
            text_line_max=kwargs.get('text_line_max', 60),
            method_description_dict=kwargs.get('method_description_dict',
                                               {}),
            background_infos=background_infos,
            explain_mode_on=kwargs.get('explain_mode_on', False)
        )
        return modified_outputs, modified_conflicts, self.content_slices, self.extraction_history


if __name__ == "__main__":
    pass
