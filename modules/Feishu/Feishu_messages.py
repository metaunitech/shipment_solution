# encoding=utf-8
import json
import os
import time
from pathlib import Path
import yaml
import requests
from requests_toolbelt import MultipartEncoder
from loguru import logger
from typing import Union, Dict, List, Tuple

try:
    from .Feishu_base import FeishuApp
except:
    from Feishu_base import FeishuApp
import lark_oapi as lark
from lark_oapi.api.im.v1 import *


class FeishuMessageHandler(FeishuApp):
    def __init__(self, config_yaml_path, global_token_type=lark.AccessTokenType.TENANT, chat_id=None):
        super().__init__(config_yaml_path)
        self.__global_token_type = global_token_type
        self.chat_id = chat_id
        with open(config_yaml_path, 'r') as f:
            configs = yaml.load(f, Loader=yaml.FullLoader)
        self.__app_id = configs.get('app_id')
        self.__app_secret = configs.get('app_secret')

    def send_message_by_template(self, receive_id, template_id, template_variable: dict, receive_id_type='chat_id'):
        content = {'type': 'template', 'data': {'template_id': template_id, 'template_variable': template_variable}}
        # 创建client
        client = lark.Client.builder() \
            .app_id(self.__app_id) \
            .app_secret(self.__app_secret) \
            .log_level(lark.LogLevel.DEBUG) \
            .build()

        # 构造请求对象
        request: CreateMessageRequest = CreateMessageRequest.builder() \
            .receive_id_type(receive_id_type) \
            .request_body(CreateMessageRequestBody.builder()
                          .receive_id(receive_id)
                          .msg_type("interactive")
                          .content(json.dumps(content, ensure_ascii=False))
                          .build()) \
            .build()

        # 发起请求
        response: CreateMessageResponse = client.im.v1.message.create(request)

        # 处理失败返回
        if not response.success():
            lark.logger.error(
                f"client.im.v1.message.create failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}")
            return

        # 处理业务结果
        lark.logger.info(lark.JSON.marshal(response.data, indent=4))
        return response.data.message_id

    def send_message_by_text(self, receive_id, text, receive_id_type='chat_id'):
        client = lark.Client.builder() \
            .app_id(self.__app_id) \
            .app_secret(self.__app_secret) \
            .log_level(lark.LogLevel.DEBUG) \
            .build()

        # 构造请求对象
        request: CreateMessageRequest = CreateMessageRequest.builder() \
            .receive_id_type(receive_id_type) \
            .request_body(CreateMessageRequestBody.builder()
                          .receive_id(receive_id)
                          .msg_type("text")
                          .content(json.dumps({'text': text}, ensure_ascii=False))
                          .build()) \
            .build()

        # 发起请求
        response: CreateMessageResponse = client.im.v1.message.create(request)

        # 处理失败返回
        if not response.success():
            lark.logger.error(
                f"client.im.v1.message.create failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}")
            return

        # 处理业务结果
        lark.logger.info(lark.JSON.marshal(response.data, indent=4))
        return response.data.message_id

    def reply_message_by_template(self, message_id, template_id, template_variable: dict, in_thread=False):
        content = {'type': 'template', 'data': {'template_id': template_id, 'template_variable': template_variable}}

        # 创建client
        client = lark.Client.builder() \
            .app_id(self.__app_id) \
            .app_secret(self.__app_secret) \
            .log_level(lark.LogLevel.DEBUG) \
            .build()

        # 构造请求对象
        request: ReplyMessageRequest = ReplyMessageRequest.builder() \
            .message_id(message_id) \
            .request_body(ReplyMessageRequestBody.builder()
                          .msg_type("interactive")
                          .content(json.dumps(content, ensure_ascii=False))
                          .reply_in_thread(in_thread)
                          .build()) \
            .build()

        # 发起请求
        response: ReplyMessageResponse = client.im.v1.message.reply(request)

        # 处理失败返回
        if not response.success():
            lark.logger.error(
                f"client.im.v1.message.reply failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}")
            return

        # 处理业务结果
        lark.logger.info(lark.JSON.marshal(response.data, indent=4))
        return response.data.message_id

    def retrieve_file(self, message_id, file_key, store_path: Path, file_type='file'):
        # 创建client
        client = lark.Client.builder() \
            .app_id(self.__app_id) \
            .app_secret(self.__app_secret) \
            .log_level(lark.LogLevel.DEBUG) \
            .build()

        # 构造请求对象
        request: GetMessageResourceRequest = GetMessageResourceRequest.builder() \
            .message_id(message_id) \
            .file_key(file_key) \
            .type(file_type) \
            .build()

        # 发起请求
        response: GetMessageResourceResponse = client.im.v1.message_resource.get(request)

        # 处理失败返回
        if not response.success():
            lark.logger.error(
                f"client.im.v1.message_resource.get failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}")

            # 处理业务结果
        f = open(str(store_path), "wb")
        f.write(response.file.read())
        f.close()



