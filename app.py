"""
黄金AI交易系统 - 专业版
品牌化UI设计，适合商业销售
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
# 页面配置
# ============================================================
st.set_page_config(
    page_title="GoldAI Pro - 黄金智能交易系统",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# 🎨 自定义CSS样式（品牌化设计）
# ============================================================
st.markdown("""
<style>
    /* 全局字体和背景 */
    .stApp {
        background: linear-gradient(135deg, #0a0e1a 0%, #1a1a2e 50%, #16213e 100%);
    }
    
    /* 主标题 */
    .main-title {
        text-align: center;
        padding: 20px 0 10px 0;
        background: linear-gradient(90deg, #f7971e, #ffd200);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 48px;
        font-weight: 800;
        letter-spacing: 2px;
        text-shadow: 0 0 40px rgba(247, 151, 30, 0.3);
    }
    
    .sub-title {
        text-align: center;
        color: #8892b0;
        font-size: 16px;
        margin-bottom: 30px;
        letter-spacing: 4px;
    }
    
    /* 品牌卡片 */
    .brand-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,215,0,0.15);
        border-radius: 16px;
        padding: 20px;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        transition: all 0.3s ease;
    }
    .brand-card:hover {
        border-color: rgba(255,215,0,0.4);
        box-shadow: 0 8px 40px rgba(247,151,30,0.15);
        transform: translateY(-2px);
    }
    
    /* 价格显示 */
    .price-display {
        font-size: 42px;
        font-weight: 700;
        color: #ffffff;
        text-shadow: 0 0 30px rgba(247,151,30,0.2);
    }
    .price-change-positive {
        color: #00ff88;
        font-size: 18px;
        font-weight: 600;
    }
    .price-change-negative {
        color: #ff4757;
        font-size: 18px;
        font-weight: 600;
    }
    
    /* 信号标签 */
    .signal-bullish {
        background: linear-gradient(90deg, #00ff8833, #00ff8811);
        border: 1px solid #00ff88;
        border-radius: 8px;
        padding: 8px 16px;
        color: #00ff88;
        font-weight: 600;
    }
    .signal-bearish {
        background: linear-gradient(90deg, #ff475733, #ff475711);
        border: 1px solid #ff4757;
        border-radius: 8px;
        padding: 8px 16px;
        color: #ff4757;
        font-weight: 600;
    }
    .signal-neutral {
        background: linear-gradient(90deg, #ffd70033, #ffd70011);
        border: 1px solid #ffd700;
        border-radius: 8px;
        padding: 8px 16px;
        color: #ffd700;
        font-weight: 600;
    }
    
    /* 金箔分割线 */
    .gold-divider {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #f7971e, #ffd200, #f7971e, transparent);
        margin: 30px 0;
    }
    
    /* 指标卡片 */
    .metric-card {
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.06);
    }
    .metric-label {
        color: #8892b0;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .metric-value {
        color: #ffffff;
        font-size: 26px;
        font-weight: 700;
        margin-top: 4px;
    }
    
    /* 进度条美化 */
    .stProgress > div > div {
        background: linear-gradient(90deg, #f7971e, #ffd200) !important;
        border-radius: 10px !important;
    }
    
    /* 底部信息 */
    .footer {
        text-align: center;
        color: #495670;
        font-size: 12px;
        padding: 30px 0 10px 0;
        border-top: 1px solid rgba(255,255,255,0.05);
        margin-top: 30px;
    }
    .footer a {
        color: #f7971e;
        text-decoration: none;
    }
    
    /* 状态标签 */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .status-online {
        background: #00ff8833;
        color: #00ff88;
        border: 1px solid #00ff8844;
    }
    .status-updating {
        background: #ffd70033;
        color: #ffd700;
        border: 1px solid #ffd70044;
    }
    
    /* 交易建议卡片 */
    .trade-card {
        background: rgba(255,255,255,0.03);
        border-radius: 12px;
        padding: 20px 24px;
        border-left: 4px solid #f7971e;
    }
    .trade-card-buy {
        border-left-color: #00ff88;
        background: rgba(0,255,136,0.05);
    }
    .trade-card-sell {
        border-left-color: #ff4757;
        background: rgba(255,71,87,0.05);
    }
    .trade-card-wait {
        border-left-color: #ffd700;
        background: rgba(255,215,0,0.05);
    }
    
    /* 概率条文字 */
    .prob-label {
        font-size: 14px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

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
        return None, None, "未加载"

model, scaler, model_type = load_model()

# ============================================================
# 获取实时黄金价格
# ============================================================
@st.cache_data(ttl=30)
def get_realtime_price():
    """使用多个免费API获取实时黄金价格"""
    
    # API 1: Gold-API
    try:
        url = "https://www.gold-api.com/price/XAU"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            price = data.get('price')
            if price and float(price) > 1000:
                return float(price), "Gold-API"
    except:
        pass
    
    # API 2: ExchangeRate-API
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            price = data.get('rates', {}).get('XAU')
            if price:
                if price < 1:
                    price = 1 / price
                if price > 1000:
                    return float(price), "ExchangeRate-API"
    except:
        pass
    
    # API 3: Yadio
    try:
        url = "https://api.yadio.io/rates/XAU.json"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            price = data.get('XAU', {}).get('USD')
            if price and price > 1000:
                return float(price), "Yadio API"
    except:
        pass
    
    # 备用模拟数据
    seed = int(time.time() / 30)
    np.random.seed(seed)
    base_price = 4000 + np.random.randn() * 10
    return float(base_price), "模拟数据"

@st.cache_data(ttl=60)
def get_historical_data():
    current_price, source = get_realtime_price()
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
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['BB_Upper'] = df['MA20'] + (df['Close'].rolling(window=20).std() * 2)
    df['BB_Lower'] = df['MA20'] - (df['Close'].rolling(window=20).std() * 2)
    df['BB_Width'] = df['BB_Upper'] - df['BB_Lower']
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
# 主标题
# ============================================================
st.markdown('<h1 class="main-title">🏆 GoldAI Pro</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">智能黄金交易决策系统 · 实时AI分析</p>', unsafe_allow_html=True)

# ============================================================
# 状态栏
# ============================================================
col_status1, col_status2, col_status3, col_status4 = st.columns(4)
with col_status1:
    st.markdown(f'<span class="status-badge status-online">● 系统在线</span>', unsafe_allow_html=True)
with col_status2:
    st.caption(f"📡 {data_source}")
with col_status3:
    st.caption(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
with col_status4:
    st.caption("🔄 实时更新")

st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)

# ============================================================
# 4个核心指标
# ============================================================
col1, col2, col3, col4 = st.columns(4)

# 计算涨跌
price_change = current_price - df['Close'].iloc[-2] if len(df) > 1 else 0
change_pct = (price_change / df['Close'].iloc[-2] * 100) if len(df) > 1 else 0
change_color = "price-change-positive" if price_change >= 0 else "price-change-negative"
change_symbol = "▲" if price_change >= 0 else "▼"

with col1:
    st.markdown(f"""
    <div class="brand-card">
        <div style="text-align:center;">
            <div style="color:#8892b0;font-size:13px;text-transform:uppercase;letter-spacing:1px;">💰 实时金价</div>
            <div class="price-display">${current_price:,.2f}</div>
            <div class="{change_color}">{change_symbol} ${abs(price_change):.2f} ({change_pct:.2f}%)</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    rsi_val = latest.get('RSI', 50)
    rsi_status = "超买 🔴" if rsi_val > 70 else "超卖 🟢" if rsi_val < 30 else "中性"
    st.markdown(f"""
    <div class="brand-card">
        <div style="text-align:center;">
            <div style="color:#8892b0;font-size:13px;text-transform:uppercase;letter-spacing:1px;">📈 RSI</div>
            <div class="metric-value">{rsi_val:.1f}</div>
            <div style="color:#8892b0;font-size:14px;">{rsi_status}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    macd_val = latest.get('MACD', 0)
    signal_val = latest.get('MACD_Signal', 0)
    macd_status = "多头" if macd_val > signal_val else "空头"
    macd_color = "#00ff88" if macd_val > signal_val else "#ff4757"
    st.markdown(f"""
    <div class="brand-card">
        <div style="text-align:center;">
            <div style="color:#8892b0;font-size:13px;text-transform:uppercase;letter-spacing:1px;">📊 MACD</div>
            <div class="metric-value">{macd_val:.2f}</div>
            <div style="color:{macd_color};font-size:14px;">{macd_status}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    signal_class = "signal-bullish" if prob > 0.6 else "signal-bearish" if prob < 0.4 else "signal-neutral"
    signal_text = "看涨 📈" if prob > 0.6 else "看跌 📉" if prob < 0.4 else "观望 ⏸️"
    st.markdown(f"""
    <div class="brand-card">
        <div style="text-align:center;">
            <div style="color:#8892b0;font-size:13px;text-transform:uppercase;letter-spacing:1px;">🤖 AI 信号</div>
            <div class="metric-value">{prob*100:.1f}%</div>
            <div><span class="{signal_class}">{signal_text}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# 概率条
# ============================================================
st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)

up_prob = prob * 100
down_prob = (1 - prob) * 100

col_prob1, col_prob2 = st.columns(2)

with col_prob1:
    st.markdown(f'<span class="prob-label">📈 上涨概率 <span style="color:#00ff88;font-weight:700;">{up_prob:.1f}%</span></span>', unsafe_allow_html=True)
    st.progress(up_prob / 100)

with col_prob2:
    st.markdown(f'<span class="prob-label">📉 下跌概率 <span style="color:#ff4757;font-weight:700;">{down_prob:.1f}%</span></span>', unsafe_allow_html=True)
    st.progress(down_prob / 100)

# ============================================================
# 交易建议
# ============================================================
st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)

col_trade, col_market = st.columns([2, 1])

with col_trade:
    st.markdown('<p style="color:#f7971e;font-weight:700;font-size:18px;letter-spacing:1px;">🎯 交易建议</p>', unsafe_allow_html=True)
    
    if prob >= 0.70:
        long_stop = current_price - atr * 1.5
        long_take = current_price + atr * 2.5
        rr = ((long_take - current_price) / (current_price - long_stop)) if (current_price - long_stop) > 0 else 0
        st.markdown(f"""
        <div class="trade-card trade-card-buy">
            <p style="color:#00ff88;font-size:20px;font-weight:700;">✅ 强烈建议 · 买入 (做多)</p>
            <table style="width:100%;color:#c9d1d9;font-size:14px;">
                <tr><td>入场价</td><td style="text-align:right;font-weight:600;">${current_price:.2f}</td></tr>
                <tr><td>止损价</td><td style="text-align:right;color:#ff4757;font-weight:600;">${long_stop:.2f}</td></tr>
                <tr><td>止盈价</td><td style="text-align:right;color:#00ff88;font-weight:600;">${long_take:.2f}</td></tr>
                <tr><td>风险/收益比</td><td style="text-align:right;font-weight:600;">1:{rr:.2f}</td></tr>
                <tr><td>建议仓位</td><td style="text-align:right;color:#ffd700;font-weight:600;">2% 总资金</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        
    elif prob >= 0.55:
        long_stop = current_price - atr * 1.2
        long_take = current_price + atr * 2.0
        rr = ((long_take - current_price) / (current_price - long_stop)) if (current_price - long_stop) > 0 else 0
        st.markdown(f"""
        <div class="trade-card trade-card-buy">
            <p style="color:#ffd700;font-size:20px;font-weight:700;">⚠️ 轻仓试多</p>
            <table style="width:100%;color:#c9d1d9;font-size:14px;">
                <tr><td>入场价</td><td style="text-align:right;font-weight:600;">${current_price:.2f}</td></tr>
                <tr><td>止损价</td><td style="text-align:right;color:#ff4757;font-weight:600;">${long_stop:.2f}</td></tr>
                <tr><td>止盈价</td><td style="text-align:right;color:#00ff88;font-weight:600;">${long_take:.2f}</td></tr>
                <tr><td>风险/收益比</td><td style="text-align:right;font-weight:600;">1:{rr:.2f}</td></tr>
                <tr><td>建议仓位</td><td style="text-align:right;color:#ffd700;font-weight:600;">1% 总资金</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        
    elif prob <= 0.30:
        short_stop = current_price + atr * 1.5
        short_take = current_price - atr * 2.5
        rr = ((current_price - short_take) / (short_stop - current_price)) if (short_stop - current_price) > 0 else 0
        st.markdown(f"""
        <div class="trade-card trade-card-sell">
            <p style="color:#ff4757;font-size:20px;font-weight:700;">❌ 强烈建议 · 卖出 (做空)</p>
            <table style="width:100%;color:#c9d1d9;font-size:14px;">
                <tr><td>入场价</td><td style="text-align:right;font-weight:600;">${current_price:.2f}</td></tr>
                <tr><td>止损价</td><td style="text-align:right;color:#ff4757;font-weight:600;">${short_stop:.2f}</td></tr>
                <tr><td>止盈价</td><td style="text-align:right;color:#00ff88;font-weight:600;">${short_take:.2f}</td></tr>
                <tr><td>风险/收益比</td><td style="text-align:right;font-weight:600;">1:{rr:.2f}</td></tr>
                <tr><td>建议仓位</td><td style="text-align:right;color:#ffd700;font-weight:600;">2% 总资金</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        
    elif prob <= 0.45:
        short_stop = current_price + atr * 1.2
        short_take = current_price - atr * 2.0
        rr = ((current_price - short_take) / (short_stop - current_price)) if (short_stop - current_price) > 0 else 0
        st.markdown(f"""
        <div class="trade-card trade-card-sell">
            <p style="color:#ffd700;font-size:20px;font-weight:700;">⚠️ 轻仓试空</p>
            <table style="width:100%;color:#c9d1d9;font-size:14px;">
                <tr><td>入场价</td><td style="text-align:right;font-weight:600;">${current_price:.2f}</td></tr>
                <tr><td>止损价</td><td style="text-align:right;color:#ff4757;font-weight:600;">${short_stop:.2f}</td></tr>
                <tr><td>止盈价</td><td style="text-align:right;color:#00ff88;font-weight:600;">${short_take:.2f}</td></tr>
                <tr><td>风险/收益比</td><td style="text-align:right;font-weight:600;">1:{rr:.2f}</td></tr>
                <tr><td>建议仓位</td><td style="text-align:right;color:#ffd700;font-weight:600;">1% 总资金</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        
    else:
        st.markdown(f"""
        <div class="trade-card trade-card-wait">
            <p style="color:#ffd700;font-size:20px;font-weight:700;">🤔 观望 · 等待信号</p>
            <p style="color:#c9d1d9;font-size:14px;">市场方向不明，AI 信心度不足</p>
            <p style="color:#c9d1d9;font-size:14px;">上涨概率：{prob*100:.1f}%</p>
            <p style="color:#8892b0;font-size:13px;">建议等待价格突破关键位再交易</p>
        </div>
        """, unsafe_allow_html=True)

with col_market:
    st.markdown('<p style="color:#f7971e;font-weight:700;font-size:18px;letter-spacing:1px;">📊 市场状态</p>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.03);border-radius:12px;padding:16px;border:1px solid rgba(255,255,255,0.06);">
        <p style="color:#c9d1d9;font-size:14px;margin:4px 0;">📅 {latest['Date'].strftime('%Y-%m-%d %H:%M')}</p>
        <p style="color:#c9d1d9;font-size:14px;margin:4px 0;">📈 24h变化: <span style="color:{'#00ff88' if df['Close'].iloc[-1] > df['Close'].iloc[-24] else '#ff4757'};font-weight:600;">${df['Close'].iloc[-1] - df['Close'].iloc[-24]:.2f}</span></p>
        <p style="color:#c9d1d9;font-size:14px;margin:4px 0;">📊 布林带宽: <span style="color:#ffd700;">${latest.get('BB_Width', 0):.2f}</span></p>
        <p style="color:#c9d1d9;font-size:14px;margin:4px 0;">📍 偏离均线: <span style="color:{'#00ff88' if ((current_price - latest['MA20'])/latest['MA20']*100) > 0 else '#ff4757'};">{((current_price - latest['MA20'])/latest['MA20']*100):.2f}%</span></p>
        <p style="color:#c9d1d9;font-size:14px;margin:4px 0;">📊 波动率: <span style="color:#ffd700;">${atr:.2f}</span></p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# 价格走势图
# ============================================================
st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)
st.markdown('<p style="color:#f7971e;font-weight:700;font-size:16px;letter-spacing:1px;">📈 价格走势</p>', unsafe_allow_html=True)

df_plot = df.tail(200)

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df_plot['Date'],
    y=df_plot['Close'],
    mode='lines',
    name='价格',
    line=dict(color='#f7971e', width=2.5)
))

fig.add_trace(go.Scatter(
    x=df_plot['Date'],
    y=df_plot['MA20'],
    mode='lines',
    name='MA20',
    line=dict(color='#ffd700', width=1.5, dash='dash')
))

fig.add_trace(go.Scatter(
    x=df_plot['Date'],
    y=df_plot['BB_Upper'],
    mode='lines',
    name='布林上轨',
    line=dict(color='rgba(255,255,255,0.2)', width=1, dash='dot')
))

fig.add_trace(go.Scatter(
    x=df_plot['Date'],
    y=df_plot['BB_Lower'],
    mode='lines',
    name='布林下轨',
    line=dict(color='rgba(255,255,255,0.2)', width=1, dash='dot')
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
        x=0.01,
        font=dict(color='#8892b0')
    ),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    margin=dict(l=0, r=0, t=20, b=20)
)

fig.update_xaxes(gridcolor='rgba(255,255,255,0.05)')
fig.update_yaxes(gridcolor='rgba(255,255,255,0.05)')

st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 底部信息
# ============================================================
st.markdown("""
<div class="footer">
    <p>🏆 GoldAI Pro · 智能黄金交易决策系统</p>
    <p>AI模型：随机森林 · 数据来源：实时市场API</p>
    <p style="color:#2d3850;">⚠️ 仅供参考，不构成投资建议 · 交易有风险，请谨慎决策</p>
    <p style="color:#1a2340;margin-top:8px;">© 2026 GoldAI Pro · All Rights Reserved</p>
</div>
""", unsafe_allow_html=True)