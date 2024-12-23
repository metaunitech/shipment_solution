import json
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
    # 从 Form Data 获取数据
    data = request.form.to_dict()  # 转为 Python 字典

    # 打印接收到的数据
    logger.info(f"Received Form Data: {data}")
    for keyname in ['YJBL']:
        try:
            data[keyname] = float(data[keyname])
        except:
            data[keyname] = data[keyname]
    res = SHIPMENT_FLOW_INS.bx_handler.add_sa_job(payload=data)
    # 返回 JSON 响应
    return jsonify(res), 200


@app.route('/api/add_bx_cargo', methods=['POST'])
def add_data_to_bx_cargo():
    # 从 Form Data 获取数据
    data = request.form.to_dict()  # 转为 Python 字典
    # 打印接收到的数据
    logger.info(f"Received Form Data: {data}")
    raw_text = data.get('原文依据')
    extraction_res = [[data, raw_text]]
    res = SHIPMENT_FLOW_INS.insert_data_to_bx(document_path=None,
                                              document_type='cargo_info',
                                              extraction_res=extraction_res,
                                              event_id=None,
                                              raw_text=raw_text)
    # 返回 JSON 响应
    return jsonify(res), 200


@app.route('/api/add_bx_vessel', methods=['POST'])
def add_data_to_bx_vessel():
    # 从 Form Data 获取数据
    data = request.form.to_dict()  # 转为 Python 字典
    # 打印接收到的数据
    logger.info(f"Received Form Data: {data}")
    raw_text = data.get('原文依据')
    extraction_res = [[data, raw_text]]
    res = SHIPMENT_FLOW_INS.insert_data_to_bx(document_path=None,
                                              document_type='ship_info',
                                              extraction_res=extraction_res,
                                              event_id=None,
                                              raw_text=raw_text)
    # 返回 JSON 响应
    return jsonify(res), 200


@app.route('/api/update_knowledge', methods=['POST'])
def update_knowledge():
    # 从 Form Data 获取数据
    data = request.form.to_dict()  # 转为 Python 字典
    # 打印接收到的数据
    logger.info(f"Received Form Data: {data}")
    knowledge_json_path = Path(__file__).parent/'modules'/'knowledges'/'uploaded_knowledge.json'
    if knowledge_json_path.exists():
        with open(knowledge_json_path, 'r', encoding='utf-8') as f:
            knowledge = json.load(f)
    knowledge[data['知识类型']] = data['知识主体']
    with open(knowledge_json_path, 'w', encoding='utf-8') as f:
        json.dump(knowledge, f, indent=2, ensure_ascii=False)
    SHIPMENT_FLOW_INS.extra_knowledge = knowledge
    return jsonify(knowledge), 200


if __name__ == '__main__':
    app.run("0.0.0.0", port=WEB_PORT)
