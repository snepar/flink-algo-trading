import backtrader as bt
from alpaca.data import TimeFrame
from alpaca_trade_api import REST

from alpaca_config.keys import config
from strategies.MomentumStrategy import MomentumStrategy


def run_backtest(strategy, symbols, start, end, timeframe, cash):
    rest_api = REST(config['key_id'], config['secret_key'], base_url=config['trade_api_base_url'])

    #initialize backtrader broker
    cerebro = bt.Cerebro(stdstats=True)
    cerebro.broker.setcash(cash)

    # add strategy
    cerebro.addstrategy(strategy)

    # add analytics
    cerebro.addobserver(bt.observers.Value)
    cerebro.addobserver(bt.observers.BuySell)

    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='mysharpre')

    if type(symbols) == str:
        symbol = symbols
        alpaca_data = rest_api.get_bars(symbol, timeframe, start, end, adjustment='all').df
        data = bt.feeds.PandasData(dataname=alpaca_data, name=symbol)
        cerebro.adddata(data)
    elif type(symbols) == list or type(symbols) == set:
        for symbol in symbols:
            alpaca_data = rest_api.get_bars(symbol, timeframe, start, end, adjustment='all').df
            data = bt.feeds.PandasData(dataname=alpaca_data, name=symbol)
            cerebro.adddata(data)

    #run
    initial_portfolio_value = cerebro.broker.getvalue()
    print(f'Starting Portfolio Value: {initial_portfolio_value}')
    results = cerebro.run()
    final_portfolio_value = cerebro.broker.getvalue()
    print(
        f'Final Portfolio Value: {final_portfolio_value} ----> Return {(final_portfolio_value / initial_portfolio_value - 1) * 100}%')

    strat = results[0]
    print('Sharpe Ratio: ', strat.analyzers.mysharpre.get_analysis()['sharperatio'])
    cerebro.plot(iplot=False)

    return results


if __name__ == "__main__":
    #run_backtest(AllWeatherStrategy, ['VTI', 'TLT', 'IEF', 'GLD', 'DBC'], '2023-01-01', '2024-06-20', TimeFrame.Day, 100000)

    #run_backtest(strategy=GoldenCrossStrategy, symbols='AAPL', start='2023-01-01', end='2024-06-20', timeframe=TimeFrame.Day, cash=100000)

    run_backtest(strategy=MomentumStrategy, symbols='AAPL', start='2023-01-01', end='2024-06-20', timeframe=TimeFrame.Day, cash=100000)

