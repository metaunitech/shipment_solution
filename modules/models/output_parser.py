# encoding=utf-8
from langchain.output_parsers import PydanticOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List, Union


class KeyValuePair(BaseModel):
    key: str = Field(
        description='关键信息提取结果中关键信息的键值名(key information key name)',
    )
    value: Union[None, str] = Field(
        description='关键信息提取结果中关键信息的提取结果(key information value)'
    )
    quote: Union[None, str] = Field(
        description='原文中包含该关键信息的句子'
    )


class KeyValuePairDict(BaseModel):
    key_value_pairs: dict = Field(
        description='关键信息提取结果中所有关键信息的键值对,key是关键信息字段，value是对应的值。注意，如果原文中无法提取到的字段请删除。仅保留能提取出结果的键值对。'
    )


class KeyValuePairList(BaseModel):
    NodeList: List[KeyValuePair] = Field(
        description='关键信息提取结果列表。列表中的元素是所提供的原文中所有关键信息的键值对字典。每个键值对只能包含一组key value quote。'
    )


class KeyInfoSource(BaseModel):
    keyword: str = Field(
        description='目标字段'
    )
    extracted_info: str = Field(
        description='我们需要溯源的给定的从原文中提取出的目标字段的结果'
    )
    is_correct: bool = Field(
        description='是否能从原文中推断出该关键信息'
    )
    reason: str = Field(
        description="为什么能从上述的source_text中得出该目标字段结果。"
    )
    source_text: List[str] = Field(
        description='如果可以从原文中得出该关键信息，返回原文中包含我们目标字段信息的句子的列表。列表的元素是原文中的原句（仅包含原句）。如果目标字段不是从该原文中提取出来返回空列表。'
    )



if __name__ == "__main__":
    parser = PydanticOutputParser(pydantic_object=KeyInfoSource)
    print(parser.get_format_instructions())
