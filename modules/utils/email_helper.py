import datetime
import json
import zmail
from loguru import logger
import yaml
# from nltk.twitter.twitter_demo import yesterday
import os

# 邮箱配置列表
email_configs = {
    'default': {
        "server": "smtp.qiye.163.com",
        "user": "CHARTERING@JAH-LINE.COM",
        "password": "BUb4R2u2Z7ac15wN"
    }
}


class EmailHelper:
    def __init__(self, config_path):
        with open(config_path, 'r') as f:
            configs = yaml.load(f, Loader=yaml.FullLoader)
        self.all_emails = configs.get('emails', {})
        self.cache_storage = configs.get('cache_path')

    def check_if_parsed(self, email_id, name='default'):
        today = datetime.date.today()
        for days_ago in range(30):  # 限制检查天数范围，防止过多循环
            date = today - datetime.timedelta(days=days_ago)
            log_file = os.path.join(self.cache_storage, f"{date}.json")
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    log_data = json.load(f)
                if name in log_data and email_id in log_data[name]:
                    return log_data[name][email_id]['status']
        return False

    def get_yesterday_start_id(self, name='default'):
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        log_file = os.path.join(self.cache_storage, f"{yesterday}.json")

        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                log_data = json.load(f)
            if name in log_data:
                valid_ids = [int(email_id) for email_id, details in log_data[name].items() if details['status']]
                return max(valid_ids, default=None)
        return None

    def update_today_finished(self, email_id, parse_status, name='default'):
        today = datetime.date.today()
        log_file = os.path.join(self.cache_storage, f"{today}.json")

        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                log_data = json.load(f)
        else:
            log_data = {}

        if name not in log_data:
            log_data[name] = {}

        log_data[name][email_id] = {
            'status': parse_status,
            'ts': datetime.datetime.now().timestamp()
        }

        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=4)

    def fetch_today_latest_email(self, name):
        server = self.all_emails[name]["server"]
        user = self.all_emails[name]["user"]
        password = self.all_emails[name]["password"]

        # 创建邮件服务对象
        mail_server = zmail.server(user, password, smtp_host=server, smtp_port=25)
        latest_email = mail_server.get_latest()
        return latest_email['id']

    def get_today_task_list(self, name):
        yesterday_start_id = self.get_yesterday_start_id(name)
        today_latest_id = self.fetch_today_latest_email(name)

        # 假设 fetch_today_latest_email 提供了完整邮件 ID 列表功能，
        # 这里可以增加从昨天最大 ID 到今天最新 ID 的逻辑
        task_list = []
        if yesterday_start_id is not None and today_latest_id is not None:
            task_list = list(range(yesterday_start_id + 1, today_latest_id + 1))
        return task_list


# def fetch_new_emails(config, target_date=None):
#     if target_date is None:
#         target_date = datetime.now().date()
#     else:
#         target_date = target_date.date()
#
#     # 设置开始时间和结束时间，确保只获取目标日期的邮件
#     start_time = datetime.combine(target_date, datetime.min.time())
#     end_time = start_time + timedelta(days=1)
#
#     server = config["server"]
#     user = config["user"]
#     password = config["password"]
#
#     # 创建邮件服务对象
#     mail_server = zmail.server(user, password, smtp_host=server, smtp_port=25)
#
#     # 获取目标日期的所有邮件
#     mails = mail_server.get_mails(start_time=start_time, end_time=end_time)
#
#     return mails
#
#
# def main():
#     for config in email_configs:
#         emails = fetch_new_emails(config)
#         logger.info(f"We fetched {len(emails)} mails. \nFirst {emails[0]}. \nLast: {emails[-1]}")


if __name__ == "__main__":
    ins = EmailHelper(config_path=r"W:\Personal_Project\NeiRelated\projects\shipment_solution\configs\emails.yaml")
    res = ins.get_today_task_list('default')
    print("HERE")