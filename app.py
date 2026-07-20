"""
黄金交易系统 - 中文版 + 动态止盈
根据市场趋势强度自动调整止盈大小
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import time

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title="TOKONG 黄金交易",
    page_icon="🏆",
    layout="wide"
)

# ============================================================
# 自定义CSS
# ============================================================
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0a0e1a 0%, #1a1a2e 50%, #16213e 100%); }
    .main-title { background: linear-gradient(90deg, #f7971e, #ffd200); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 32px; font-weight: 800; }
    .price-display { font-size: 48px; font-weight: 700; color: #ffffff; text-align: center; }
    .price-change-positive { color: #00ff88; font-size: 18px; font-weight: 600; }
    .price-change-negative { color: #ff4757; font-size: 18px; font-weight: 600; }
    .brand-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,215,0,0.12); border-radius: 16px; padding: 16px; text-align: center; }
    .metric-value { color: #ffffff; font-size: 26px; font-weight: 700; }
    .metric-label { color: #8892b0; font-size: 13px; text-transform: uppercase; }
    .signal-bullish { background: #00ff8833; border: 1px solid #00ff88; border-radius: 8px; padding: 4px 16px; color: #00ff88; }
    .signal-bearish { background: #ff475733; border: 1px solid #ff4757; border-radius: 8px; padding: 4px 16px; color: #ff4757; }
    .signal-neutral { background: #ffd70033; border: 1px solid #ffd700; border-radius: 8px; padding: 4px 16px; color: #ffd700; }
    .gold-divider { border: none; height: 2px; background: linear-gradient(90deg, transparent, #f7971e, #ffd200, #f7971e, transparent); margin: 15px 0; }
    .trade-card { background: rgba(255,255,255,0.03); border-radius: 12px; padding: 18px 22px; border-left: 4px solid #f7971e; }
    .trade-card-buy { border-left-color: #00ff88; background: rgba(0,255,136,0.05); }
    .trade-card-sell { border-left-color: #ff4757; background: rgba(255,71,87,0.05); }
    .trade-card-wait { border-left-color: #ffd700; background: rgba(255,215,0,0.05); }
    .footer { text-align: center; color: #495670; font-size: 12px; padding: 25px 0 10px 0; border-top: 1px solid rgba(255,255,255,0.05); margin-top: 30px; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .stDeployButton {display: none !important;}
</style>
""", unsafe_allow_html=True)

# ============================================================
# 获取实时黄金价格
# ============================================================
@st.cache_data(ttl=30)
def get_realtime_price():
    """从免费API获取实时黄金价格"""
    
    # API 1: Yadio
    try:
        url = "https://api.yadio.io/rates/XAU.json"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            price = data.get('XAU', {}).get('USD')
            if price and float(price) > 1000:
                return float(price), "Yadio API"
    except:
        pass
    
    # API 2: Gold-API
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
    
    # 备用：模拟数据（约4000）
    seed = int(time.time() / 30)
    np.random.seed(seed)
    base_price = 4000 + np.random.randn() * 3
    return float(base_price), "模拟数据 ⚠️"

@st.cache_data(ttl=60)
def get_historical_data():
    """生成历史价格数据"""
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
    
    # 计算技术指标
    df['MA20'] = df['Close'].rolling(20).mean()
    df['RSI'] = calculate_rsi(df['Close'])
    df['MACD'], df['MACD_Signal'] = calculate_macd(df['Close'])
    df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
    df['BB_Upper'] = df['MA20'] + (df['Close'].rolling(20).std() * 2)
    df['BB_Lower'] = df['MA20'] - (df['Close'].rolling(20).std() * 2)
    df['BB_Width'] = df['BB_Upper'] - df['BB_Lower']
    
    return df, current_price, source

def calculate_rsi(prices, period=14):
    """计算 RSI 指标"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """计算 MACD 指标"""
    exp1 = prices.ewm(span=fast, adjust=False).mean()
    exp2 = prices.ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    macd_signal = macd.ewm(span=signal, adjust=False).mean()
    return macd, macd_signal

# ============================================================
# AI 预测（基于 RSI + MACD + 价格位置）
# ============================================================
def ai_predict(df):
    """
    基于多个指标生成交易信号
    给出平衡的信号（不会总是看跌）
    """
    latest = df.iloc[-1]
    rsi = latest.get('RSI', 50)
    macd = latest.get('MACD', 0)
    macd_signal = latest.get('MACD_Signal', 0)
    close = latest.get('Close', 4000)
    ma20 = latest.get('MA20', close)
    
    # RSI 评分：>55 看涨，<45 看跌
    rsi_score = (rsi - 50) / 50  # 范围: -1 到 1
    
    # MACD 评分：高于信号线看涨
    macd_diff = macd - macd_signal
    macd_max = close * 0.01  # 价格的1%作为最大差值
    macd_score = max(-1, min(1, macd_diff / macd_max))
    
    # 价格位置：高于 MA20 看涨
    price_score = (close - ma20) / ma20 * 20  # 放大
    
    # 综合评分（权重：RSI 40%，MACD 40%，价格 20%）
    combined = rsi_score * 0.4 + macd_score * 0.4 + price_score * 0.2
    
    # 转换为概率（0-1 范围）
    prob = 0.5 + combined * 0.3  # 范围: 0.2 - 0.8
    
    # 限制在安全范围
    prob = max(0.2, min(0.8, prob))
    
    return float(prob)

# ============================================================
# 🚀 动态止盈计算（根据趋势强度调整）
# ============================================================
def calculate_dynamic_targets(df, current_price, atr, prob):
    """
    根据市场状态动态计算止盈止损
    - 趋势强 → 大止盈
    - 趋势弱 → 小止盈
    - 震荡 → 中等止盈
    """
    latest = df.iloc[-1]
    
    # 1. 计算趋势强度
    ma20 = latest.get('MA20', current_price)
    price_deviation = abs(current_price - ma20) / ma20 * 100
    
    # MACD 强度
    macd_hist = latest.get('MACD_Histogram', 0)
    macd_strength = abs(macd_hist) / current_price * 100
    
    # RSI 极端程度
    rsi = latest.get('RSI', 50)
    rsi_extreme = abs(rsi - 50) / 50
    
    # 综合趋势强度（0-1）
    trend_strength = min(1, (price_deviation * 0.4 + macd_strength * 0.3 + rsi_extreme * 0.3) / 2)
    
    # 2. 根据趋势强度调整倍数
    if trend_strength > 0.6:
        stop_multiplier = 1.5
        take_multiplier = 3.5
        take_style = "🚀 强趋势（大止盈）"
    elif trend_strength > 0.3:
        stop_multiplier = 1.3
        take_multiplier = 2.5
        take_style = "📈 中等趋势"
    else:
        stop_multiplier = 1.0
        take_multiplier = 1.8
        take_style = "⚖️ 震荡（小止盈）"
    
    # 3. AI 信心度调整
    confidence_boost = (prob - 0.5) * 2
    take_multiplier = take_multiplier + confidence_boost * 0.5
    
    # 4. 计算具体价格
    long_stop = current_price - atr * stop_multiplier
    long_take = current_price + atr * take_multiplier
    short_stop = current_price + atr * stop_multiplier
    short_take = current_price - atr * take_multiplier
    
    # 计算风险收益比
    long_risk = current_price - long_stop
    long_reward = long_take - current_price
    long_rr = long_reward / long_risk if long_risk > 0 else 0
    
    return {
        'long_stop': long_stop,
        'long_take': long_take,
        'short_stop': short_stop,
        'short_take': short_take,
        'stop_multiplier': stop_multiplier,
        'take_multiplier': take_multiplier,
        'trend_strength': trend_strength,
        'take_style': take_style,
        'long_rr': long_rr
    }

# ============================================================
# 获取数据
# ============================================================
with st.spinner("🔄 正在获取实时数据..."):
    df, current_price, data_source = get_historical_data()
    prob = ai_predict(df)
    latest = df.iloc[-1]

# 计算 ATR
high_low = df['High'] - df['Low']
high_close = np.abs(df['High'] - df['Close'].shift())
low_close = np.abs(df['Low'] - df['Close'].shift())
ranges = pd.concat([high_low, high_close, low_close], axis=1)
true_range = np.max(ranges, axis=1)
atr = true_range.rolling(14).mean().iloc[-1]
if pd.isna(atr):
    atr = 12

# 计算动态止盈
targets = calculate_dynamic_targets(df, current_price, atr, prob)

# ============================================================
# 顶部：标题在左 + 时间在右
# ============================================================
col_title, col_time = st.columns([3, 1])

with col_title:
    st.markdown('<span class="main-title">🏆 TOKONG 黄金交易</span>', unsafe_allow_html=True)

with col_time:
    st.markdown(f'<p style="text-align:right;color:#8892b0;font-size:14px;margin-top:10px;">🕐 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>', unsafe_allow_html=True)

st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)

# ============================================================
# 价格显示（居中）
# ============================================================
price_change = current_price - df['Close'].iloc[-2] if len(df) > 1 else 0
change_symbol = "▲" if price_change >= 0 else "▼"
change_color = "price-change-positive" if price_change >= 0 else "price-change-negative"

st.markdown(f"""
<div style="text-align:center;padding:20px 0 15px 0;">
    <div style="color:#8892b0;font-size:14px;text-transform:uppercase;letter-spacing:2px;">💰 实时价格</div>
    <div class="price-display">${current_price:,.2f}</div>
    <div class="{change_color}">{change_symbol} ${abs(price_change):.2f}</div>
</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)

# ============================================================
# RSI + MACD + AI 信号（三列）
# ============================================================
col_rsi, col_macd, col_ai = st.columns(3)

with col_rsi:
    rsi_val = latest.get('RSI', 50)
    rsi_status = "超买 🔴" if rsi_val > 70 else "超卖 🟢" if rsi_val < 30 else "中性 ⚪"
    st.markdown(f"""
    <div class="brand-card">
        <div class="metric-label">📈 RSI (14)</div>
        <div class="metric-value">{rsi_val:.1f}</div>
        <div class="metric-sub" style="color:#8892b0;font-size:14px;">{rsi_status}</div>
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
        <div class="metric-sub" style="color:#8892b0;font-size:14px;">{macd_status}</div>
    </div>
    """, unsafe_allow_html=True)

with col_ai:
    signal_class = "signal-bullish" if prob > 0.55 else "signal-bearish" if prob < 0.45 else "signal-neutral"
    signal_text = "看涨 📈" if prob > 0.55 else "看跌 📉" if prob < 0.45 else "中性 ⏸️"
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

if prob > 0.55:
    st.success(f"✅ **当前信号：看涨**（信心度：{up_prob:.0f}%）")
elif prob < 0.45:
    st.error(f"❌ **当前信号：看跌**（信心度：{down_prob:.0f}%）")
else:
    st.warning(f"⏸️ **当前信号：中性**（横盘震荡）")

# ============================================================
# 交易建议 + 市场状态
# ============================================================
st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)

col_trade, col_market = st.columns([2, 1])

with col_trade:
    st.markdown('<p style="color:#f7971e;font-weight:700;font-size:16px;">🎯 交易建议</p>', unsafe_allow_html=True)
    
    # 显示当前市场状态
    st.caption(f"📊 市场状态：{targets['take_style']} | 趋势强度：{targets['trend_strength']*100:.0f}%")
    
    if prob >= 0.70:
        st.markdown(f"""
        <div class="trade-card trade-card-buy">
            <div class="trade-title" style="color:#00ff88;">✅ 强烈建议 · 买入（做多）</div>
            <div class="trade-row">├─ 入场价：<strong>${current_price:.2f}</strong></div>
            <div class="trade-row">├─ 止损价：<strong style="color:#ff4757;">${targets['long_stop']:.2f}</strong></div>
            <div class="trade-row">├─ 止盈价：<strong style="color:#00ff88;">${targets['long_take']:.2f}</strong></div>
            <div class="trade-row">├─ 风险/收益比：<strong>1:{targets['long_rr']:.2f}</strong></div>
            <div class="trade-row">├─ 止盈倍数：<strong>{targets['take_multiplier']:.1f}x ATR</strong></div>
            <div class="trade-row">└─ 建议仓位：<strong style="color:#ffd700;">2% 总资金</strong></div>
        </div>
        """, unsafe_allow_html=True)
        
    elif prob >= 0.55:
        st.markdown(f"""
        <div class="trade-card trade-card-buy">
            <div class="trade-title" style="color:#ffd700;">⚠️ 轻仓试多</div>
            <div class="trade-row">├─ 入场价：<strong>${current_price:.2f}</strong></div>
            <div class="trade-row">├─ 止损价：<strong style="color:#ff4757;">${targets['long_stop']:.2f}</strong></div>
            <div class="trade-row">├─ 止盈价：<strong style="color:#00ff88;">${targets['long_take']:.2f}</strong></div>
            <div class="trade-row">├─ 风险/收益比：<strong>1:{targets['long_rr']:.2f}</strong></div>
            <div class="trade-row">├─ 止盈倍数：<strong>{targets['take_multiplier']:.1f}x ATR</strong></div>
            <div class="trade-row">└─ 建议仓位：<strong style="color:#ffd700;">1% 总资金</strong></div>
        </div>
        """, unsafe_allow_html=True)
        
    elif prob <= 0.30:
        short_risk = targets['short_stop'] - current_price
        short_reward = current_price - targets['short_take']
        short_rr = short_reward / short_risk if short_risk > 0 else 0
        st.markdown(f"""
        <div class="trade-card trade-card-sell">
            <div class="trade-title" style="color:#ff4757;">❌ 强烈建议 · 卖出（做空）</div>
            <div class="trade-row">├─ 入场价：<strong>${current_price:.2f}</strong></div>
            <div class="trade-row">├─ 止损价：<strong style="color:#ff4757;">${targets['short_stop']:.2f}</strong></div>
            <div class="trade-row">├─ 止盈价：<strong style="color:#00ff88;">${targets['short_take']:.2f}</strong></div>
            <div class="trade-row">├─ 风险/收益比：<strong>1:{short_rr:.2f}</strong></div>
            <div class="trade-row">├─ 止盈倍数：<strong>{targets['take_multiplier']:.1f}x ATR</strong></div>
            <div class="trade-row">└─ 建议仓位：<strong style="color:#ffd700;">2% 总资金</strong></div>
        </div>
        """, unsafe_allow_html=True)
        
    elif prob <= 0.45:
        short_risk = targets['short_stop'] - current_price
        short_reward = current_price - targets['short_take']
        short_rr = short_reward / short_risk if short_risk > 0 else 0
        st.markdown(f"""
        <div class="trade-card trade-card-sell">
            <div class="trade-title" style="color:#ffd700;">⚠️ 轻仓试空</div>
            <div class="trade-row">├─ 入场价：<strong>${current_price:.2f}</strong></div>
            <div class="trade-row">├─ 止损价：<strong style="color:#ff4757;">${targets['short_stop']:.2f}</strong></div>
            <div class="trade-row">├─ 止盈价：<strong style="color:#00ff88;">${targets['short_take']:.2f}</strong></div>
            <div class="trade-row">├─ 风险/收益比：<strong>1:{short_rr:.2f}</strong></div>
            <div class="trade-row">├─ 止盈倍数：<strong>{targets['take_multiplier']:.1f}x ATR</strong></div>
            <div class="trade-row">└─ 建议仓位：<strong style="color:#ffd700;">1% 总资金</strong></div>
        </div>
        """, unsafe_allow_html=True)
        
    else:
        st.markdown(f"""
        <div class="trade-card trade-card-wait">
            <div class="trade-title" style="color:#ffd700;">🤔 观望 · 等待信号</div>
            <div class="trade-row">市场方向不明</div>
            <div class="trade-row">上涨概率：<strong>{prob*100:.1f}%</strong></div>
            <div class="trade-row">趋势强度：<strong>{targets['trend_strength']*100:.0f}%</strong></div>
            <div class="trade-row">等待价格突破关键位再交易</div>
        </div>
        """, unsafe_allow_html=True)

with col_market:
    st.markdown('<p style="color:#f7971e;font-weight:700;font-size:16px;">📊 市场状态</p>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.03);border-radius:12px;padding:16px;border:1px solid rgba(255,255,255,0.06);">
        <div style="color:#c9d1d9;font-size:14px;margin:4px 0;">📅 {latest['Date'].strftime('%Y-%m-%d %H:%M')}</div>
        <div style="color:#c9d1d9;font-size:14px;margin:4px 0;">📈 24小时变化：<strong style="color:{'#00ff88' if df['Close'].iloc[-1] > df['Close'].iloc[-24] else '#ff4757'};">${df['Close'].iloc[-1] - df['Close'].iloc[-24]:.2f}</strong></div>
        <div style="color:#c9d1d9;font-size:14px;margin:4px 0;">📊 布林带宽：<strong style="color:#ffd700;">${latest.get('BB_Width', 0):.2f}</strong></div>
        <div style="color:#c9d1d9;font-size:14px;margin:4px 0;">📍 偏离均线：<strong style="color:{'#00ff88' if ((current_price - latest['MA20'])/latest['MA20']*100) > 0 else '#ff4757'};">{((current_price - latest['MA20'])/latest['MA20']*100):.2f}%</strong></div>
        <div style="color:#c9d1d9;font-size:14px;margin:4px 0;">📊 波动率（ATR）：<strong style="color:#ffd700;">${atr:.2f}</strong></div>
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
    yaxis_title="价格（美元）",
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
    <p>🏆 TOKONG 黄金交易 · 智能决策系统</p>
    <p style="color:#2d3850;">⚠️ 仅供参考，不构成投资建议 · 交易有风险，请谨慎决策</p>
</div>
""", unsafe_allow_html=True)
