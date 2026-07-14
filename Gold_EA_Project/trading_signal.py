"""
AI 交易信号生成器
运行这个程序，AI 会告诉你现在该怎么做
"""

import pandas as pd
import numpy as np
import joblib
from datetime import datetime
import MetaTrader5 as mt5

# 加载训练好的模型
print("🔄 加载 AI 模型...")
model = joblib.load('gold_ai_model.pkl')
scaler = joblib.load('scaler.pkl')
print("✅ 模型加载成功！")

# 连接 MT5 获取最新数据
print("🔄 连接 MetaTrader 5...")
if not mt5.initialize():
    print("❌ MT5 初始化失败！请确保 MT5 已打开并登录")
    mt5.shutdown()
    exit()

account_info = mt5.account_info()
if account_info is None:
    print("❌ 未登录账户！")
    mt5.shutdown()
    exit()
print(f"✅ 已登录账户：{account_info.login}")

# 获取最新的 100 根 K 线（用于计算指标）
print("🔄 获取最新数据...")
SYMBOL = "XAUUSD"
rates = mt5.copy_rates_from_pos(SYMBOL, mt5.TIMEFRAME_H1, 0, 100)

if rates is None or len(rates) < 50:
    print("❌ 获取数据失败！")
    mt5.shutdown()
    exit()

df = pd.DataFrame(rates)
df['time'] = pd.to_datetime(df['time'], unit='s')
df = df[['time', 'open', 'high', 'low', 'close', 'tick_volume']]
df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']

# 计算技术指标
print("🔄 计算技术指标...")

# MACD
exp1 = df['Close'].ewm(span=12, adjust=False).mean()
exp2 = df['Close'].ewm(span=26, adjust=False).mean()
df['MACD'] = exp1 - exp2
df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']

# RSI
delta = df['Close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
df['RSI'] = 100 - (100 / (1 + rs))

# 布林带
df['MA20'] = df['Close'].rolling(window=20).mean()
df['BB_Upper'] = df['MA20'] + (df['Close'].rolling(window=20).std() * 2)
df['BB_Lower'] = df['MA20'] - (df['Close'].rolling(window=20).std() * 2)
df['BB_Width'] = df['BB_Upper'] - df['BB_Lower']

# 删除 NaN
df = df.dropna()

# 获取最新一条数据
latest = df.iloc[-1]
print(f"✅ 数据获取成功！最新时间：{latest['Date']}")
print(f"📊 最新价格：{latest['Close']:.2f}")

# 准备特征
features = [
    latest['MACD'],
    latest['MACD_Signal'],
    latest['MACD_Histogram'],
    latest['RSI'],
    latest['BB_Upper'],
    latest['BB_Lower'],
    latest['BB_Width'],
    latest['MA20']
]

# 标准化
features_scaled = scaler.transform([features])

# AI 预测
prob = model.predict_proba(features_scaled)[0][1]
prediction = model.predict(features_scaled)[0]

# 获取之前的几根 K 线判断趋势
prev_close = df['Close'].iloc[-2]
trend = "上涨" if latest['Close'] > prev_close else "下跌"

# 计算 ATR（波动率，用于设置止损止盈）
high_low = df['High'] - df['Low']
high_close = np.abs(df['High'] - df['Close'].shift())
low_close = np.abs(df['Low'] - df['Close'].shift())
ranges = pd.concat([high_low, high_close, low_close], axis=1)
true_range = np.max(ranges, axis=1)
atr = true_range.rolling(14).mean().iloc[-1]

# ============================================================
# 🎯 输出交易建议
# ============================================================

print("\n" + "="*60)
print("📊 AI 交易信号分析报告")
print("="*60)

print(f"\n📈 市场状态：")
print(f"   ├─ 当前价格：${latest['Close']:.2f}")
print(f"   ├─ 20日均线：${latest['MA20']:.2f}")
print(f"   ├─ 价格位置：{'高于' if latest['Close'] > latest['MA20'] else '低于'} 均线")
print(f"   ├─ RSI（强弱指标）：{latest['RSI']:.1f}")
print(f"   ├─ 布林带宽：${latest['BB_Width']:.2f}")
print(f"   └─ 短期趋势：{trend}")

print(f"\n🤖 AI 模型分析：")
print(f"   ├─ 上涨概率：{prob*100:.1f}%")
print(f"   ├─ 下跌概率：{(1-prob)*100:.1f}%")
print(f"   └─ 模型信心度：{'高' if prob > 0.7 or prob < 0.3 else '中' if prob > 0.6 or prob < 0.4 else '低'}")

# 交易建议
print(f"\n🎯 交易建议：")

if prob >= 0.70:
    # 强烈看涨
    print("   ✅ 建议：**买入（做多）**")
    print(f"   ├─ 入场价格：${latest['Close']:.2f}")
    print(f"   ├─ 止损价格：${latest['Close'] - atr * 1.5:.2f} (1.5倍ATR)")
    print(f"   ├─ 止盈价格：${latest['Close'] + atr * 2.5:.2f} (2.5倍ATR)")
    risk = atr * 1.5
    reward = atr * 2.5
    print(f"   ├─ 风险/收益比：1:{reward/risk:.2f}")
    print(f"   ├─ 建议仓位：**2% 总资金** (激进可3%)")
    print(f"   └─ 持有时间：预计 3-8 小时")

elif prob >= 0.60:
    # 轻度看涨
    print("   ⚠️ 建议：**轻仓试多**")
    print(f"   ├─ 入场价格：${latest['Close']:.2f}")
    print(f"   ├─ 止损价格：${latest['Close'] - atr * 1.2:.2f}")
    print(f"   ├─ 止盈价格：${latest['Close'] + atr * 2.0:.2f}")
    print(f"   ├─ 风险/收益比：1:{atr*2.0/(atr*1.2):.2f}")
    print(f"   ├─ 建议仓位：**1% 总资金**")
    print(f"   └─ 持有时间：预计 2-5 小时")

elif prob <= 0.30:
    # 强烈看跌
    print("   ❌ 建议：**卖出（做空）**")
    print(f"   ├─ 入场价格：${latest['Close']:.2f}")
    print(f"   ├─ 止损价格：${latest['Close'] + atr * 1.5:.2f}")
    print(f"   ├─ 止盈价格：${latest['Close'] - atr * 2.5:.2f}")
    print(f"   ├─ 风险/收益比：1:{atr*2.5/(atr*1.5):.2f}")
    print(f"   ├─ 建议仓位：**2% 总资金**")
    print(f"   └─ 持有时间：预计 3-8 小时")

elif prob <= 0.40:
    # 轻度看跌
    print("   ⚠️ 建议：**轻仓试空**")
    print(f"   ├─ 入场价格：${latest['Close']:.2f}")
    print(f"   ├─ 止损价格：${latest['Close'] + atr * 1.2:.2f}")
    print(f"   ├─ 止盈价格：${latest['Close'] - atr * 2.0:.2f}")
    print(f"   └─ 建议仓位：**1% 总资金**")

else:
    # 震荡观望
    print("   🤔 建议：**观望，不交易**")
    print("   ├─ 原因：市场方向不明，AI 信心度不足")
    print("   ├─ 上涨概率：{prob*100:.1f}%")
    print("   └─ 建议等待价格突破布林带中轨后再决定")

# 额外建议
print(f"\n📋 风险提示：")
print(f"   ├─ 当前波动率（ATR）：${atr:.2f}")
print(f"   ├─ 单笔最大亏损建议：≤ 总资金 2%")
print(f"   ├─ 今日数据时间：{latest['Date']}")
print(f"   └─ ⚠️ 此建议仅供参考，请自行判断！")

# 如果是震荡行情，给出条件单建议
if 0.40 < prob < 0.60:
    print(f"\n📌 条件单建议：")
    print(f"   ├─ 突破买入：价格突破 ${latest['MA20'] + atr * 0.5:.2f} 时做多")
    print(f"   └─ 跌破卖出：价格跌破 ${latest['MA20'] - atr * 0.5:.2f} 时做空")

print("\n" + "="*60)
print("🔄 建议每隔 30-60 分钟重新运行一次")
print("="*60)

# 关闭连接
mt5.shutdown()