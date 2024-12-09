import backtrader as bt

class MomentumStrategy(bt.Strategy):
    params = (
        ('momentum_period', 12),
        ('exit_period', 26)
    )

    def __init__(self):
        self.momentum = bt.indicators.MomentumOscillator(
            self.datas[0].close, period=self.params.momentum_period)
        self.exit_signal = bt.indicators.EMA(
            self.datas[0].close, period=self.params.exit_period)

    def next(self):
        if not self.position:
            if self.momentum > 100:
                self.buy()
        elif self.datas[0].close[0] < self.exit_signal[0]:
            self.close()