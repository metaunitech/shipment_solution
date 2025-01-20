from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
import yaml
import json
from pathlib import Path
from loguru import logger
import concurrent.futures

MODEL_NAME = 'Zhipu_glm4_flash'

class MessageTranslator:
    def __init__(self):
        self.__prompt_base_dir = Path(__file__).parent / 'prompts'
        self.__example_base_dir = Path(__file__).parent / 'knowledges'

    def create_llm_instance(self, model_name=MODEL_NAME):
        with open(Path(__file__).parent.parent / 'configs' / 'backend_configs.yaml', 'r') as f:
            config = yaml.safe_load(f)
        return ChatOpenAI(temperature=0.95,
                          model=config['LLM'][model_name]['llm_params']['model_name'],
                          openai_api_key=config['LLM'][model_name]['llm_params']['api_key'],
                          openai_api_base=config['LLM'][model_name]['llm_params']['endpoint'])

    def translate(self, content):
        logger.info("Starts to translate this content using Knowledges.")
