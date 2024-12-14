import traceback

from flask import Flask, request, jsonify
from loguru import logger
from threading import Lock
from pathlib import Path
import yaml
from main import ShipmentFlow

app = Flask(__name__)


CONFIG_PATH = Path(__file__).parent / 'configs' / 'backend_configs.yaml'
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config_data = yaml.load(f, Loader=yaml.FullLoader)
LLM_PARAMS = config_data.get('LLM', {}).get("llm_params", {})
LLM_PLATFORM = LLM_PARAMS.get('platform')
logger.info(f"LLM_PLATFORM : {LLM_PLATFORM}")
logger.info(f"LLM_PARAMS: {LLM_PARAMS}")

WEB_PORT = int(config_data.get("WEB", {}).get('port'))

FEISHU_CONFIG_PATH = Path(__file__).parent / 'configs' / 'feishu_config.yaml'

previous_id_lock = Lock()
app.config['data_queue'] = []
app.config['previous_id'] = None

SHIPMENT_FLOW_INS = ShipmentFlow(FEISHU_CONFIG_PATH)

@app.route('/api/lark_event', methods=['POST'])
def receive_data():
    # 获取POST请求中的JSON数据
    data = request.get_json()

    # 打印接收到的数据
    logger.info(f"Received Data: {data}")
    inserted_msgs = []
    if data.get('header', {}).get('event_type') == 'im.message.receive_v1':
        with previous_id_lock:  # 使用锁保护previous_id的读写操作
            msg_id = data.get('event', {}).get('message', {}).get('message_id')
            logger.info(f"Received Message. MSG_ID: {msg_id}")
            if msg_id != app.config['previous_id']:
                app.config['data_queue'].append(data)
            if app.config['data_queue'] and msg_id != app.config['previous_id']:
                msg_dicts = app.config['data_queue']
                # inserted_msgs = msg_dicts
                try:
                    inserted_msgs = SHIPMENT_FLOW_INS.process_msg_dicts(msg_dicts)
                    logger.info(msg_dicts)
                    app.config['data_queue'] = []
                    app.config['previous_id'] = msg_id
                except:
                    logger.error(traceback.format_exc())
                    app.config['data_queue'] = []
                    app.config['previous_id'] = msg_id

    logger.warning("DATA QUEUE:")
    logger.info(app.config['data_queue'])
    logger.warning("PREVIOUS ID:")
    logger.info(app.config['previous_id'])

    # 返回一个响应给客户端
    response = {"challenge": data.get('challenge')} if data.get('challenge') else {'note': 'success',
                                                                                   'data': inserted_msgs,
                                                                                   'data_string': f'PASS',
                                                                                   "challenge": data.get('challenge')}
    return jsonify(response), 200

@app.route('/api/add_bx', methods=['POST'])
def add_data_to_bx():
    data = request.get_json()
    # 打印接收到的数据
    logger.info(f"Received Data: {data}")
    return jsonify({"Status": 1}), 200


if __name__ == '__main__':
    app.run("0.0.0.0", port=WEB_PORT)
