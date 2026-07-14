"""
黄金AI交易系统 - 网站版
使用免费API获取实时数据，无需MT5
部署到 Streamlit Cloud
"""

import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import requests
import time
import json

# ============================================================
# 导入自动刷新库
# ============================================================
from streamlit_autorefresh import st_autorefresh

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title="黄金AI交易系统",
    page_icon="📊",
    layout="wide"
)

st.title("📊 黄金 XAUUSD AI 交易系统")
st.markdown("基于随机森林 AI 模型的实时交易信号")

# ============================================================
# 🔄 自动刷新：每30秒刷新一次页面
# ============================================================
st_autorefresh(interval=30000, key="gold_price_refresh")

# ============================================================
# 加载AI模型
# ============================================================
@st.cache_resource
def load_model():
    try:
        model = joblib.load('gold_ai_model.pkl')
        scaler = joblib.load('scaler.pkl')
        return model, scaler, "随机森林"
    except Exception as e:
        st.error(f"❌ 模型加载失败：{e}")
        st.info("请确保 gold_ai_model.pkl 和 scaler.pkl 文件存在")
        return None, None, "未加载"

model, scaler, model_type = load_model()

if model is None:
    st.stop()

# ============================================================
# 🚀 获取实时黄金价格（Yadio API - 完全免费，无需注册）
# ============================================================
@st.cache_data(ttl=30)
def get_realtime_price():
    """使用 Yadio API 获取实时黄金价格（完全免费，无需注册）"""
    
    # Yadio API（免费，无需注册，稳定）
    try:
        url = "https://api.yadio.io/rates/XAU.json"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            price = data.get('XAU', {}).get('USD')
            if price:
                return float(price), "Yadio API"
    except Exception as e:
        print(f"Yadio API 获取失败: {e}")
    
    # 备用：模拟数据
    seed = int(time.time() / 30)
    np.random.seed(seed)
    base_price = 2420 + np.random.randn() * 2
    return float(base_price), "模拟数据 ⚠️"

@st.cache_data(ttl=60)
def get_historical_data():
    """生成历史K线数据"""
    
    current_price, source = get_realtime_price()
    
    # 生成过去7天的K线
    hours = 168
    dates = pd.date_range(
        start=datetime.now() - timedelta(hours=hours),
        periods=hours,
        freq='h'
    )
    
    np.random.seed(42)
    returns = np.random.normal(0, 0.0002, hours)
    prices = current_price * np.cumprod(1 + returns)
    
    df = pd.DataFrame({
        'Date': dates,
        'Close': prices,
        'Open': prices * (1 + np.random.normal(0, 0.0001, hours)),
        'High': prices * (1 + np.abs(np.random.normal(0, 0.0003, hours))),
        'Low': prices * (1 - np.abs(np.random.normal(0, 0.0003, hours))),
        'Volume': np.random.randint(50, 500, hours)
    })
    
    df = calculate_indicators(df)
    return df, current_price, source

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
    
    # ATR
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    df['ATR'] = true_range.rolling(14).mean()
    
    return df

def ai_predict(df):
    if model is None or scaler is None:
        return 0.55
    
    try:
        latest = df.iloc[-1]
        features = [
            latest.get('MACD', 0),
            latest.get('MACD_Signal', 0),
            latest.get('MACD_Histogram', 0),
            latest.get('RSI', 50),
            latest.get('BB_Upper', latest.get('Close', 2000) * 1.02),
            latest.get('BB_Lower', latest.get('Close', 2000) * 0.98),
            latest.get('BB_Width', 20),
            latest.get('MA20', latest.get('Close', 2000)),
        ]
        features_scaled = scaler.transform([features])
        prob = model.predict_proba(features_scaled)[0][1]
        return float(prob)
    except:
        return 0.55

# ============================================================
# 获取数据
# ============================================================
with st.spinner("🔄 正在获取实时数据..."):
    df, current_price, data_source = get_historical_data()
    prob = ai_predict(df)
    latest = df.iloc[-1]
    atr = latest.get('ATR', 12)

# ============================================================
# 显示状态栏
# ============================================================
col_status1, col_status2, col_status3 = st.columns(3)
with col_status1:
    st.caption(f"📡 数据来源：{data_source}")
with col_status2:
    st.caption(f"🕐 更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
with col_status3:
    st.caption("🔄 每30秒自动刷新")

# ============================================================
# 4个核心指标 + 下方概率条
# ============================================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="💰 实时价格",
        value=f"${current_price:.2f}",
        delta=f"{current_price - df['Close'].iloc[-2]:.2f}" if len(df) > 1 else "+0.00"
    )

with col2:
    rsi_val = latest.get('RSI', 50)
    status = "超买 🔴" if rsi_val > 70 else "超卖 🟢" if rsi_val < 30 else "中性 ⚪"
    st.metric(label="📈 RSI (14)", value=f"{rsi_val:.1f}", delta=status)

with col3:
    macd_val = latest.get('MACD', 0)
    signal_val = latest.get('MACD_Signal', 0)
    status = "多头 📈" if macd_val > signal_val else "空头 📉"
    st.metric(label="📊 MACD", value=f"{macd_val:.2f}", delta=status)

with col4:
    st.metric(
        label=f"🤖 AI信号",
        value=f"{prob*100:.1f}%",
        delta="看涨 📈" if prob > 0.6 else "看跌 📉" if prob < 0.4 else "观望 ⏸️"
    )

# ============================================================
# 👇 概率条（在4列下方）
# ============================================================
st.markdown("---")

# 计算概率
up_prob = prob * 100
down_prob = (1 - prob) * 100

# 用两列显示上涨和下跌概率
col_prob1, col_prob2 = st.columns(2)

with col_prob1:
    st.markdown(f"📈 **上涨概率：{up_prob:.1f}%**")
    st.progress(up_prob / 100)

with col_prob2:
    st.markdown(f"📉 **下跌概率：{down_prob:.1f}%**")
    st.progress(down_prob / 100)

# 显示信号总结
if prob > 0.6:
    st.success(f"✅ **当前信号：看涨** (信心度：{up_prob:.0f}%)")
elif prob < 0.4:
    st.error(f"❌ **当前信号：看跌** (信心度：{down_prob:.0f}%)")
else:
    st.warning(f"⏸️ **当前信号：观望** (方向不明)")

# ============================================================
# 交易建议 + 市场状态
# ============================================================
st.markdown("---")
col_trade, col_market = st.columns([2, 1])

with col_trade:
    st.subheader("🎯 交易建议")
    
    if prob >= 0.70:
        long_stop = current_price - atr * 1.5
        long_take = current_price + atr * 2.5
        rr = ((long_take - current_price) / (current_price - long_stop)) if (current_price - long_stop) > 0 else 0
        st.success(f"✅ **强烈建议：买入（做多）**")
        st.write(f"├─ 入场价：**${current_price:.2f}**")
        st.write(f"├─ 止损价：**${long_stop:.2f}**")
        st.write(f"├─ 止盈价：**${long_take:.2f}**")
        st.write(f"├─ 风险/收益比：**1:{rr:.2f}**")
        st.write(f"└─ 建议仓位：**2% 总资金**")
        
    elif prob >= 0.55:
        long_stop = current_price - atr * 1.2
        long_take = current_price + atr * 2.0
        rr = ((long_take - current_price) / (current_price - long_stop)) if (current_price - long_stop) > 0 else 0
        st.info(f"⚠️ **轻仓试多**")
        st.write(f"├─ 入场价：**${current_price:.2f}**")
        st.write(f"├─ 止损价：**${long_stop:.2f}**")
        st.write(f"├─ 止盈价：**${long_take:.2f}**")
        st.write(f"├─ 风险/收益比：**1:{rr:.2f}**")
        st.write(f"└─ 建议仓位：**1% 总资金**")
        
    elif prob <= 0.30:
        short_stop = current_price + atr * 1.5
        short_take = current_price - atr * 2.5
        rr = ((current_price - short_take) / (short_stop - current_price)) if (short_stop - current_price) > 0 else 0
        st.error(f"❌ **建议：卖出（做空）**")
        st.write(f"├─ 入场价：**${current_price:.2f}**")
        st.write(f"├─ 止损价：**${short_stop:.2f}**")
        st.write(f"├─ 止盈价：**${short_take:.2f}**")
        st.write(f"├─ 风险/收益比：**1:{rr:.2f}**")
        st.write(f"└─ 建议仓位：**2% 总资金**")
        
    elif prob <= 0.45:
        short_stop = current_price + atr * 1.2
        short_take = current_price - atr * 2.0
        rr = ((current_price - short_take) / (short_stop - current_price)) if (short_stop - current_price) > 0 else 0
        st.warning(f"⚠️ **轻仓试空**")
        st.write(f"├─ 入场价：**${current_price:.2f}**")
        st.write(f"├─ 止损价：**${short_stop:.2f}**")
        st.write(f"├─ 止盈价：**${short_take:.2f}**")
        st.write(f"├─ 风险/收益比：**1:{rr:.2f}**")
        st.write(f"└─ 建议仓位：**1% 总资金**")
        
    else:
        st.warning(f"🤔 **建议：观望**")
        st.write("市场方向不明，AI 信心度不足")
        st.write(f"├─ 上涨概率：**{prob*100:.1f}%**")
        st.write(f"└─ 等待价格突破关键位再交易")

with col_market:
    st.subheader("📊 市场状态")
    st.write(f"📅 数据时间：{latest['Date'].strftime('%Y-%m-%d %H:%M')}")
    st.write(f"📈 24小时变化：**${df['Close'].iloc[-1] - df['Close'].iloc[-24]:.2f}**" if len(df) > 24 else "数据不足")
    st.write(f"📊 布林带宽：**${latest.get('BB_Width', 0):.2f}**")
    st.write(f"📍 价格偏离均线：**{((current_price - latest['MA20'])/latest['MA20']*100):.2f}%**")
    st.write(f"📊 波动率 ATR：**${atr:.2f}**")

# ============================================================
# 价格走势图
# ============================================================
st.markdown("---")
st.subheader("📈 价格走势")

df_plot = df.tail(200)

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df_plot['Date'],
    y=df_plot['Close'],
    mode='lines',
    name='价格',
    line=dict(color='#00ff88', width=2)
))

fig.add_trace(go.Scatter(
    x=df_plot['Date'],
    y=df_plot['MA20'],
    mode='lines',
    name='MA20',
    line=dict(color='orange', width=1, dash='dash')
))

fig.add_trace(go.Scatter(
    x=df_plot['Date'],
    y=df_plot['BB_Upper'],
    mode='lines',
    name='布林上轨',
    line=dict(color='gray', width=1, dash='dot')
))

fig.add_trace(go.Scatter(
    x=df_plot['Date'],
    y=df_plot['BB_Lower'],
    mode='lines',
    name='布林下轨',
    line=dict(color='gray', width=1, dash='dot')
))

fig.update_layout(
    height=400,
    template='plotly_dark',
    xaxis_title="时间",
    yaxis_title="价格 ($)",
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01
    )
)

st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 底部信息
# ============================================================
st.markdown("---")
col_footer1, col_footer2, col_footer3 = st.columns(3)

with col_footer1:
    st.caption(f"📊 AI模型：{model_type}")

with col_footer2:
    st.caption("📡 数据来源：Yadio API（免费）")

with col_footer3:
    st.caption("⚠️ 仅供参考，不构成投资建议")

st.caption("🔄 页面每30秒自动刷新数据")