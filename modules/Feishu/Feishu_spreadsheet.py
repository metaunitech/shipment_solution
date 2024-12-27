from modules.Feishu.Feishu_base import FeishuApp
import lark_oapi as lark
from lark_oapi.api.bitable.v1 import *
import yaml
import json
from loguru import logger
from typing import Tuple


class FeishuSpreadsheetHandler(FeishuApp):
    def __init__(self, config_yaml_path, global_token_type=lark.AccessTokenType.TENANT):
        super().__init__(config_yaml_path)
        self.__global_token_type = global_token_type
        with open(config_yaml_path, 'r') as f:
            configs = yaml.load(f, Loader=yaml.FullLoader)
        self.__app_id = configs.get('app_id')
        self.__app_secret = configs.get('app_secret')

    def get_table_fields(self, app_token, table_id, **kwargs):
        # uri = '/open.feishu.cn/open-apis/bitable/v1/apps/:app_token/tables/:table_id/fields'
        # queries_params = {}
        # for query_param_name in ['view_id', 'text_field_as_array', 'page_token', 'page_size']:
        #     if query_param_name in kwargs:
        #         queries_params[query_param_name] = kwargs[query_param_name]
        # queries_params = None if not queries_params else queries_params
        client = lark.Client.builder() \
            .app_id(self.__app_id) \
            .app_secret(self.__app_secret) \
            .log_level(lark.LogLevel.DEBUG) \
            .build()

        # 构造请求对象
        request: ListAppTableFieldRequest = ListAppTableFieldRequest.builder() \
            .app_token(app_token) \
            .table_id(table_id) \
            .view_id(kwargs.get('view_id')) \
            .page_size(kwargs.get('page_size', 50)) \
            .build()

        # 发起请求
        option = lark.RequestOption.builder().user_access_token(self.get_tenant_access_token()).build()
        response: ListAppTableFieldResponse = client.bitable.v1.app_table_field.list(request, option)

        # 处理失败返回
        if not response.success():
            lark.logger.error(
                f"client.bitable.v1.app_table_field.list failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}")
            return []

        # 处理业务结果
        lark.logger.info(lark.JSON.marshal(response.data, indent=4))

        return [i.__dict__ for i in response.data.items]

    def add_records(self, app_token, table_id, records):
        # 创建client
        client = lark.Client.builder() \
            .app_id(self.__app_id) \
            .app_secret(self.__app_secret) \
            .log_level(lark.LogLevel.DEBUG) \
            .build()

        # records_inserted = {'records': [{'fields': i} for i in records]}

        # 构造请求对象
        request: BatchCreateAppTableRecordRequest = BatchCreateAppTableRecordRequest.builder() \
            .app_token(app_token) \
            .table_id(table_id) \
            .request_body(BatchCreateAppTableRecordRequestBody.builder()
                          .records([AppTableRecord.builder()
                                   .fields(i)
                                   .build()
                                    for i in records])
                          .build()) \
            .build()

        # 发起请求
        response: BatchCreateAppTableRecordResponse = client.bitable.v1.app_table_record.batch_create(request)

        # 处理失败返回
        if not response.success():
            lark.logger.error(
                f"client.bitable.v1.app_table_record.batch_create failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}")
            return

        # 处理业务结果
        lark.logger.info(lark.JSON.marshal(response.data, indent=4))
        return [i['record_id'] for i in json.loads(lark.JSON.marshal(response.data, indent=4)).get('records')]

    def unit_get_records(self, app_token, table_id, view_id, page_token=None, page_size=20, show_fields=None, **kwargs):
        client = lark.Client.builder() \
            .app_id(self.__app_id) \
            .app_secret(self.__app_secret) \
            .log_level(lark.LogLevel.DEBUG) \
            .build()
        if not page_token:
            # 构造请求对象
            request: SearchAppTableRecordRequest = SearchAppTableRecordRequest.builder() \
                .page_size(page_size) \
                .app_token(app_token) \
                .table_id(table_id) \
                .request_body(SearchAppTableRecordRequestBody.builder()
                              .view_id(view_id)
                              .field_names(list(kwargs.keys()) + show_fields if show_fields else list(kwargs.keys()))
                              .filter(FilterInfo.builder()
                                      .conjunction("and")
                                      .conditions([Condition.builder()
                                                  .field_name(i)
                                                  .operator("is")
                                                  .value([kwargs[i]])
                                                  .build() for i in kwargs.keys()])
                                      .build()) \
                              .automatic_fields(False)
                              .build()) \
                .build()
        else:
            # 构造请求对象
            request: SearchAppTableRecordRequest = SearchAppTableRecordRequest.builder() \
                .page_size(page_size) \
                .app_token(app_token) \
                .table_id(table_id) \
                .page_token(page_token) \
                .request_body(SearchAppTableRecordRequestBody.builder() \
                              .view_id(view_id)
                              .field_names(list(kwargs.keys()))
                              .filter(FilterInfo.builder()
                                      .conjunction("and")
                                      .conditions([Condition.builder()
                                                  .field_name(i)
                                                  .operator("is")
                                                  .value([kwargs[i]])
                                                  .build() for i in kwargs.keys()])
                                      .build()) \
                              .automatic_fields(False)
                              .build()) \
                .build()
        response: SearchAppTableRecordResponse = client.bitable.v1.app_table_record.search(request)

        # 处理失败返回
        if not response.success():
            lark.logger.error(
                f"client.bitable.v1.app_table_record.search failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}")
            return None

        # 处理业务结果
        lark.logger.info(lark.JSON.marshal(response.data, indent=4))
        return json.loads(lark.JSON.marshal(response.data))

    def get_records(self, app_token, table_id, view_id, show_fields=None, **kwargs):
        final_res = []
        error_page_token = []
        page_token = None
        total = -1
        while 1:
            res = self.unit_get_records(app_token, table_id, view_id, page_token=page_token, show_fields=show_fields,
                                        **kwargs)
            items = res.get("items", [])
            final_res.extend(items)
            total = res.get('total', total)
            if not items and len(final_res) != total:
                logger.error(
                    f'Current length: {len(final_res)}. We have total: {total}. Current page_token: {page_token} has None res. Page token error.')
                error_page_token.append(page_token)
            has_more = res.get('has_more', False)
            page_token = res.get('page_token', None)
            if has_more is False:
                return final_res, error_page_token

    def update_records(self, app_token, table_id, record_id, records):
        # 创建client
        client = lark.Client.builder() \
            .app_id(self.__app_id) \
            .app_secret(self.__app_secret) \
            .log_level(lark.LogLevel.DEBUG) \
            .build()

        # 构造请求对象
        request: UpdateAppTableRecordRequest = UpdateAppTableRecordRequest.builder() \
            .app_token(app_token) \
            .table_id(table_id) \
            .record_id(record_id) \
            .request_body(AppTableRecord.builder()
                          .fields(records)
                          .build()) \
            .build()

        # 发起请求
        response: UpdateAppTableRecordResponse = client.bitable.v1.app_table_record.update(request)

        # 处理失败返回
        if not response.success():
            lark.logger.error(
                f"client.bitable.v1.app_table_record.update failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}")
            return

        # 处理业务结果
        lark.logger.info(lark.JSON.marshal(response.data, indent=4))

    def batch_get_records(self, app_token, table_id, record_ids):
        client = lark.Client.builder() \
            .app_id(self.__app_id) \
            .app_secret(self.__app_secret) \
            .log_level(lark.LogLevel.DEBUG) \
            .build()
        request: BatchGetAppTableRecordRequest = BatchGetAppTableRecordRequest.builder() \
            .app_token(app_token) \
            .table_id(table_id) \
            .request_body(BatchGetAppTableRecordRequestBody.builder()
                          .record_ids(record_ids)
                          .user_id_type("open_id")
                          .with_shared_url(True)
                          .automatic_fields(True)
                          .build()) \
            .build()

        # 发起请求
        response: BatchGetAppTableRecordResponse = client.bitable.v1.app_table_record.batch_get(request)

        # 处理失败返回
        if not response.success():
            lark.logger.error(
                f"client.bitable.v1.app_table_record.batch_get failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}")
            return

        # 处理业务结果
        lark.logger.info(lark.JSON.marshal(response.data, indent=4))
        return json.loads(lark.JSON.marshal(response.data, indent=4))


if __name__ == "__main__":
    ins = FeishuSpreadsheetHandler(
        r'W:\Personal_Project\NeiRelated\projects\shipment_solution\configs\feishu_config.yaml',
        lark.AccessTokenType.TENANT)
    # res = ins.get_table_fields(app_token='B7XnbQTtLapDfDsJj27c7ZgQnLd',
    #                            table_id='tblSsCLLIEXguHpk',
    #                            view_id='vewFnBR0nY')
    ins.update_records(app_token='O2Q6bNHULa3HxusXxCNc9J9KnHg', table_id='tblowlKy1UIzilNU',
                       record_id='recuxFLRLuT1Rc', records={
            'id': 'demo',
            '消息主体': 'dd',
            '数据源': 'dd',
            '状态': '成功',
        })
