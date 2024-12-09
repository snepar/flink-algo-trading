import backtrader as bt

class AllWeatherStrategy(bt.Strategy):
    def __init__(self):
        self.year_last_rebalanced = -1
        self.weights = {"VTI": 0.30, 'TLT': 0.40, 'IEF': 0.15, 'GLD': 0.075, 'DBC': 0.075}

    def next(self):
        if self.datetime.date().year == self.year_last_rebalanced:
            return

        self.year_last_rebalanced = self.datetime.date().year

        for i, d in enumerate(self.datas):
            symbol = d._name
            self.order_target_percent(d, target=self.weights[symbol])