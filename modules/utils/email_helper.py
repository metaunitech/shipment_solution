import zmail

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


def fetch_new_emails(config):
    server = config["server"]
    user = config["user"]
    password = config["password"]

    # 创建邮件服务对象
    server = zmail.server(user, password, smtp_host=server, smtp_port=25)

    # 获取最新邮件
    mails = server.get_latest()

    if not mails:
        print("No new emails found.")
        return

    for mail_id, mail in mails.items():
        # 获取邮件主题和发件人
        subject = mail['subject']
        from_ = mail['from']

        # 打印邮件信息
        print(f"From: {from_}")
        print(f"Subject: {subject}")
        print("-" * 40)


# 主函数
def main():
    for config in email_configs:
        print(f"Checking new emails for {config['user']}...")
        fetch_new_emails(config)
        print("-" * 40)


if __name__ == "__main__":
    main()