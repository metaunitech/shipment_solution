from datetime import datetime, timedelta
import zmail
from loguru import logger
import yaml
from nltk.twitter.twitter_demo import yesterday

# 邮箱配置列表
email_configs = [
    # {
    #     "server": "smtp.gmail.com",
    #     "user": "your_username1@gmail.com",
    #     "password": "your_password1"
    # },
    {
        "server": "smtp.qiye.163.com",
        "user": "CHARTERING@JAH-LINE.COM",
        "password": "BUb4R2u2Z7ac15wN"
    }
]

class EmailHelper:
    def __init__(self, config_path):
        with open(config_path, 'r') as f:
            configs = yaml.load(f, Loader=yaml.FullLoader)
        self.all_emails = configs.get('emails', {})
        self.cache_storage = configs.get('cache_path')

    def check_if_parsed(self, email_id, name='default'):
        # 从最新日期往前依次打开cache_storage里以日期为名字的json文件，
        # 判断name和对应email_id是否在文件中出现，且status == True
        # 如果没出现，继续打开其他文件
        # 如果出现了，返回最新一次的status
        # 如果打开了所有文件都没出现，返回False
        #
        pass

    def get_yesterday_start_id(self, name='default'):
        # 从最新日期往前依次打开cache_storage里以日期为名字的json文件，
        # 返回最新日期前一天的最大的且status为True的email_id
        # 如果没有之前的日志，返回None
        pass

    def update_today_finished(self, email_id, parse_status, name='default'):
        # 打开cache_storage里的以今天日期为名字的json文件
        # name为Key,{<email_id>: {status: <parse_status>, ts: <update_datetime_timestamp>}}为value
        pass

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






def fetch_new_emails(config, target_date=None):
    if target_date is None:
        target_date = datetime.now().date()
    else:
        target_date = target_date.date()

    # 设置开始时间和结束时间，确保只获取目标日期的邮件
    start_time = datetime.combine(target_date, datetime.min.time())
    end_time = start_time + timedelta(days=1)

    server = config["server"]
    user = config["user"]
    password = config["password"]

    # 创建邮件服务对象
    mail_server = zmail.server(user, password, smtp_host=server, smtp_port=25)

    # 获取目标日期的所有邮件
    mails = mail_server.get_mails(start_time=start_time, end_time=end_time)

    return mails

def main():
    for config in email_configs:
        emails = fetch_new_emails(config)
        logger.info(f"We fetched {len(emails)} mails. \nFirst {emails[0]}. \nLast: {emails[-1]}")


if __name__ == "__main__":
    main()