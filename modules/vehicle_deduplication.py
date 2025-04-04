import json

from modules.utils.bx_utils import BXApis
from fuzzywuzzy import fuzz
import re
from loguru import logger


class VehicleDeduplicator:
    def __init__(self):
        self.bx_api = BXApis()
        self.current_vehicles = {}
        self.refresh_vehicle_list()

    @staticmethod
    def util_FuzzyMatch(name1, name2):
        # 正则表达式匹配一个或多个数字
        pattern = r'\d+'

        # 查找所有匹配的数字
        matches1 = re.findall(pattern, name1)
        matches2 = re.findall(pattern, name2)

        # 提取第一个匹配到的数字，如果没有找到则为None
        num1 = matches1[0] if matches1 else None
        num2 = matches2[0] if matches2 else None

        # 去除原始字符串中的数字
        clean_name1 = re.sub(pattern, '', name1).strip()
        clean_name2 = re.sub(pattern, '', name2).strip()

        # 如果两个字符串中都包含数字并且不同，返回False
        if num1 and num2 and num1 != num2:
            return False

        # 如果数字相同或没有数字，进行模糊匹配
        return fuzz.ratio(clean_name1, clean_name2) > 90

    @staticmethod
    def util_remove_symbols_and_spaces(name, ignore_space=False):
        # 使用正则表达式去掉所有非字母数字和中文字符
        cleaned_string = re.sub(r'[^\u4e00-\u9fffA-Za-z0-9]', '', name)
        cleaned_string = cleaned_string.upper()
        if not ignore_space:
            cleaned_string = ''.join(cleaned_string.split(' '))
        return cleaned_string

    @staticmethod
    def util_remove_common_prefixes(name):
        if not name:
            return name
        prefixes = ['MV ', 'MS ', 'SS ']
        for prefix in prefixes:
            if name.startswith(prefix):
                return name[len(prefix):]
        return name

    @staticmethod
    def util_InitialMatch(name1, name2):
        if ' ' in name1 and ' ' in name2:
            return ''.join([i[0] for i in name1.split(' ')]).upper() == ''.join(
                [i[0] for i in name2.split(' ')]).upper()
        elif ' ' in name1 and ' ' not in name2:
            return ''.join([i[0] for i in name1.split(' ')]).upper() == name2.upper()
        elif ' ' not in name1 and ' ' in name2:
            return name1.upper() == ''.join([i[0] for i in name2.split(' ') if i])

    @staticmethod
    def util_SlashValueMatch(name1, name2):
        if '/' in name2:
            return ''.join(name2.split('/')[-1].split(' ')).upper() == name1.upper()
        return False

    def step_PreprocessName(self, name):
        if not name:
            return name
        p_name = name
        p_name = self.util_remove_symbols_and_spaces(p_name)
        p_name = self.util_remove_common_prefixes(p_name)
        # logger.debug(f'{name}->{p_name}')

        # logger.debug(f'{name}->{p_name}')
        return p_name

    def refresh_vehicle_list(self):
        raw_res = self.bx_api.get_vessel_list()
        if raw_res.get('status') == 'error':
            raise Exception(f'Failed to refresh vessel_list. {raw_res["message"]}')
        else:
            vehicle_detail_list = raw_res.get('vessel_list', [])
            for vehicle_detail in vehicle_detail_list:
                vessel_id = vehicle_detail['VesselID']
                raw_name = vehicle_detail['VesselName']
                raw_namec = vehicle_detail['VesselNamec']
                self.current_vehicles[raw_name] = vessel_id
                processed_name = self.step_PreprocessName(raw_name)
                if processed_name != raw_name:
                    self.current_vehicles[processed_name] = vessel_id
                if raw_namec != raw_name:
                    self.current_vehicles[raw_namec] = vessel_id
                    processed_namec = self.step_PreprocessName(raw_namec)
                    if processed_namec != raw_namec:
                        self.current_vehicles[processed_namec] = vessel_id

    def method_ExactMatch(self, name):
        return self.current_vehicles.get(name)

    def method_FuzzyMatch(self, name):  # TODO
        return [self.current_vehicles[i] for i in self.current_vehicles.keys() if self.util_FuzzyMatch(name, i)]

    def method_InitialMatch(self, name):
        return [self.current_vehicles[i] for i in self.current_vehicles.keys() if self.util_InitialMatch(name, i)]

    def method_SlashValueMatch(self, name):
        return [self.current_vehicles[i] for i in self.current_vehicles.keys() if self.util_SlashValueMatch(name, i)]

    def check_existing_vehicle(self, name, **kwargs):
        for method in [self.method_ExactMatch,
                       self.method_SlashValueMatch,
                       self.method_FuzzyMatch,
                       self.method_InitialMatch]:
            if method != self.method_InitialMatch:
                vid = method(name=self.util_remove_symbols_and_spaces(name))
            else:
                vid = method(name=self.util_remove_symbols_and_spaces(name, ignore_space=True))
            if vid:
                if isinstance(vid, str):
                    vids = [vid]
                elif isinstance(vid, list):
                    vids = vid
                else:
                    vids = [vid]
                logger.info(f"Matched candidates by METHOD: {method.__name__}. {vids}")
                for vid in vids:
                    is_same = self.check_if_same(vid, **kwargs)
                    if is_same:
                        logger.success(f"Found exact previous vehicle. {vid}")
                        details = self.bx_api.get_vessel(vid)
                        logger.info(json.dumps(details, indent=2, ensure_ascii=False))
                        return vid

                logger.warning("Not exact vehicle.")
            logger.warning(f"Failed to match by METHOD: {method.__name__}")
        return None

    def check_if_same(self, vid, **kwargs):
        return True

    def main(self, name, **kwargs):
        vid = self.check_existing_vehicle(name, **kwargs)
        if vid:
            return vid
        logger.info("Will do refresh vehicle and check again.")
        self.refresh_vehicle_list()
        vid = self.check_existing_vehicle(name, **kwargs)
        if vid:
            return vid
        logger.error("Not existing Vehicle")
        return None


if __name__ == "__main__":
    ins = VehicleDeduplicator()
    res = ins.main('J 1')
    print(res)
