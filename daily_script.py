import time

import tqdm

from main import ShipmentFlow
from modules.utils.email_helper import EmailHelper
from pathlib import Path
from loguru import logger


class DailyFlow:
    def __init__(self, timeout=3*60*60):
        self.email_handler = EmailHelper(Path(__file__).parent / 'configs' / 'emails.yaml')
        self.flow_ins = ShipmentFlow(Path(__file__).parent / 'configs' / 'feishu_config.yaml')
        self.timeout = timeout
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
                                    source_name=f'Email_{name}')

    def main(self):
        start_ts = time.time()
        res = self.get_email_list()
        for name in res:
            if time.time() - start_ts >= self.timeout:
                logger.error("Exceed timeout. Quit")
                return
            logger.info(f"Still have {self.timeout- time.time()+start_ts} seconds.")
            self.register_tasks(name, res[name])


if __name__ == "__main__":
    ins = DailyFlow()
    ins.main()
