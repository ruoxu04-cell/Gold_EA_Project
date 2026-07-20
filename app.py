import time
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

st.set_page_config(page_title="TOKONG 黄金交易", page_icon="🏆", layout="wide")

# 在这里粘贴你的新 Twelve Data API Key
TWELVE_DATA_API_KEY = "b3b8143cd542493b9de1fb5aa13a9d07"

st.markdown("""
<style>
.stApp {background:linear-gradient(135deg,#0a0e1a,#1a1a2e,#16213e);}
.main-title {color:#ffd200;font-size:32px;font-weight:800;}
.price {font-size:48px;font-weight:700;color:#fff;text-align:center;}
.card {background:rgba(255,255,255,.04);border:1px solid rgba(255,215,0,.15);
border-radius:16px;padding:16px;text-align:center;}
.trade {background:rgba(255,255,255,.04);border-left:4px solid #ffd200;
border-radius:10px;padding:18px;line-height:1.9;}
.green {color:#00ff88;} .red {color:#ff4757;} .gold {color:#ffd200;}
.divider {border:none;height:2px;background:linear-gradient(90deg,transparent,#ffd200,transparent);}
</style>
""", unsafe_allow_html=True)


def demo_data():
    """没有行情时只显示演示数据，不会显示交易建议。"""
    rng = np.random.default_rng(42)
    dates = pd.date_range(
        end=datetime.now(timezone.utc), periods=200, freq="h"
    )
    close = 2350 * np.exp(np.cumsum(rng.normal(0, 0.0015, 200)))
    spread = close * rng.uniform(0.0004, 0.0015, 200)

    return pd.DataFrame({
        "Open": np.r_[close[0], close[:-1]],
        "High": close + spread,
        "Low": close - spread,
        "Close": close,
    }, index=dates)


@st.cache_data(ttl=60)
def get_price_data(api_key):
    try:
        response = requests.get(
            "https://api.twelvedata.com/time_series",
            params={
                "symbol": "XAU/USD",
                "interval": "1h",
                "outputsize": 200,
                "apikey": api_key,
            },
            timeout=12,
        )
        response.raise_for_status()
        values = response.json().get("values", [])

        if not values:
            raise ValueError("没有收到行情数据")

        df = pd.DataFrame(values).rename(columns=str.title)
        df["Datetime"] = pd.to_datetime(df["Datetime"], utc=True)
        df = df.set_index("Datetime").sort_index()

        for column in ["Open", "High", "Low", "Close"]:
            df[column] = pd.to_numeric(df[column], errors="coerce")

        df = df.dropna()

        if len(df) < 50:
            raise ValueError("行情数据不足")

        return df, "Twelve Data · XAU/USD 1小时K线", False

    except Exception as error:
        return demo_data(), f"演示数据：{error}", True


def add_indicators(df):
    df = df.copy()

    df["MA20"] = df["Close"].rolling(20).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0).ewm(
        alpha=1 / 14, adjust=False, min_periods=14
    ).mean()
    loss = (-delta.clip(upper=0)).ewm(
        alpha=1 / 14, adjust=False, min_periods=14
    ).mean()

    df["RSI"] = 100 - (100 / (1 + gain / loss.replace(0, np.nan)))

    ema_fast = df["Close"].ewm(span=12, adjust=False).mean()
    ema_slow = df["Close"].ewm(span=26, adjust=False).mean()

    df["MACD"] = ema_fast - ema_slow
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

    std = df["Close"].rolling(20).std()
    df["BB_Upper"] = df["MA20"] + std * 2
    df["BB_Lower"] = df["MA20"] - std * 2

    previous_close = df["Close"].shift()
    true_range = pd.concat([
        df["High"] - df["Low"],
        (df["High"] - previous_close).abs(),
        (df["Low"] - previous_close).abs(),
    ], axis=1).max(axis=1)

    df["ATR"] = true_range.ewm(
        alpha=1 / 14, adjust=False, min_periods=14
    ).mean()

    return df.dropna()


def get_signal(df, minimum_score):
    latest = df.iloc[-1]
    score = 0
    reasons = []

    if latest["Close"] > latest["MA20"]:
        score += 1
        reasons.append("价格在 MA20 上方")
    else:
        score -= 1
        reasons.append("价格在 MA20 下方")

    if latest["MACD"] > latest["MACD_Signal"]:
        score += 1
        reasons.append("MACD 偏多")
    else:
        score -= 1
        reasons.append("MACD 偏空")

    if latest["RSI"] >= 55:
        score += 1
        reasons.append("RSI 偏强")
    elif latest["RSI"] <= 45:
        score -= 1
        reasons.append("RSI 偏弱")
    else:
        reasons.append("RSI 中性")

    confidence = 50 + abs(score) / 3 * 35
    probability = 0.5 + score / 3 * 0.35

    if abs(score) < 2 or confidence < minimum_score:
        return "观望", 0.5, confidence, reasons

    if score > 0:
        return "偏多", probability, confidence, reasons

    return "偏空", probability, confidence, reasons


def trade_levels(price, atr, direction):
    stop_distance = atr * 1.5
    target_distance = stop_distance * 2

    if direction == "偏多":
        return price - stop_distance, price + target_distance

    return price + stop_distance, price - target_distance


with st.sidebar:
    st.header("⚙️ 风险设置")
    minimum_score = st.slider("最低规则评分", 60, 85, 70)
    account_size = st.number_input(
        "账户资金（美元）", min_value=0.0, value=10000.0, step=500.0
    )
    risk_percent = st.slider("每笔最大风险 (%)", 0.25, 2.0, 1.0, 0.25)

    if st.button("🔄 刷新行情", use_container_width=True):
        get_price_data.clear()
        st.rerun()


with st.spinner("正在获取黄金行情…"):
    raw_df, data_source, is_demo = get_price_data(TWELVE_DATA_API_KEY)
    df = add_indicators(raw_df)

if df.empty:
    st.error("数据不足，暂时无法计算。")
    st.stop()

latest = df.iloc[-1]
price = float(latest["Close"])
price_change = price - float(df["Close"].iloc[-2])

direction, probability, confidence, reasons = get_signal(
    df, minimum_score
)

st.markdown('<div class="main-title">🏆 TOKONG 黄金交易</div>',
            unsafe_allow_html=True)
st.caption(
    f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  |  {data_source}"
)

if is_demo:
    st.warning("⚠️ 当前是演示数据，不应作为真实交易依据。")

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

color = "#00ff88" if price_change >= 0 else "#ff4757"
arrow = "▲" if price_change >= 0 else "▼"

st.markdown(f"""
<div style="text-align:center;padding:20px;">
    <div style="color:#8892b0;">💰 XAU/USD 最近收盘价</div>
    <div class="price">${price:,.2f}</div>
    <div style="color:{color};font-size:18px;">{arrow} ${abs(price_change):.2f}</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    rsi_status = "超买 🔴" if latest["RSI"] > 70 else \
                 "超卖 🟢" if latest["RSI"] < 30 else "中性 ⚪"
    st.markdown(f"""
    <div class="card">
        <div>📈 RSI (14)</div>
        <h2>{latest["RSI"]:.1f}</h2>
        <div>{rsi_status}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    macd_status = "多头 📈" if latest["MACD"] > latest["MACD_Signal"] \
                  else "空头 📉"
    st.markdown(f"""
    <div class="card">
        <div>📊 MACD</div>
        <h2>{latest["MACD"]:.2f}</h2>
        <div>{macd_status}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    signal_color = "#00ff88" if direction == "偏多" else \
                   "#ff4757" if direction == "偏空" else "#ffd200"
    st.markdown(f"""
    <div class="card">
        <div>🤖 规则评分</div>
        <h2>{confidence:.0f}%</h2>
        <div style="color:{signal_color};">{direction}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

up_probability = probability * 100
down_probability = (1 - probability) * 100

p1, p2 = st.columns(2)
with p1:
    st.write(f"📈 **偏多评分：{up_probability:.1f}%**")
    st.progress(up_probability / 100)

with p2:
    st.write(f"📉 **偏空评分：{down_probability:.1f}%**")
    st.progress(down_probability / 100)

trade_col, market_col = st.columns([2, 1])

with trade_col:
    st.subheader("🎯 交易建议")

    if is_demo:
        st.info("当前为演示数据：请先填入有效 API Key。")

    elif direction == "观望":
        st.warning("⏸️ 建议观望：多个指标尚未形成一致方向。")

    else:
        stop, target = trade_levels(price, float(latest["ATR"]), direction)
        max_loss = account_size * risk_percent / 100
        position = max_loss / abs(price - stop)

        action = "做多" if direction == "偏多" else "做空"
        action_color = "green" if direction == "偏多" else "red"

        st.markdown(f"""
        <div class="trade">
            <h3 class="{action_color}">{direction} · {action}参考</h3>
            入场参考：<b>${price:,.2f}</b><br>
            风险止损：<b class="red">${stop:,.2f}</b><br>
            目标价格：<b class="green">${target:,.2f}</b><br>
            风险/收益比：<b>1:2.00</b><br>
            最大可承受亏损：<b class="gold">${max_loss:,.2f}</b><br>
            估算仓位上限：<b>{position:.2f} 金衡盎司</b>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("查看评分依据"):
        for item in reasons:
            st.write(f"• {item}")

with market_col:
    change_24h = float(df["Close"].iloc[-1] - df["Close"].iloc[-24])
    ma_bias = (price - latest["MA20"]) / latest["MA20"] * 100

    st.subheader("📊 市场状态")
    st.write(f"24小时变化：${change_24h:.2f}")
    st.write(f"偏离 MA20：{ma_bias:.2f}%")
    st.write(f"ATR 波动率：${latest['ATR']:.2f}")
    st.write(f"最后 K 线：{df.index[-1].strftime('%Y-%m-%d %H:%M UTC')}")

st.markdown("<hr class='divider'>", unsafe_allow_html=True)
st.subheader("📈 价格走势")

fig = go.Figure()

fig.add_scatter(
    x=df.index, y=df["Close"], name="价格",
    line=dict(color="#f7971e", width=2.5)
)
fig.add_scatter(
    x=df.index, y=df["MA20"], name="MA20",
    line=dict(color="#ffd200", dash="dash")
)
fig.add_scatter(
    x=df.index, y=df["BB_Upper"], name="布林上轨",
    line=dict(color="rgba(255,255,255,.3)", dash="dot")
)
fig.add_scatter(
    x=df.index, y=df["BB_Lower"], name="布林下轨",
    line=dict(color="rgba(255,255,255,.3)", dash="dot"),
    fill="tonexty",
    fillcolor="rgba(255,255,255,.04)",
)

fig.update_layout(
    template="plotly_dark",
    height=420,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=0, r=0, t=20, b=0),
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("""
<div style="text-align:center;color:#64748b;font-size:12px;padding:25px;">
⚠️ 本工具仅供研究与教育用途，不构成投资建议，也不会自动交易。
</div>
""", unsafe_allow_html=True)
