CREATE OR REPLACE TABLE market_news (
    id BIGINT,
    author VARCHAR,
    headline VARCHAR,
    source VARCHAR,
    summary VARCHAR,
    data_provider VARCHAR,
    `url` VARCHAR,
    symbol VARCHAR,
    sentiment DECIMAL,
    timestamp_ms BIGINT,
    event_time AS TO_TIMESTAMP_LTZ(timestamp_ms, 3),
    WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'market-news',
    'properties.bootstrap.servers' = 'redpanda-1:29092,redpanda-2:29092',
    'properties.group.id' = 'test-group',
    'properties.auto.offset.reset' = 'earliest',
    'format' = 'json'
);


CREATE OR REPLACE TABLE stock_prices (
    symbol VARCHAR,
    `open` FLOAT,
    high FLOAT,
    low FLOAT,
    `close` FLOAT,
    volume DECIMAL,
    trade_count FLOAT,
    vwap DECIMAL,
    provider VARCHAR,
    `timestamp` BIGINT,
    event_time AS TO_TIMESTAMP_LTZ(`timestamp`, 3),
    WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'stock-prices',
    'properties.bootstrap.servers' = 'redpanda-1:29092,redpanda-2:29093',
    'properties.group.id' = 'test-group',
    'properties.auto.offset.reset' = 'earliest',
    'format' = 'json'
);

CREATE OR REPLACE VIEW sma_20 AS
SELECT symbol, `close`, event_time,
    AVG(`close`) OVER (PARTITION BY symbol ORDER BY event_time ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS sma_20
FROM stock_prices;

CREATE OR REPLACE VIEW sma_50 AS
SELECT
    symbol,
    `close`,
    event_time,
    AVG(`close`) OVER (PARTITION BY symbol ORDER BY event_time ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS sma_50
FROM stock_prices;

CREATE OR REPLACE VIEW price_with_movavg AS
SELECT
    s20.symbol,
    s20.`close`,
    s20.event_time,
    s20.sma_20,
    s50.sma_50
FROM sma_20 s20
JOIN sma_50 s50
    ON s20.symbol = s50.symbol AND s20.event_time = s50.event_time;

CREATE OR REPLACE VIEW news_and_prices AS
SELECT
    n.symbol,
    n.headline,
    n.sentiment,
    p.`close`,
    p.sma_20,
    p.sma_50,
    n.event_time AS news_time,
    p.event_time AS price_time
FROM market_news n
JOIN price_with_movavg p
    ON n.symbol = p.symbol
    AND n.event_time BETWEEN p.event_time - INTERVAL '1' MINUTE AND p.event_time + INTERVAL '1' MINUTE;


CREATE OR REPLACE VIEW trading_signals AS
SELECT
    symbol,
    news_time,
    `close`,
    1 as quantity,
    CASE
        WHEN sentiment > 0 AND `close` < sma_20 AND lag(`close`, 1) OVER (PARTITION BY symbol ORDER BY news_time) >= sma_20 THEN 'BUY'
        WHEN sentiment < 0 AND `close` > sma_20 AND lag(`close`, 1) OVER (PARTITION BY symbol ORDER BY news_time) <= sma_20 THEN 'SELL'
        ELSE NULL
    END AS signal
FROM news_and_prices;

CREATE OR REPLACE TABLE trading_signals_sink (
    symbol STRING,
    signal_time TIMESTAMP_LTZ,
    signal STRING
) WITH (
    'connector' = 'kafka',
    'topic' = 'trading-signals',
    'properties.bootstrap.servers' = 'redpanda-1:29092, redpanda-2:29092',
    'properties.group.id' = 'test-group',
    'format' = 'json'
);

INSERT INTO trading_signals_sink
SELECT symbol, news_time, signal
FROM trading_signals
WHERE signal IS NOT NULL;