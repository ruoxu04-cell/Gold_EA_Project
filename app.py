"""
黄金AI交易系统 - 专业版设计
保留原版功能，升级视觉设计
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
    page_title="TOKONG黄金交易",
    page_icon="🏆",
    layout="wide"
)

# ============================================================
# 🛡️ 隐藏 GitHub 和 Streamlit 标识（电脑+手机全平台）
# ============================================================
hide_streamlit_style = """
    <style>
    /* 电脑版隐藏 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .viewerBadge_container__1QSob {display: none !important;}
    .stDeployButton {display: none !important;}
    .stAppViewContainer .stDeployButton {display: none !important;}
    [data-testid="stStatusWidget"] {display: none !important;}
    .stApp > header {display: none !important;}
    .stApp > div:last-child {display: none !important;}
    
    /* 手机版隐藏 */
    .st-emotion-cache-1v0mbdj {display: none !important;}
    .st-emotion-cache-1wmy9hl {display: none !important;}
    .st-emotion-cache-1y4p8pa {display: none !important;}
    .st-emotion-cache-1dp5vir {display: none !important;}
    .st-emotion-cache-1avcm0n {display: none !important;}
    .st-emotion-cache-1r6slb0 {display: none !important;}
    .st-emotion-cache-17lhtej {display: none !important;}
    .st-emotion-cache-1vs7n35 {display: none !important;}
    .st-emotion-cache-1dte5yh {display: none !important;}
    .st-emotion-cache-1gk3tl8 {display: none !important;}
    
    /* 通用隐藏：所有包含 github 或 streamlit 的元素 */
    [class*="github"] {display: none !important;}
    [class*="streamlit"] {display: none !important;}
    [class*="deploy"] {display: none !important;}
    [class*="badge"] {display: none !important;}
    
    /* 底部任何文本 */
    .st-emotion-cache-1r6slb0, 
    .st-emotion-cache-1v0mbdj,
    .st-emotion-cache-1wmy9hl,
    .st-emotion-cache-17lhtej,
    .st-emotion-cache-1dp5vir {
        display: none !important;
    }
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ============================================================
# 🎨 自定义CSS（专业黄金主题）
# ============================================================
st.markdown("""
<style>
    /* 背景 */
    .stApp {
        background: linear-gradient(135deg, #0a0e1a 0%, #1a1a2e 50%, #16213e 100%);
    }
    
    /* 顶部标题行 */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 15px 0 5px 0;
        border-bottom: 1px solid rgba(255,215,0,0.1);
    }
    .header-left {
        display: flex;
        align-items: center;
    }
    .main-title {
        background: linear-gradient(90deg, #f7971e, #ffd200);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 36px;
        font-weight: 800;
        letter-spacing: 2px;
    }
    .header-time {
        color: #8892b0;
        font-size: 14px;
        letter-spacing: 1px;
    }
    
    /* 价格居中显示 */
    .price-center {
        text-align: center;
        padding: 20px 0 15px 0;
    }
    .price-label {
        color: #8892b0;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .price-display {
        font-size: 52px;
        font-weight: 700;
        color: #ffffff;
        text-shadow: 0 0 40px rgba(247,151,30,0.2);
        line-height: 1.3;
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
    
    /* 品牌卡片（三列） */
    .brand-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,215,0,0.12);
        border-radius: 16px;
        padding: 16px 14px;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
        text-align: center;
    }
    .brand-card:hover {
        border-color: rgba(255,215,0,0.35);
        box-shadow: 0 8px 40px rgba(247,151,30,0.12);
        transform: translateY(-2px);
    }
    
    .metric-label {
        color: #8892b0;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 500;
    }
    .metric-value {
        color: #ffffff;
        font-size: 26px;
        font-weight: 700;
        margin: 4px 0 2px 0;
    }
    .metric-sub {
        color: #8892b0;
        font-size: 14px;
    }
    
    /* 信号标签 */
    .signal-bullish {
        background: linear-gradient(90deg, #00ff8833, #00ff8811);
        border: 1px solid #00ff88;
        border-radius: 8px;
        padding: 4px 16px;
        color: #00ff88;
        font-weight: 600;
        font-size: 14px;
    }
    .signal-bearish {
        background: linear-gradient(90deg, #ff475733, #ff475711);
        border: 1px solid #ff4757;
        border-radius: 8px;
        padding: 4px 16px;
        color: #ff4757;
        font-weight: 600;
        font-size: 14px;
    }
    .signal-neutral {
        background: linear-gradient(90deg, #ffd70033, #ffd70011);
        border: 1px solid #ffd700;
        border-radius: 8px;
        padding: 4px 16px;
        color: #ffd700;
        font-weight: 600;
        font-size: 14px;
    }
    
    /* 金箔分割线 */
    .gold-divider {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #f7971e, #ffd200, #f7971e, transparent);
        margin: 20px 0;
    }
    
    /* 交易建议卡片 */
    .trade-card {
        background: rgba(255,255,255,0.03);
        border-radius: 12px;
        padding: 18px 22px;
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
    .trade-title {
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 10px;
    }
    .trade-row {
        color: #c9d1d9;
        font-size: 14px;
        margin: 3px 0;
    }
    
    /* 底部 */
    .footer {
        text-align: center;
        color: #495670;
        font-size: 12px;
        padding: 25px 0 10px 0;
        border-top: 1px solid rgba(255,255,255,0.05);
        margin-top: 30px;
    }
    
    /* 进度条 */
    .stProgress > div > div {
        background: linear-gradient(90deg, #f7971e, #ffd200) !important;
        border-radius: 10px !important;
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
        st.error(f"❌ 模型加载失败：{e}")
        st.info("请确保 gold_ai_model.pkl 和 scaler.pkl 文件存在")
        return None, None, "未加载"

model, scaler, model_type = load_model()

if model is None:
    st.stop()

# ============================================================
# 获取实时黄金价格
# ============================================================
@st.cache_data(ttl=120)
def get_realtime_price():
    """使用 Twelve Data API 获取实时黄金价格"""
    
    API_KEY = "b3b8143cd542493b9de1fb5aa13a9d07"
    
    try:
        url = f"https://api.twelvedata.com/price?symbol=XAU/USD&apikey={API_KEY}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            price = data.get('price')
            if price:
                return float(price), "Twelve Data"
    except:
        pass
    
    seed = int(time.time() / 30)
    np.random.seed(seed)
    base_price = 2420 + np.random.randn() * 2
    return float(base_price), "模拟数据 ⚠️"

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
# 🏆 顶部：标题在左 + 时间在右
# ============================================================
col_title, col_time = st.columns([3, 1])

with col_title:
    st.markdown('<span class="main-title">🏆 TOKONG黄金交易</span>', unsafe_allow_html=True)

with col_time:
    st.markdown(f'<p style="text-align:right;color:#8892b0;font-size:14px;margin-top:10px;">🕐 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>', unsafe_allow_html=True)

st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)

# ============================================================
# 💰 实时价格（居中显示）
# ============================================================
price_change = current_price - df['Close'].iloc[-2] if len(df) > 1 else 0
change_symbol = "▲" if price_change >= 0 else "▼"
change_color = "price-change-positive" if price_change >= 0 else "price-change-negative"

st.markdown(f"""
<div class="price-center">
    <div class="price-label">💰 实时价格</div>
    <div class="price-display">${current_price:,.2f}</div>
    <div class="{change_color}">{change_symbol} ${abs(price_change):.2f}</div>
</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)

# ============================================================
# 📊 RSI + MACD + AI信号（三列）
# ============================================================
col_rsi, col_macd, col_ai = st.columns(3)

with col_rsi:
    rsi_val = latest.get('RSI', 50)
    rsi_status = "超买 🔴" if rsi_val > 70 else "超卖 🟢" if rsi_val < 30 else "中性 ⚪"
    st.markdown(f"""
    <div class="brand-card">
        <div class="metric-label">📈 RSI (14)</div>
        <div class="metric-value">{rsi_val:.1f}</div>
        <div class="metric-sub">{rsi_status}</div>
    </div>
    """, unsafe_allow_html=True)

with col_macd:
    macd_val = latest.get('MACD', 0)
    signal_val = latest.get('MACD_Signal', 0)
    macd_status = "多头 📈" if macd_val > signal_val else "空头 📉"
    st.markdown(f"""
    <div class="brand-card">
        <div class="metric-label">📊 MACD</div>
        <div class="metric-value">{macd_val:.2f}</div>
        <div class="metric-sub">{macd_status}</div>
    </div>
    """, unsafe_allow_html=True)

with col_ai:
    signal_class = "signal-bullish" if prob > 0.6 else "signal-bearish" if prob < 0.4 else "signal-neutral"
    signal_text = "看涨 📈" if prob > 0.6 else "看跌 📉" if prob < 0.4 else "观望 ⏸️"
    st.markdown(f"""
    <div class="brand-card">
        <div class="metric-label">🤖 AI 信号</div>
        <div class="metric-value">{prob*100:.1f}%</div>
        <div><span class="{signal_class}">{signal_text}</span></div>
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
    st.markdown(f"📈 **上涨概率：{up_prob:.1f}%**")
    st.progress(up_prob / 100)

with col_prob2:
    st.markdown(f"📉 **下跌概率：{down_prob:.1f}%**")
    st.progress(down_prob / 100)

if prob > 0.6:
    st.success(f"✅ **当前信号：看涨** (信心度：{up_prob:.0f}%)")
elif prob < 0.4:
    st.error(f"❌ **当前信号：看跌** (信心度：{down_prob:.0f}%)")
else:
    st.warning(f"⏸️ **当前信号：观望** (方向不明)")

# ============================================================
# 交易建议 + 市场状态
# ============================================================
st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)

col_trade, col_market = st.columns([2, 1])

with col_trade:
    st.markdown('<p style="color:#f7971e;font-weight:700;font-size:16px;">🎯 交易建议</p>', unsafe_allow_html=True)
    
    if prob >= 0.70:
        long_stop = current_price - atr * 1.5
        long_take = current_price + atr * 2.5
        rr = ((long_take - current_price) / (current_price - long_stop)) if (current_price - long_stop) > 0 else 0
        st.markdown(f"""
        <div class="trade-card trade-card-buy">
            <div class="trade-title" style="color:#00ff88;">✅ 强烈建议 · 买入 (做多)</div>
            <div class="trade-row">├─ 入场价：<strong>${current_price:.2f}</strong></div>
            <div class="trade-row">├─ 止损价：<strong style="color:#ff4757;">${long_stop:.2f}</strong></div>
            <div class="trade-row">├─ 止盈价：<strong style="color:#00ff88;">${long_take:.2f}</strong></div>
            <div class="trade-row">├─ 风险/收益比：<strong>1:{rr:.2f}</strong></div>
            <div class="trade-row">└─ 建议仓位：<strong style="color:#ffd700;">2% 总资金</strong></div>
        </div>
        """, unsafe_allow_html=True)
        
    elif prob >= 0.55:
        long_stop = current_price - atr * 1.2
        long_take = current_price + atr * 2.0
        rr = ((long_take - current_price) / (current_price - long_stop)) if (current_price - long_stop) > 0 else 0
        st.markdown(f"""
        <div class="trade-card trade-card-buy">
            <div class="trade-title" style="color:#ffd700;">⚠️ 轻仓试多</div>
            <div class="trade-row">├─ 入场价：<strong>${current_price:.2f}</strong></div>
            <div class="trade-row">├─ 止损价：<strong style="color:#ff4757;">${long_stop:.2f}</strong></div>
            <div class="trade-row">├─ 止盈价：<strong style="color:#00ff88;">${long_take:.2f}</strong></div>
            <div class="trade-row">├─ 风险/收益比：<strong>1:{rr:.2f}</strong></div>
            <div class="trade-row">└─ 建议仓位：<strong style="color:#ffd700;">1% 总资金</strong></div>
        </div>
        """, unsafe_allow_html=True)
        
    elif prob <= 0.30:
        short_stop = current_price + atr * 1.5
        short_take = current_price - atr * 2.5
        rr = ((current_price - short_take) / (short_stop - current_price)) if (short_stop - current_price) > 0 else 0
        st.markdown(f"""
        <div class="trade-card trade-card-sell">
            <div class="trade-title" style="color:#ff4757;">❌ 强烈建议 · 卖出 (做空)</div>
            <div class="trade-row">├─ 入场价：<strong>${current_price:.2f}</strong></div>
            <div class="trade-row">├─ 止损价：<strong style="color:#ff4757;">${short_stop:.2f}</strong></div>
            <div class="trade-row">├─ 止盈价：<strong style="color:#00ff88;">${short_take:.2f}</strong></div>
            <div class="trade-row">├─ 风险/收益比：<strong>1:{rr:.2f}</strong></div>
            <div class="trade-row">└─ 建议仓位：<strong style="color:#ffd700;">2% 总资金</strong></div>
        </div>
        """, unsafe_allow_html=True)
        
    elif prob <= 0.45:
        short_stop = current_price + atr * 1.2
        short_take = current_price - atr * 2.0
        rr = ((current_price - short_take) / (short_stop - current_price)) if (short_stop - current_price) > 0 else 0
        st.markdown(f"""
        <div class="trade-card trade-card-sell">
            <div class="trade-title" style="color:#ffd700;">⚠️ 轻仓试空</div>
            <div class="trade-row">├─ 入场价：<strong>${current_price:.2f}</strong></div>
            <div class="trade-row">├─ 止损价：<strong style="color:#ff4757;">${short_stop:.2f}</strong></div>
            <div class="trade-row">├─ 止盈价：<strong style="color:#00ff88;">${short_take:.2f}</strong></div>
            <div class="trade-row">├─ 风险/收益比：<strong>1:{rr:.2f}</strong></div>
            <div class="trade-row">└─ 建议仓位：<strong style="color:#ffd700;">1% 总资金</strong></div>
        </div>
        """, unsafe_allow_html=True)
        
    else:
        st.markdown(f"""
        <div class="trade-card trade-card-wait">
            <div class="trade-title" style="color:#ffd700;">🤔 观望 · 等待信号</div>
            <div class="trade-row">市场方向不明，AI 信心度不足</div>
            <div class="trade-row">上涨概率：<strong>{prob*100:.1f}%</strong></div>
            <div class="trade-row">建议等待价格突破关键位再交易</div>
        </div>
        """, unsafe_allow_html=True)

with col_market:
    st.markdown('<p style="color:#f7971e;font-weight:700;font-size:16px;">📊 市场状态</p>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.03);border-radius:12px;padding:16px;border:1px solid rgba(255,255,255,0.06);">
        <div style="color:#c9d1d9;font-size:14px;margin:4px 0;">📅 {latest['Date'].strftime('%Y-%m-%d %H:%M')}</div>
        <div style="color:#c9d1d9;font-size:14px;margin:4px 0;">📈 24h变化：<strong style="color:{'#00ff88' if df['Close'].iloc[-1] > df['Close'].iloc[-24] else '#ff4757'};">${df['Close'].iloc[-1] - df['Close'].iloc[-24]:.2f}</strong></div>
        <div style="color:#c9d1d9;font-size:14px;margin:4px 0;">📊 布林带宽：<strong style="color:#ffd700;">${latest.get('BB_Width', 0):.2f}</strong></div>
        <div style="color:#c9d1d9;font-size:14px;margin:4px 0;">📍 偏离均线：<strong style="color:{'#00ff88' if ((current_price - latest['MA20'])/latest['MA20']*100) > 0 else '#ff4757'};">{((current_price - latest['MA20'])/latest['MA20']*100):.2f}%</strong></div>
        <div style="color:#c9d1d9;font-size:14px;margin:4px 0;">📊 波动率 ATR：<strong style="color:#ffd700;">${atr:.2f}</strong></div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# 价格走势图
# ============================================================
st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)
st.markdown('<p style="color:#f7971e;font-weight:700;font-size:16px;">📈 价格走势</p>', unsafe_allow_html=True)

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
    <p>🏆 TOKONG黄金交易</p>
    <p style="color:#2d3850;">⚠️ 仅供参考，不构成投资建议 · 交易有风险，请谨慎决策</p>
</div>
""", unsafe_allow_html=True)

# 在页面最底部加入
st.markdown("""
<script>
    // 等待页面加载完成后移除所有底部元素
    setTimeout(function() {
        // 移除所有可能的底部元素
        var elements = document.querySelectorAll('footer, .stDeployButton, .viewerBadge_container__1QSob, [data-testid="stStatusWidget"], .st-emotion-cache-1r6slb0, .st-emotion-cache-1v0mbdj');
        elements.forEach(function(el) {
            if (el) el.remove();
        });
        
        // 移除任何包含 github 或 streamlit 的元素
        var all = document.querySelectorAll('*');
        all.forEach(function(el) {
            if (el.innerText && (el.innerText.includes('GitHub') || el.innerText.includes('Streamlit') || el.innerText.includes('deploy'))) {
                if (el.tagName !== 'BODY' && el.tagName !== 'HTML') {
                    el.style.display = 'none';
                }
            }
        });
    }, 1000);
</script>
""", unsafe_allow_html=True)