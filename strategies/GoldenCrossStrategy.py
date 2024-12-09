import backtrader as bt

class GoldenCrossStrategy(bt.Strategy):
    params = (
        ('short_window', 50),
        ('long_window', 200)
    )

    def __init__(self):
        self.short_ema = bt.indicators.EMA(self.datas[0].close, period=self.params.short_window)
        self.long_ema = bt.indicators.EMA(self.datas[0].close, period=self.params.long_window)
        self.crossover = bt.indicators.CrossOver(self.short_ema, self.long_ema)

    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy()
        elif self.crossover < 0:
            self.close()