"""
AI 交易信号生成器 - 升级版
动态止损止盈 + 多时间框架分析 + 支撑阻力位
"""

import pandas as pd
import numpy as np
import joblib
from datetime import datetime, timedelta
import MetaTrader5 as mt5
import warnings
warnings.filterwarnings('ignore')

print("="*60)
print("📊 黄金 XAUUSD AI 交易信号系统 v2.0")
print("   动态止损止盈 + 精准入场")
print("="*60)

# ============================================================
# 1. 加载 AI 模型
# ============================================================
print("\n🔄 加载 AI 模型...")

try:
    model = joblib.load('gold_ai_model.pkl')
    scaler = joblib.load('scaler.pkl')
    print("✅ 随机森林模型加载成功！")
except:
    print("❌ 模型加载失败！")
    exit()

# ============================================================
# 2. 连接 MT5
# ============================================================
print("\n🔄 连接 MetaTrader 5...")

if not mt5.initialize():
    print("❌ MT5 初始化失败！")
    mt5.shutdown()
    exit()

account_info = mt5.account_info()
if account_info is None:
    print("❌ 未登录账户！")
    mt5.shutdown()
    exit()

print(f"✅ 已登录账户：{account_info.login}")

# ============================================================
# 3. 获取多周期数据（1小时 + 4小时 + 15分钟）
# ============================================================
print("\n🔄 获取多周期市场数据...")

SYMBOL = "XAUUSD"

def get_data(timeframe, bars=200):
    rates = mt5.copy_rates_from_pos(SYMBOL, timeframe, 0, bars)
    if rates is None:
        return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df = df[['time', 'open', 'high', 'low', 'close', 'tick_volume']]
    df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    return df

# 获取不同周期数据
df_h1 = get_data(mt5.TIMEFRAME_H1, 200)      # 1小时
df_h4 = get_data(mt5.TIMEFRAME_H4, 100)      # 4小时
df_m15 = get_data(mt5.TIMEFRAME_M15, 300)    # 15分钟

if df_h1 is None or len(df_h1) < 50:
    print("❌ 获取数据失败！")
    mt5.shutdown()
    exit()

print(f"✅ 数据获取成功！")
print(f"   ├─ 1小时图：{len(df_h1)} 根K线")
print(f"   ├─ 4小时图：{len(df_h4)} 根K线" if df_h4 is not None else "   ├─ 4小时图：无数据")
print(f"   └─ 15分钟图：{len(df_m15)} 根K线" if df_m15 is not None else "   └─ 15分钟图：无数据")

# ============================================================
# 4. 计算技术指标（1小时图）
# ============================================================
print("\n🔄 计算技术指标...")

def calculate_indicators(df):
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
    
    # 增加更多指标
    # ATR
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    df['ATR'] = true_range.rolling(14).mean()
    
    # 成交量均线
    df['Volume_MA'] = df['Volume'].rolling(20).mean()
    
    return df

df_h1 = calculate_indicators(df_h1)
df_h1 = df_h1.dropna()

if df_h4 is not None:
    df_h4 = calculate_indicators(df_h4)
    df_h4 = df_h4.dropna()

if df_m15 is not None:
    df_m15 = calculate_indicators(df_m15)
    df_m15 = df_m15.dropna()

print(f"✅ 指标计算完成！有效数据：{len(df_h1)} 根K线")

# ============================================================
# 5. AI 预测
# ============================================================
print("\n🤖 AI 模型分析中...")

latest = df_h1.iloc[-1]

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

features_scaled = scaler.transform([features])
prob = model.predict_proba(features_scaled)[0][1]

print(f"✅ 分析完成！")
print(f"   ├─ 上涨概率：{prob*100:.1f}%")
print(f"   └─ 下跌概率：{(1-prob)*100:.1f}%")

# ============================================================
# 6. 动态计算关键位（精准版）
# ============================================================
print("\n🔄 计算精准支撑阻力位...")

# --- 6a. 多周期支撑阻力 ---
def find_support_resistance(df, lookback=50):
    """找关键支撑阻力位"""
    recent_high = df['High'].iloc[-lookback:].max()
    recent_low = df['Low'].iloc[-lookback:].min()
    
    # 找前高前低
    pivots_high = []
    pivots_low = []
    
    for i in range(5, len(df)-5):
        if df['High'].iloc[i] == df['High'].iloc[i-5:i+5].max():
            pivots_high.append(df['High'].iloc[i])
        if df['Low'].iloc[i] == df['Low'].iloc[i-5:i+5].min():
            pivots_low.append(df['Low'].iloc[i])
    
    # 最近的支撑阻力
    if len(pivots_high) > 0:
        nearest_resistance = min([h for h in pivots_high if h > df['Close'].iloc[-1]], default=df['Close'].iloc[-1] * 1.01)
    else:
        nearest_resistance = df['Close'].iloc[-1] * 1.01
    
    if len(pivots_low) > 0:
        nearest_support = max([l for l in pivots_low if l < df['Close'].iloc[-1]], default=df['Close'].iloc[-1] * 0.99)
    else:
        nearest_support = df['Close'].iloc[-1] * 0.99
    
    return nearest_support, nearest_resistance, recent_high, recent_low

# 1小时图支撑阻力
support_h1, resistance_h1, high_h1, low_h1 = find_support_resistance(df_h1)

# 4小时图支撑阻力（如果有）
if df_h4 is not None and len(df_h4) > 20:
    support_h4, resistance_h4, high_h4, low_h4 = find_support_resistance(df_h4)
else:
    support_h4, resistance_h4 = support_h1, resistance_h1

# 15分钟图支撑阻力（如果有）
if df_m15 is not None and len(df_m15) > 20:
    support_m15, resistance_m15, high_m15, low_m15 = find_support_resistance(df_m15)
else:
    support_m15, resistance_m15 = support_h1, resistance_h1

# --- 6b. 动态ATR ---
atr = latest['ATR'] if not pd.isna(latest['ATR']) else 12

# --- 6c. 斐波那契水平 ---
current_price = latest['Close']
range_high = max(high_h1, high_h4 if df_h4 is not None else high_h1)
range_low = min(low_h1, low_h4 if df_h4 is not None else low_h1)
fib_range = range_high - range_low

fib_levels = {
    '0.236': range_low + fib_range * 0.236,
    '0.382': range_low + fib_range * 0.382,
    '0.5': range_low + fib_range * 0.5,
    '0.618': range_low + fib_range * 0.618,
    '0.786': range_low + fib_range * 0.786,
}

print(f"✅ 关键位计算完成！")
print(f"   ├─ 1小时支撑：${support_h1:.2f}")
print(f"   ├─ 1小时阻力：${resistance_h1:.2f}")
print(f"   ├─ 4小时支撑：${support_h4:.2f}")
print(f"   ├─ 4小时阻力：${resistance_h4:.2f}")
print(f"   └─ ATR波动率：${atr:.2f}")

# ============================================================
# 7. 计算精确的止损止盈（动态版）
# ============================================================
current_price = latest['Close']

# 根据市场状态动态调整倍数
if atr > 20:
    # 高波动市场：扩大止损
    stop_multiplier = 1.8
    take_multiplier = 3.0
elif atr > 12:
    # 中等波动
    stop_multiplier = 1.5
    take_multiplier = 2.5
else:
    # 低波动市场：缩小止损
    stop_multiplier = 1.2
    take_multiplier = 2.0

# 根据趋势强度调整
trend_strength = abs(latest['Close'] - df_h1['Close'].iloc[-10]) / df_h1['Close'].iloc[-10] * 100
if trend_strength > 2:
    # 强趋势：扩大止盈
    take_multiplier += 0.5

if prob >= 0.70 or prob <= 0.30:
    # 强烈信号：稍大仓位
    risk_percent = 2.0
else:
    risk_percent = 1.0

# --- 计算做多止损止盈 ---
long_stop = current_price - atr * stop_multiplier
long_take = current_price + atr * take_multiplier

# 根据支撑阻力调整
long_stop = min(long_stop, support_h1 - 2)  # 止损设在支撑下方
long_take = min(long_take, resistance_h1, resistance_h4)  # 止盈设在阻力附近

# --- 计算做空止损止盈 ---
short_stop = current_price + atr * stop_multiplier
short_take = current_price - atr * take_multiplier

# 根据支撑阻力调整
short_stop = max(short_stop, resistance_h1 + 2)  # 止损设在阻力上方
short_take = max(short_take, support_h1, support_h4)  # 止盈设在支撑附近

# 计算风险收益比
long_risk = abs(current_price - long_stop)
long_reward = abs(long_take - current_price)
long_rr = long_reward / long_risk if long_risk > 0 else 0

short_risk = abs(short_stop - current_price)
short_reward = abs(current_price - short_take)
short_rr = short_reward / short_risk if short_risk > 0 else 0

# ============================================================
# 8. 多周期趋势确认
# ============================================================
def get_trend(df, period=50):
    """判断趋势方向"""
    if len(df) < period:
        return "震荡"
    
    sma20 = df['Close'].rolling(20).mean().iloc[-1]
    sma50 = df['Close'].rolling(50).mean().iloc[-1]
    current = df['Close'].iloc[-1]
    
    if current > sma20 > sma50:
        return "强势上涨"
    elif current > sma20 and current > sma50:
        return "上涨"
    elif current < sma20 < sma50:
        return "强势下跌"
    elif current < sma20 and current < sma50:
        return "下跌"
    else:
        return "震荡"

trend_h1 = get_trend(df_h1)
trend_h4 = get_trend(df_h4) if df_h4 is not None else "无数据"
trend_m15 = get_trend(df_m15) if df_m15 is not None else "无数据"

# ============================================================
# 9. 输出完整报告
# ============================================================
print("\n" + "="*60)
print("📊 AI 交易信号分析报告 v2.0（动态精准版）")
print("="*60)

print(f"\n📈 市场状态：")
print(f"   ├─ 当前价格：${current_price:.2f}")
print(f"   ├─ 20日均线：${latest['MA20']:.2f}")
print(f"   ├─ 价格偏离均线：{((current_price - latest['MA20']) / latest['MA20'] * 100):.2f}%")
print(f"   ├─ RSI：{latest['RSI']:.1f}")
print(f"   ├─ 布林带宽：${latest['BB_Width']:.2f}")
print(f"   ├─ 1小时趋势：{trend_h1}")
print(f"   ├─ 4小时趋势：{trend_h4}")
print(f"   ├─ 15分钟趋势：{trend_m15}")
print(f"   └─ ATR波动率：${atr:.2f}")

print(f"\n🔑 关键支撑阻力位：")
print(f"   ├─ 1小时支撑：${support_h1:.2f}  |  1小时阻力：${resistance_h1:.2f}")
print(f"   ├─ 4小时支撑：${support_h4:.2f}  |  4小时阻力：${resistance_h4:.2f}")
print(f"   ├─ 50根K线最高：${high_h1:.2f}  |  50根K线最低：${low_h1:.2f}")
print(f"   └─ 斐波那契0.618：${fib_levels['0.618']:.2f}")

print(f"\n🤖 AI 模型分析：")
print(f"   ├─ 上涨概率：{prob*100:.1f}%")
print(f"   ├─ 下跌概率：{(1-prob)*100:.1f}%")
print(f"   └─ 信号强度：{'强烈' if prob > 0.7 or prob < 0.3 else '中等' if prob > 0.6 or prob < 0.4 else '弱'}")

# ============================================================
# 10. 精准交易建议
# ============================================================
print(f"\n🎯 精准交易建议：")

if prob >= 0.70:
    # 强烈看涨
    print(f"   ✅ 建议：**买入（做多）**")
    print(f"   ├─ 入场价格：${current_price:.2f}")
    print(f"   ├─ 止损价格：${long_stop:.2f}")
    print(f"   ├─ 止盈价格：${long_take:.2f}")
    print(f"   ├─ 风险点数：${long_risk:.2f} 点")
    print(f"   ├─ 收益点数：${long_reward:.2f} 点")
    print(f"   ├─ 风险/收益比：1:{long_rr:.2f}")
    print(f"   ├─ 建议仓位：**{risk_percent:.0f}% 总资金**")
    print(f"   ├─ 持有时间：预计 3-8 小时")
    print(f"   └─ 参考：斐波那契目标 {fib_levels['0.618']:.2f}")

elif prob >= 0.55:
    # 轻度看涨
    print(f"   ⚠️ 建议：**轻仓试多**")
    print(f"   ├─ 入场价格：${current_price:.2f}")
    print(f"   ├─ 止损价格：${long_stop:.2f}")
    print(f"   ├─ 止盈价格：${long_take:.2f}")
    print(f"   ├─ 风险点数：${long_risk:.2f} 点")
    print(f"   ├─ 收益点数：${long_reward:.2f} 点")
    print(f"   ├─ 风险/收益比：1:{long_rr:.2f}")
    print(f"   ├─ 建议仓位：**1% 总资金**")
    print(f"   └─ 持有时间：预计 2-5 小时")

elif prob <= 0.30:
    # 强烈看跌
    print(f"   ❌ 建议：**卖出（做空）**")
    print(f"   ├─ 入场价格：${current_price:.2f}")
    print(f"   ├─ 止损价格：${short_stop:.2f}")
    print(f"   ├─ 止盈价格：${short_take:.2f}")
    print(f"   ├─ 风险点数：${short_risk:.2f} 点")
    print(f"   ├─ 收益点数：${short_reward:.2f} 点")
    print(f"   ├─ 风险/收益比：1:{short_rr:.2f}")
    print(f"   ├─ 建议仓位：**{risk_percent:.0f}% 总资金**")
    print(f"   └─ 持有时间：预计 3-8 小时")

elif prob <= 0.45:
    # 轻度看跌
    print(f"   ⚠️ 建议：**轻仓试空**")
    print(f"   ├─ 入场价格：${current_price:.2f}")
    print(f"   ├─ 止损价格：${short_stop:.2f}")
    print(f"   ├─ 止盈价格：${short_take:.2f}")
    print(f"   ├─ 风险点数：${short_risk:.2f} 点")
    print(f"   ├─ 收益点数：${short_reward:.2f} 点")
    print(f"   ├─ 风险/收益比：1:{short_rr:.2f}")
    print(f"   ├─ 建议仓位：**1% 总资金**")
    print(f"   └─ 持有时间：预计 2-5 小时")

else:
    # 震荡观望
    print(f"   🤔 建议：**观望，不交易**")
    print(f"   ├─ 原因：市场方向不明，AI 信心度不足")
    print(f"   ├─ 上涨概率：{prob*100:.1f}%")
    print(f"   └─ 等待价格突破 ${fib_levels['0.618']:.2f} 或跌破 ${support_h1:.2f}")

# ============================================================
# 11. 风险提示
# ============================================================
print(f"\n📋 风险提示：")
print(f"   ├─ 当前波动率（ATR）：${atr:.2f}")
print(f"   ├─ 单笔最大亏损建议：≤ 总资金 2%")
print(f"   ├─ 数据时间：{latest['Date']}")
print(f"   ├─ 模型类型：随机森林 (Random Forest)")
print(f"   ├─ 多周期确认：1小时 {trend_h1} / 4小时 {trend_h4}")
print(f"   └─ ⚠️ 此建议仅供参考，请自行判断！")

# ============================================================
# 12. 条件单建议
# ============================================================
if 0.40 < prob < 0.60:
    entry_long = fib_levels['0.5'] + 3
    entry_short = fib_levels['0.5'] - 3
    print(f"\n📌 条件单建议：")
    print(f"   ├─ 突破买入：价格突破 ${entry_long:.2f} 时做多")
    print(f"   ├─   止损：${entry_long - atr * 1.2:.2f}")
    print(f"   ├─   止盈：${entry_long + atr * 2.0:.2f}")
    print(f"   ├─ 跌破卖出：价格跌破 ${entry_short:.2f} 时做空")
    print(f"   ├─   止损：${entry_short + atr * 1.2:.2f}")
    print(f"   └─   止盈：${entry_short - atr * 2.0:.2f}")

print("\n" + "="*60)
print("🔄 建议每隔 30-60 分钟重新运行一次")
print("="*60)

# ============================================================
# 13. 关闭连接
# ============================================================
mt5.shutdown()
print("\n✅ 程序执行完毕！")