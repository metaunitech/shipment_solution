from main import ShipmentFlow
from modules.utils.email_helper import EmailHelper
from pathlib import Path


class DailyFlow:
    def __init__(self):
        self.email_handler = EmailHelper(Path(__file__).parent/'configs'/'emails.yaml')
        self.flow_ins = ShipmentFlow(Path(__file__).parent/'configs'/'feishu_config.yaml')

    def get_email_list(self):
        pass

    def get_daily_input(self):
        pass

    def main(self):
        pass
