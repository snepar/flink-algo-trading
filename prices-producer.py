import json
from datetime import datetime
from typing import List

from alpaca.data import StockHistoricalDataClient, StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from kafka import KafkaProducer

from alpaca_config.keys import config


def get_producer(brokers: List[str]):
    producer = KafkaProducer(
        bootstrap_servers=brokers,
        key_serializer=str.encode,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    return producer


def produce_historical_price(
        redpanda_client: KafkaProducer,
        topic: str,
        start_date: str,
        end_date: str,
        symbol: str
):
    api = StockHistoricalDataClient(api_key=config['key_id'], secret_key=config['secret_key'])

    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    granularity = TimeFrame.Minute

    request_params = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=granularity,
        start=start_date,
        end=end_date
    )

    prices_df = api.get_stock_bars(request_params).df
    prices_df.reset_index(inplace=True)

    records = json.loads(prices_df.to_json(orient='records'))
    for idx, record in enumerate(records):
        record['provider'] = 'alpaca'

        try:
            future = redpanda_client.send(
                topic=topic,
                key=record['symbol'],
                value=record,
                timestamp_ms=record['timestamp']
            )

            _ = future.get(timeout=10)
            print(f'Record sent successfully')
        except Exception as e:
            print(f'Error sending message for symbol {symbol}: {e.__class__.__name__} - {e}')


if __name__ == '__main__':
    redpanda_client = get_producer(config['redpanda_brokers'])
    produce_historical_price(
        redpanda_client,
        topic='stock-prices',
        start_date='2024-12-01',
        end_date='2024-12-08',
        symbol='AAPL'
    )

    redpanda_client.close()
