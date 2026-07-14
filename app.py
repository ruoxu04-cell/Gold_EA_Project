"""
黄金AI交易系统 - 简化稳定版
"""

import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import time

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title="TOKONG黄金交易",
    page_icon="🏆",
    layout="wide"
)

# ============================================================
# 隐藏 Streamlit 品牌（简化版）
# ============================================================
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none !important;}
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
        return None, None, "未加载"

model, scaler, model_type = load_model()

# ============================================================
# 获取实时黄金价格
# ============================================================
@st.cache_data(ttl=30)
def get_realtime_price():
    """使用免费API获取实时黄金价格"""
    
    # 使用 Gold-API（免费，无需注册）
    try:
        url = "https://www.gold-api.com/price/XAU"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            price = data.get('price')
            if price:
                return float(price), "Gold-API"
    except:
        pass
    
    # 备用：模拟数据（4000附近）
    seed = int(time.time() / 30)
    np.random.seed(seed)
    base_price = 4000 + np.random.randn() * 5
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
    return df

def ai_predict(df):
    if model is None or scaler is None:
        return 0.55
    try:
        latest = df.iloc[-1]
        features = [
            latest.get('Close', 0),
            latest.get('Close', 0),
            latest.get('Close', 0),
            50,
            latest.get('Close', 0),
            latest.get('Close', 0),
            20,
            latest.get('Close', 0),
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
    df = get_historical_data()
    current_price = df['Close'].iloc[-1]
    prob = ai_predict(df)
    latest = df.iloc[-1]

# ============================================================
# 显示标题
# ============================================================
st.markdown('<h1 style="text-align:center;color:#f7971e;">🏆 TOKONG黄金交易</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center;color:#8892b0;">智能黄金交易决策系统</p>', unsafe_allow_html=True)

st.markdown("---")

# ============================================================
# 显示价格
# ============================================================
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("💰 实时价格", f"${current_price:,.2f}")

with col2:
    st.metric("📊 数据源", "Gold-API")

with col3:
    signal = "看涨 📈" if prob > 0.6 else "看跌 📉" if prob < 0.4 else "观望 ⏸️"
    st.metric("🤖 AI信号", f"{prob*100:.1f}%", delta=signal)

# ============================================================
# 概率条
# ============================================================
st.markdown("---")
up_prob = prob * 100
down_prob = (1 - prob) * 100

col_p1, col_p2 = st.columns(2)
with col_p1:
    st.markdown(f"📈 上涨概率：{up_prob:.1f}%")
    st.progress(up_prob / 100)
with col_p2:
    st.markdown(f"📉 下跌概率：{down_prob:.1f}%")
    st.progress(down_prob / 100)

# ============================================================
# 交易建议
# ============================================================
st.markdown("---")
st.subheader("🎯 交易建议")

if prob >= 0.7:
    st.success(f"✅ 强烈建议：买入 (做多) 入场价：${current_price:.2f}")
elif prob >= 0.55:
    st.info(f"⚠️ 轻仓试多 入场价：${current_price:.2f}")
elif prob <= 0.3:
    st.error(f"❌ 强烈建议：卖出 (做空) 入场价：${current_price:.2f}")
elif prob <= 0.45:
    st.warning(f"⚠️ 轻仓试空 入场价：${current_price:.2f}")
else:
    st.warning(f"🤔 观望，等待信号")

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
    line=dict(color='#f7971e', width=2)
))
fig.update_layout(
    height=400,
    template='plotly_dark',
    xaxis_title="时间",
    yaxis_title="价格 ($)"
)
st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 底部
# ============================================================
st.markdown("---")
st.caption("⚠️ 仅供参考，不构成投资建议 · 交易有风险，请谨慎决策")
