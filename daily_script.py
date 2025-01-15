import hashlib
import json
import time
import traceback

import tqdm

from main import ShipmentFlow
from datetime import datetime, timedelta, timezone

from modules.utils.email_helper import EmailHelper
from pathlib import Path
from loguru import logger

import os

# 确保 logs 文件夹存在
log_dir = Path(__file__).parent / 'logs'
os.makedirs(log_dir, exist_ok=True)

# 设置 loguru 日志处理器
logger.remove()  # 移除默认的处理器，防止重复打印
start_time_str = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
log_file_name = f"{start_time_str}.log"
log_file_path = f"{log_dir}/{log_file_name}"

logger.add(
    f"{log_file_path}",  # 日志文件路径和名称，使用运行开始时间命名
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",  # 日志格式
    rotation="00:00",  # 每天午夜轮换日志文件
    compression="zip",  # 压缩旧的日志文件
    level="DEBUG"  # 设置最低日志级别
)
logger.add(
    sink=lambda msg: tqdm.tqdm.write(msg, end=''),  # 控制台输出，与 tqdm 兼容
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    colorize=True,  # 控制台输出时使用颜色
    level="DEBUG"
)
class DailyFlow:
    def __init__(self, timeout=3 * 60 * 60):
        self.email_handler = EmailHelper(Path(__file__).parent / 'configs' / 'emails.yaml')
        self.flow_ins = ShipmentFlow(Path(__file__).parent / 'configs' / 'feishu_config.yaml')
        self.timeout = timeout

    @staticmethod
    def generate_md5_hash(input_data):
        """
        根据文本内容或文件路径生成唯一的 MD5 哈希字符串。

        参数:
        - input_data (str or Path): 输入的文本或文件路径。

        返回:
        - str: 生成的 MD5 哈希值（十六进制字符串）。
        """
        hasher = hashlib.md5()

        if isinstance(input_data, (str, Path)):
            # 如果输入是文件路径，则直接对路径字符串进行哈希
            path_str = str(input_data)
            hasher.update(path_str.encode('utf-8'))
        else:
            # 如果输入是文本，则直接计算文本的哈希
            if isinstance(input_data, str):
                input_data = input_data.encode('utf-8')
            hasher.update(input_data)

        return hasher.hexdigest()

    def get_email_list(self):
        res = {}
        for name in self.email_handler.all_emails.keys():
            todo_list = self.email_handler.get_today_task_list(name)
            res[name] = todo_list
        return res

    def register_tasks(self, name, email_id_list, delta_date=1):
        current_time = datetime.now(timezone.utc)
        cutoff_date = current_time - timedelta(days=delta_date)
        # 计算截止日期
        start_ts = time.time()
        for email_id in tqdm.tqdm(email_id_list[::-1]):
            if time.time() - start_ts >= self.timeout:
                logger.error("Exceed timeout. Quit")
                return
            logger.info(f"Still have {self.timeout - time.time() + start_ts} seconds.")
            logger.info(f"Working on email {name} {email_id}")
            subject, m_content, sender, date = self.email_handler.get_email_detail(name, email_id)

            if subject is None:
                continue

            # 如果邮件日期早于截止日期，则跳过此邮件
            if date < cutoff_date:
                logger.info(f"Skipping old email dated {date}")
                break

            content = f"标题：{subject}\n FROM: {sender}\n RECEIVE_DATE: {date}\n CONTENT: {m_content}"
            logger.info(f"Content: {content}")
            try:
                out = self.flow_ins.unit_flow(content=content,
                                              receive_id=self.generate_md5_hash(m_content),
                                              source_name=f'Email_{name}')
                logger.success(f"{json.dumps(out, indent=4, ensure_ascii=False)}")
            except Exception as e:
                logger.error(e)
                logger.debug(traceback.format_exc())
                continue

    def main(self):
        res = self.get_email_list()
        for name in res:
            self.register_tasks(name, res[name])


if __name__ == "__main__":
    ins = DailyFlow()
    ins.main()
