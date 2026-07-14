"""
黄金EA项目 - 阶段4：完整策略回测
"""

import pandas as pd
import numpy as np
import joblib
import backtrader as bt
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

print("📈 开始策略回测...")

# 加载模型和标准化器
model = joblib.load('gold_ai_model.pkl')
scaler = joblib.load('scaler.pkl')

# 读取数据
df = pd.read_csv('XAUUSD_H1_with_indicators.csv', parse_dates=['Date'])
df = df.set_index('Date')

# -------- 自定义策略类 --------
class AIStrategy(bt.Strategy):
    params = (
        ('model', model),
        ('scaler', scaler),
        ('features', ['MACD', 'MACD_Signal', 'MACD_Histogram', 'RSI', 'BB_Upper', 'BB_Lower', 'BB_Width', 'MA20']),
        ('threshold', 0.70),  # 只有当预测概率 > 70% 时才开仓
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.trade_count = 0
        self.win_count = 0

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')

    def next(self):
        if self.order:
            return

        # 获取当前特征
        try:
            features_values = [
                self.datas[0].macd[0],
                self.datas[0].macd_signal[0],
                self.datas[0].macd_hist[0],
                self.datas[0].rsi[0],
                self.datas[0].bb_upper[0],
                self.datas[0].bb_lower[0],
                self.datas[0].bb_width[0],
                self.datas[0].ma20[0]
            ]
            
            # 检查是否有NaN
            if any(np.isnan(f) for f in features_values):
                return
                
            # 标准化
            features_scaled = self.params.scaler.transform([features_values])
            
            # AI预测
            prob = self.params.model.predict_proba(features_scaled)[0][1]
            
            # 交易逻辑
            if prob > self.params.threshold and not self.position:
                # 买入
                self.buy()
                self.trade_count += 1
                self.log(f'买入 (概率: {prob*100:.1f}%)')
                
            elif prob < (1 - self.params.threshold) and self.position:
                # 卖出
                self.close()
                self.log(f'卖出 (概率: {prob*100:.1f}%)')
                
        except Exception as e:
            pass

    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Margin]:
            self.order = None
            
    def notify_trade(self, trade):
        if trade.isclosed:
            if trade.pnl > 0:
                self.win_count += 1

# -------- 自定义数据加载类 --------
class PandasData(bt.feeds.PandasData):
    lines = ('macd', 'macd_signal', 'macd_hist', 'rsi', 'bb_upper', 'bb_lower', 'bb_width', 'ma20')
    params = (
        ('macd', 'MACD'),
        ('macd_signal', 'MACD_Signal'),
        ('macd_hist', 'MACD_Histogram'),
        ('rsi', 'RSI'),
        ('bb_upper', 'BB_Upper'),
        ('bb_lower', 'BB_Lower'),
        ('bb_width', 'BB_Width'),
        ('ma20', 'MA20'),
    )

# -------- 运行回测 --------
cerebro = bt.Cerebro()
cerebro.addstrategy(AIStrategy)

# 添加数据
data = PandasData(dataname=df)
cerebro.adddata(data)

# 设置初始资金
initial_cash = 10000.0
cerebro.broker.setcash(initial_cash)

# 设置佣金（黄金点差约 0.001%）
cerebro.broker.setcommission(commission=0.001)

print(f'💰 初始资金: ${initial_cash:.2f}')
print(f'📊 数据量: {len(df)} 根K线')

# 运行回测
print('🔄 开始回测...')
results = cerebro.run()

print(f'\n💰 最终资金: ${cerebro.broker.getvalue():.2f}')
print(f'📈 总收益: ${cerebro.broker.getvalue() - initial_cash:.2f}')
print(f'📊 收益率: {(cerebro.broker.getvalue() - initial_cash) / initial_cash * 100:.2f}%')

# 获取策略实例
strategy = cerebro.strats[0] if cerebro.strats else None
if strategy:
    print(f'📊 总交易次数: {strategy.trade_count}')
    if strategy.trade_count > 0:
        print(f'🎯 胜率: {strategy.win_count / strategy.trade_count * 100:.1f}%')

# 绘制回测曲线
print('\n📊 正在生成回测图表...')
cerebro.plot(style='candlestick', volume=False)

print('\n✅ 阶段4完成！')