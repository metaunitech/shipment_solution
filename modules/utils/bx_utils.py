import requests
import time


class BXApis:
    def __init__(self):
        # 初始化 appid 和 secret
        self.appid = "bx48H864BV4Z2NX8X8"
        self.secret = "A9C0DA0868E94F9680444103FF98ACC8"
        self.token = None
        self.expire_time = None

    def __generate_token(self):
        """
        从指定的 API 获取 token。

        Returns:
            dict: 包含 token 的字典，如果请求失败，则返回一个包含错误信息的字典。
        """
        url = "http://47.106.198.93:8080/Api/token"
        querystring = {"appid": self.appid, "secret": self.secret}

        try:
            response = requests.get(url, params=querystring)
            response.raise_for_status()  # 如果响应状态码不是 200，将抛出 HTTPError 异常
            res = response.json()

            if 'errcode' in res and res['errcode'] == 200:
                if 'data' in res and 'access_token' in res['data']:
                    self.token = res['data']['access_token']
                    # 将 expires_in 转换为秒并减去5分钟，再加上当前时间
                    self.expire_time = time.time() + (res['data']['expires_in'] * 60 - 5 * 60)
                    return {'status': 'success', 'access_token': self.token, 'expires_in': res['data']['expires_in']}
                else:
                    return {'status': 'error', 'message': 'Access token not found in response'}
            else:
                return {'status': 'error', 'message': f"API returned an error: {res.get('errmsg', 'Unknown error')}"}
        except requests.exceptions.HTTPError as http_err:
            return {'status': 'error', 'message': f"HTTP error occurred: {http_err}"}
        except requests.exceptions.ConnectionError as conn_err:
            return {'status': 'error', 'message': f"Connection error occurred: {conn_err}"}
        except requests.exceptions.Timeout as timeout_err:
            return {'status': 'error', 'message': f"Timeout error occurred: {timeout_err}"}
        except requests.exceptions.RequestException as req_err:
            return {'status': 'error', 'message': f"An error occurred: {req_err}"}
        except ValueError as json_err:  # JSON 解析错误
            return {'status': 'error', 'message': f"JSON decode error: {json_err}"}

    def __ensure_token_valid(self):
        """
        确保 token 有效，如果无效则重新生成 token。
        """
        if not self.token or time.time() >= self.expire_time:
            token_result = self.__generate_token()
            if token_result['status'] != 'success':
                raise Exception(f"Failed to generate token: {token_result['message']}")

    def get_vessel_list(self):
        """
        获取船舶列表。

        Returns:
            dict: 包含船舶列表和描述信息的字典。成功时描述信息为 "success"，失败时为具体的错误详情。
        """
        self.__ensure_token_valid()

        url = "http://47.106.198.93:8080/api/api/Vessel/GetVesselList"
        headers = {"token": self.token}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # 如果响应状态码不是 200，将抛出 HTTPError 异常
            res = response.json()
            if 'data' in res and isinstance(res['data'], list):
                return {'status': 'success', 'vessel_list': res['data']}
            else:
                return {'status': 'error', 'message': 'Invalid response format'}
        except requests.exceptions.HTTPError as http_err:
            return {'status': 'error', 'message': f"HTTP error occurred: {http_err}"}
        except requests.exceptions.ConnectionError as conn_err:
            return {'status': 'error', 'message': f"Connection error occurred: {conn_err}"}
        except requests.exceptions.Timeout as timeout_err:
            return {'status': 'error', 'message': f"Timeout error occurred: {timeout_err}"}
        except requests.exceptions.RequestException as req_err:
            return {'status': 'error', 'message': f"An error occurred: {req_err}"}
        except ValueError as json_err:  # JSON 解析错误
            return {'status': 'error', 'message': f"JSON decode error: {json_err}"}

    def add_vessel(self, payload):
        """
        添加新的船舶信息。

        Args:
            payload (dict): 包含船舶信息的字典。

        Returns:
            dict: 包含操作结果和描述信息的字典。成功时描述信息为 "success"，失败时为具体的错误详情。
        """
        self.__ensure_token_valid()

        url = "http://47.106.198.93:8080/api/api/Vessel/AddVessel"
        headers = {
            "token": self.token,
            "content-type": "application/json"
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()  # 如果响应状态码不是 200，将抛出 HTTPError 异常
            res = response.json()
            if 'errcode' in res and res['errcode'] == 200:
                return {'status': 'success', 'message': 'Vessel added successfully'}
            else:
                return {'status': 'error', 'message': f"API returned an error: {res.get('errmsg', 'Unknown error')}"}
        except requests.exceptions.HTTPError as http_err:
            return {'status': 'error', 'message': f"HTTP error occurred: {http_err}"}
        except requests.exceptions.ConnectionError as conn_err:
            return {'status': 'error', 'message': f"Connection error occurred: {conn_err}"}
        except requests.exceptions.Timeout as timeout_err:
            return {'status': 'error', 'message': f"Timeout error occurred: {timeout_err}"}
        except requests.exceptions.RequestException as req_err:
            return {'status': 'error', 'message': f"An error occurred: {req_err}"}
        except ValueError as json_err:  # JSON 解析错误
            return {'status': 'error', 'message': f"JSON decode error: {json_err}"}

    def add_vessel_voy_dt(self, payload):
        """
        添加船舶航次信息。

        Args:
            payload (dict): 包含船舶航次信息的字典。

        Returns:
            dict: 包含操作结果和描述信息的字典。成功时描述信息为 "success"，失败时为具体的错误详情。
        """
        self.__ensure_token_valid()

        url = "http://47.106.198.93:8080/api/api/Vessel/AddVesselVoyDT"
        headers = {
            "token": self.token,
            "content-type": "application/json"
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()  # 如果响应状态码不是 200，将抛出 HTTPError 异常
            res = response.json()
            if 'errcode' in res and res['errcode'] == 200:
                return {'status': 'success', 'message': 'Vessel voyage information added successfully'}
            else:
                return {'status': 'error', 'message': f"API returned an error: {res.get('errmsg', 'Unknown error')}"}
        except requests.exceptions.HTTPError as http_err:
            return {'status': 'error', 'message': f"HTTP error occurred: {http_err}"}
        except requests.exceptions.ConnectionError as conn_err:
            return {'status': 'error', 'message': f"Connection error occurred: {conn_err}"}
        except requests.exceptions.Timeout as timeout_err:
            return {'status': 'error', 'message': f"Timeout error occurred: {timeout_err}"}
        except requests.exceptions.RequestException as req_err:
            return {'status': 'error', 'message': f"An error occurred: {req_err}"}
        except ValueError as json_err:  # JSON 解析错误
            return {'status': 'error', 'message': f"JSON decode error: {json_err}"}

    def get_sa_job_list(self):
        """
        获取货盘列表。

        Returns:
            dict: 包含作业单列表和描述信息的字典。成功时描述信息为 "success"，失败时为具体的错误详情。
        """
        self.__ensure_token_valid()

        url = "http://47.106.198.93:8080/api/api/SaJob/GetSaJobList"
        headers = {"token": self.token}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # 如果响应状态码不是 200，将抛出 HTTPError 异常
            res = response.json()
            if 'data' in res and isinstance(res['data'], list):
                return {'status': 'success', 'job_list': res['data']}
            else:
                return {'status': 'error', 'message': 'Invalid response format'}
        except requests.exceptions.HTTPError as http_err:
            return {'status': 'error', 'message': f"HTTP error occurred: {http_err}"}
        except requests.exceptions.ConnectionError as conn_err:
            return {'status': 'error', 'message': f"Connection error occurred: {conn_err}"}
        except requests.exceptions.Timeout as timeout_err:
            return {'status': 'error', 'message': f"Timeout error occurred: {timeout_err}"}
        except requests.exceptions.RequestException as req_err:
            return {'status': 'error', 'message': f"An error occurred: {req_err}"}
        except ValueError as json_err:  # JSON 解析错误
            return {'status': 'error', 'message': f"JSON decode error: {json_err}"}

    def get_sa_job(self, job_id):
        """
        获取单个货盘信息。

        Args:
            job_id (str): 作业单 ID。

        Returns:
            dict: 包含作业单信息和描述信息的字典。成功时描述信息为 "success"，失败时为具体的错误详情。
        """
        self.__ensure_token_valid()

        url = "http://47.106.198.93:8080/api/api/SaJob/GetSaJob"
        headers = {"token": self.token}
        params = {"id": job_id}

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()  # 如果响应状态码不是 200，将抛出 HTTPError 异常
            res = response.json()
            if 'data' in res and isinstance(res['data'], dict):
                return {'status': 'success', 'job_info': res['data']}
            else:
                return {'status': 'error', 'message': 'Invalid response format'}
        except requests.exceptions.HTTPError as http_err:
            return {'status': 'error', 'message': f"HTTP error occurred: {http_err}"}
        except requests.exceptions.ConnectionError as conn_err:
            return {'status': 'error', 'message': f"Connection error occurred: {conn_err}"}
        except requests.exceptions.Timeout as timeout_err:
            return {'status': 'error', 'message': f"Timeout error occurred: {timeout_err}"}
        except requests.exceptions.RequestException as req_err:
            return {'status': 'error', 'message': f"An error occurred: {req_err}"}
        except ValueError as json_err:  # JSON 解析错误
            return {'status': 'error', 'message': f"JSON decode error: {json_err}"}

    def add_sa_job(self, payload):
        """
        添加单个货盘信息。

        Args:
            payload (dict): 包含作业单信息的字典。

        Returns:
            dict: 包含操作结果和描述信息的字典。成功时描述信息为 "success"，失败时为具体的错误详情。
        """
        self.__ensure_token_valid()

        url = "http://47.106.198.93:8080/api/api/SaJob/AddSaJob"
        headers = {
            "token": self.token,
            "content-type": "application/json"
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()  # 如果响应状态码不是 200，将抛出 HTTPError 异常
            res = response.json()
            if 'errcode' in res and res['errcode'] == 200:
                return {'status': 'success', 'message': 'Job added successfully'}
            else:
                return {'status': 'error', 'message': f"API returned an error: {res.get('errmsg', 'Unknown error')}"}
        except requests.exceptions.HTTPError as http_err:
            return {'status': 'error', 'message': f"HTTP error occurred: {http_err}"}
        except requests.exceptions.ConnectionError as conn_err:
            return {'status': 'error', 'message': f"Connection error occurred: {conn_err}"}
        except requests.exceptions.Timeout as timeout_err:
            return {'status': 'error', 'message': f"Timeout error occurred: {timeout_err}"}
        except requests.exceptions.RequestException as req_err:
            return {'status': 'error', 'message': f"An error occurred: {req_err}"}
        except ValueError as json_err:  # JSON 解析错误
            return {'status': 'error', 'message': f"JSON decode error: {json_err}"}


# 示例使用
if __name__ == "__main__":
    bx_apis = BXApis()

    # 示例船舶信息
    vessel_payload = {
        "VesselCode": "lzb1117a",
        "VesselName": "ZIM PANAMA",
        "VesselNamec": "以斯塔巴拿马",
        "IMOCode": "9231781",
        "VslType": None,
        "VslCreateYear": None,
        "CarryTonSJ": None,
        "CarryTon": None,
        "Tons": None,
        "NetTon": None,
        "HoldCapacity2": 0,
        "GoodsVolumeSZ": None,
        "DSKX": None,
        "Length": 10,
        "Width": 20,
        "XDeep": None,
        "Step": None,
        "HoldSize": None,
        "CabinCount": None,
        "Crane": None,
        "Grab": None,
        "FFill": None,
        "DeckCount": None,
        "PAndI": None,
        "Carrier": "MSK",
        "Remark": None
    }

    # 示例船舶航次信息
    vessel_voy_dt_payload = {
        "VesselCode": "491AC21B60EE489DAB80D1C19DFAB5EE",
        "PortNameE": "xiamen",
        "DTDate": "2024-11-17"
    }

    # 示例作业单信息
    sa_job_payload = {
        "GoodsName": "basketball",
        "Package": "bag",
        "PortLoading": "HORTA",
        "PortDischarge": None,
        "BeginDate": None,
        "EndDate": None,
        "YJBL": None,
        "BPCompany": None,
        "WeightHT2": None,
        "ZL": None,
        "XL": None,
        "CarrierPrice": None,
        "ZJPrice": None
    }

    # 示例作业单 ID
    job_id = "3DDEEDB9E2924406A5343AF5FDC8839B"

    # 调用方法并打印结果
    add_vessel_result = bx_apis.add_vessel(vessel_payload)
    print(add_vessel_result)

    # add_vessel_voy_dt_result = bx_apis.add_vessel_voy_dt(vessel_voy_dt_payload)
    # print(add_vessel_voy_dt_result)
    #
    # get_sa_job_list_result = bx_apis.get_sa_job_list()
    # print(get_sa_job_list_result)
    #
    # get_sa_job_result = bx_apis.get_sa_job(job_id)
    # print(get_sa_job_result)
    #
    # add_sa_job_result = bx_apis.add_sa_job(sa_job_payload)
    # print(add_sa_job_result)