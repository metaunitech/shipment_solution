import tqdm

from main import ShipmentFlow
from modules.utils.email_helper import EmailHelper
from pathlib import Path
from loguru import logger


class DailyFlow:
    def __init__(self):
        self.email_handler = EmailHelper(Path(__file__).parent / 'configs' / 'emails.yaml')
        self.flow_ins = ShipmentFlow(Path(__file__).parent / 'configs' / 'feishu_config.yaml')

    def get_email_list(self):
        res = {}
        for name in self.email_handler.all_emails.keys():
            todo_list = self.email_handler.get_today_task_list(name)
            res[name] = todo_list
        return res

    def register_tasks(self, name, email_id_list):
        for email_id in tqdm.tqdm(email_id_list[::-1]):
            logger.info(f"Working on email {name} {email_id}")
            subject, m_content, sender, date = self.email_handler.get_email_detail(name, email_id)
            if subject is None:
                continue
            content = f"标题：{subject}\n FROM: {sender}\n RECEIVE_DATE: {date}\n CONTENT: {m_content}"
            logger.info(f"Content: {content}")
            self.flow_ins.unit_flow(content=content,
                                    receive_id=email_id,
                                    receive_type=f'Email_{name}')

    def main(self):
        res = self.get_email_list()
        for name in res:
            self.register_tasks(name, res[name])


if __name__ == "__main__":
    ins = DailyFlow()
    ins.main()
