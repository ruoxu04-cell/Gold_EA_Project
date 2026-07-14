"""
黄金EA项目 - 阶段2：计算 MACD、RSI、布林带技术指标
"""

import pandas as pd
import numpy as np

print("📊 开始计算技术指标...")

# 读取刚才下载的数据
df = pd.read_csv('XAUUSD_H1_10years.csv', parse_dates=['Date'])
print(f"✅ 读取数据成功！共 {len(df)} 根K线")

# -------- 1. 计算 MACD (12, 26, 9) --------
def calculate_macd(data, fast=12, slow=26, signal=9):
    exp1 = data['Close'].ewm(span=fast, adjust=False).mean()
    exp2 = data['Close'].ewm(span=slow, adjust=False).mean()
    data['MACD'] = exp1 - exp2
    data['MACD_Signal'] = data['MACD'].ewm(span=signal, adjust=False).mean()
    data['MACD_Histogram'] = data['MACD'] - data['MACD_Signal']
    return data

# -------- 2. 计算 RSI (14) --------
def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    return data

# -------- 3. 计算布林带 (20, 2) --------
def calculate_bollinger(data, period=20, std_dev=2):
    data['MA20'] = data['Close'].rolling(window=period).mean()
    data['BB_Upper'] = data['MA20'] + (data['Close'].rolling(window=period).std() * std_dev)
    data['BB_Lower'] = data['MA20'] - (data['Close'].rolling(window=period).std() * std_dev)
    data['BB_Width'] = data['BB_Upper'] - data['BB_Lower']
    return data

# 执行计算
print("🔄 计算 MACD...")
df = calculate_macd(df)

print("🔄 计算 RSI...")
df = calculate_rsi(df)

print("🔄 计算布林带...")
df = calculate_bollinger(df)

# 删除前20行（因为布林带和RSI需要前期数据，前20行是NaN）
df = df.dropna()

# 保存带指标的完整数据
df.to_csv('XAUUSD_H1_with_indicators.csv', index=False)

print(f"✅ 指标计算完成！共 {len(df)} 根有效K线")
print("\n📊 数据预览（前5行）：")
print(df[['Date', 'Close', 'MACD', 'RSI', 'BB_Upper', 'BB_Lower']].head())

print("\n📊 数据统计：")
print(f"   MACD 范围：{df['MACD'].min():.2f} 到 {df['MACD'].max():.2f}")
print(f"   RSI 范围：{df['RSI'].min():.2f} 到 {df['RSI'].max():.2f}")
print(f"   布林带宽范围：{df['BB_Width'].min():.2f} 到 {df['BB_Width'].max():.2f}")

print("\n✅ 阶段2完成！文件已保存：XAUUSD_H1_with_indicators.csv")