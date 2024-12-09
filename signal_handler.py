import json

import pyflink
import requests
from pyflink.common import SimpleStringSchema, Types
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors.kafka import FlinkKafkaConsumer
from alpaca_config.keys import config
import alpaca_trade_api as trade_api

api = trade_api.REST(config['key_id'], config['secret_key'], config['trade_api_base_url'], api_version='v2')
def send_to_slack(message, token, channel_id):
    url = 'https://slack.com/api/chat.postMessage'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }

    data = {
        'channel': channel_id,
        'text': message
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code != 200:
        raise ValueError(f'Failed to send message to slack, {response.status_code}, response: {response.text}')

def place_order(symbol, qty, side, order_type, time_in_force):
    try:
        order = api.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type=order_type,
            time_in_force=time_in_force
        )
        print(f'Order submitted: {order}')
        return order
    except Exception as e:
        print(f'An error occured while submitting order {e}')
        return None


def process_message(message, token, channel_id):
    print('Received message: ', message)
    try:
        message_dict = json.loads(message)
        symbol = message_dict.get('symbol', 'N/A')
        signal_time = message_dict.get('signal_time', 'N/A')
        signal = message_dict.get('signal', 'N/A')

        formatted_message = """
        =============================
        ALERT ⚠️ New Trading Signal!\n
        Symbol: {symbol} \n
        Signal: {signal} \n
        Time: {signal_time}
        =============================
        """.format(
            symbol=symbol,
            signal=signal,
            signal_time=signal_time
        )

        send_to_slack(formatted_message, token, channel_id)
        order = place_order(symbol=symbol, qty=5, side=str(signal).lower(),
                    order_type='market', time_in_force='gtc')

        print('Order successfully placed!', order)
    except Exception as e:
        print('Failed to decode message: ', message, e)


def main():
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(4)
    env.add_jars('./libs/flink-sql-connector-kafka-3.1.0-1.18.jar')

    kafka_consumer_properties = {
        'bootstrap.servers': 'localhost:9092,localhost:9093',
        'group.id': 'news_trading_consumer_group',
        'auto.offset.reset': 'earliest'
    }

    kafka_consumer = FlinkKafkaConsumer(
        topics='trading-signals',
        deserialization_schema=SimpleStringSchema(),
        properties=kafka_consumer_properties
    )

    kafka_stream = env.add_source(kafka_consumer, type_info=Types.STRING())

    slack_token = config['slack_token']
    slack_channel_id = config['slack_channel_id']

    kafka_stream.map(lambda message: process_message(message, slack_token, slack_channel_id))

    env.execute('Flink Algorithmic Trading')

if __name__ == "__main__":
    main()