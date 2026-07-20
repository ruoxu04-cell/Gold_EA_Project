"""TOKONG 黄金交易系统：保留原版页面结构的安全增强版。

运行：streamlit run app_full.py
配置密钥：在 .streamlit/secrets.toml 加入 TWELVE_DATA_API_KEY = "..."
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st


st.set_page_config(page_title="TOKONG 黄金交易", page_icon="🏆", layout="wide")

st.markdown("""
<style>
 .stApp { background:linear-gradient(135deg,#0a0e1a 0%,#1a1a2e 50%,#16213e 100%); }
 .main-title { background:linear-gradient(90deg,#f7971e,#ffd200);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:32px;font-weight:800; }
 .price-display { font-size:48px;font-weight:700;color:#fff;text-align:center; }
 .price-change-positive { color:#00ff88;font-size:18px;font-weight:600; } .price-change-negative { color:#ff4757;font-size:18px;font-weight:600; }
 .brand-card { background:rgba(255,255,255,.03);border:1px solid rgba(255,215,0,.12);border-radius:16px;padding:16px;text-align:center;min-height:122px; }
 .metric-value { color:#fff;font-size:26px;font-weight:700; } .metric-label { color:#8892b0;font-size:13px;text-transform:uppercase; }
 .signal-bullish,.signal-bearish,.signal-neutral,.signal-wait { border-radius:8px;padding:4px 16px; }
 .signal-bullish { background:#00ff8833;border:1px solid #00ff88;color:#00ff88; } .signal-bearish { background:#ff475733;border:1px solid #ff4757;color:#ff4757; }
 .signal-wait { background:#ffd70033;border:1px solid #ffd700;color:#ffd700; } .signal-neutral { background:#8892b033;border:1px solid #8892b0;color:#8892b0; }
 .gold-divider { border:none;height:2px;background:linear-gradient(90deg,transparent,#f7971e,#ffd200,#f7971e,transparent);margin:15px 0; }
 .trade-card { background:rgba(255,255,255,.03);border-radius:12px;padding:18px 22px;border-left:4px solid #f7971e;line-height:1.9; }
 .trade-card-buy { border-left-color:#00ff88;background:rgba(0,255,136,.05); } .trade-card-sell { border-left-color:#ff4757;background:rgba(255,71,87,.05); }
 .trade-card-wait { border-left-color:#ffd700;background:rgba(255,215,0,.05); } .trade-card-neutral { border-left-color:#8892b0;background:rgba(136,146,176,.05); }
 .footer { text-align:center;color:#495670;font-size:12px;padding:25px 0 10px;border-top:1px solid rgba(255,255,255,.05);margin-top:30px; }
 #MainMenu,footer,header { visibility:hidden; } .stDeployButton { display:none!important; }
</style>
""", unsafe_allow_html=True)


def configured_key() -> str:
    return st.secrets.get("TWELVE_DATA_API_KEY", os.getenv("TWELVE_DATA_API_KEY", ""))


def make_demo_data(periods: int = 200) -> pd.DataFrame:
    """仅在明确标记为演示数据时使用，绝不混作实时数据。"""
    rng = np.random.default_rng(20260720)
    index = pd.date_range(datetime.now(timezone.utc) - timedelta(hours=periods - 1), periods=periods, freq="h")
    close = 2350 * np.exp(np.cumsum(rng.normal(0, 0.0015, periods)))
    spread = close * rng.uniform(.0003, .0015, periods)
    return pd.DataFrame({"Open": np.r_[close[0], close[:-1]], "High": close + spread,
                         "Low": close - spread, "Close": close, "Volume": 0}, index=index)


@st.cache_data(ttl=60, show_spinner=False)
def get_historical_data(key: str) -> tuple[pd.DataFrame, str, bool]:
    """从同一来源取得整段 K 线，避免旧版的实时价和模拟图表不一致。"""
    if not key:
        return make_demo_data(), "演示数据（尚未配置 API 密钥）", True
    try:
        response = requests.get("https://api.twelvedata.com/time_series", params={
            "symbol": "XAU/USD", "interval": "1h", "outputsize": 200, "apikey": key}, timeout=12)
        response.raise_for_status()
        values = response.json().get("values", [])
        if not values:
            raise ValueError(response.json().get("message", "没有收到 K 线数据"))
        df = pd.DataFrame(values).rename(columns=str.title)
        df["Datetime"] = pd.to_datetime(df["Datetime"], utc=True)
        df = df.set_index("Datetime").sort_index()
        for field in ("Open", "High", "Low", "Close"):
            df[field] = pd.to_numeric(df[field], errors="coerce")
        df = df.dropna(subset=["Open", "High", "Low", "Close"])
        if len(df) < 50:
            raise ValueError("可用 K 线不足 50 根")
        return df, "Twelve Data · XAU/USD 1 小时 K 线", False
    except (requests.RequestException, ValueError, KeyError) as exc:
        return make_demo_data(), f"演示数据（实时行情不可用：{exc}）", True


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    delta = prices.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    return 100 - 100 / (1 + gain / loss.replace(0, np.nan))


def add_indicators(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    df["MA20"] = df.Close.rolling(20).mean()
    df["RSI"] = calculate_rsi(df.Close)
    fast, slow = df.Close.ewm(span=12, adjust=False).mean(), df.Close.ewm(span=26, adjust=False).mean()
    df["MACD"] = fast - slow
    df["MACD_Signal"] = df.MACD.ewm(span=9, adjust=False).mean()
    df["MACD_Histogram"] = df.MACD - df.MACD_Signal
    std = df.Close.rolling(20).std()
    df["BB_Upper"], df["BB_Lower"] = df.MA20 + 2 * std, df.MA20 - 2 * std
    df["BB_Width"] = df.BB_Upper - df.BB_Lower
    previous = df.Close.shift()
    tr = pd.concat([df.High - df.Low, (df.High - previous).abs(), (df.Low - previous).abs()], axis=1).max(axis=1)
    df["ATR"] = tr.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    return df.dropna().copy()


def rule_signal(df: pd.DataFrame, min_confidence: int) -> tuple[float, list[str]]:
    """可审计的规则评分：并非 AI 预测，也不会承诺胜率。"""
    x, score, reasons = df.iloc[-1], 0, []
    if x.Close > x.MA20:
        score += 1; reasons.append("价格在 MA20 上方")
    else:
        score -= 1; reasons.append("价格在 MA20 下方")
    if x.MACD > x.MACD_Signal:
        score += 1; reasons.append("MACD 位于信号线上方")
    else:
        score -= 1; reasons.append("MACD 位于信号线下方")
    if x.RSI >= 55:
        score += 1; reasons.append("RSI 偏强")
    elif x.RSI <= 45:
        score -= 1; reasons.append("RSI 偏弱")
    else:
        reasons.append("RSI 中性")
    confidence = 50 + abs(score) / 3 * 35
    probability = 0.5 + score / 3 * .35
    # 不足门槛时强制置于观望区，防止低置信度给出交易建议。
    if confidence < min_confidence or abs(score) < 2:
        probability = .50
    return float(np.clip(probability, .15, .85)), reasons


def calculate_dynamic_targets(df: pd.DataFrame, price: float, prob: float) -> dict[str, float | str]:
    x, atr = df.iloc[-1], float(df.ATR.iloc[-1])
    deviation = abs(price - x.MA20) / x.MA20 * 100
    macd_strength = abs(x.MACD_Histogram) / price * 100
    rsi_extreme = abs(x.RSI - 50) / 50
    strength = min(1., (deviation * .4 + macd_strength * .3 + rsi_extreme * .3) / 2)
    if strength > .60:
        stop_mult, take_mult, style = 1.5, 3.5, "🚀 强趋势（较宽目标）"
    elif strength > .30:
        stop_mult, take_mult, style = 1.3, 2.5, "📈 中等趋势"
    else:
        stop_mult, take_mult, style = 1.0, 1.8, "⚖️ 震荡（较近目标）"
    take_mult += (abs(prob - .5) * 2) * .5
    risk, reward = atr * stop_mult, atr * take_mult
    return {"long_stop": price - risk, "long_take": price + reward, "short_stop": price + risk,
            "short_take": price - reward, "rr": reward / risk if risk else 0, "strength": strength, "style": style}


def trade_card(kind: str, title: str, price: float | None = None, stop: float | None = None,
               target: float | None = None, rr: float | None = None, position: str | None = None,
               lines: list[str] | None = None) -> None:
    color = {"buy": "#00ff88", "sell": "#ff4757", "wait": "#ffd700", "neutral": "#8892b0"}[kind]
    body = "" if lines is None else "".join(f'<div class="trade-row">├─ {line}</div>' for line in lines)
    if price is not None:
        body += (f'<div class="trade-row">├─ 入场参考：<strong>${price:,.2f}</strong></div>'
                 f'<div class="trade-row">├─ 风险止损：<strong style="color:#ff4757;">${stop:,.2f}</strong></div>'
                 f'<div class="trade-row">├─ 目标价格：<strong style="color:#00ff88;">${target:,.2f}</strong></div>'
                 f'<div class="trade-row">├─ 风险/收益比：<strong>1:{rr:.2f}</strong></div>'
                 f'<div class="trade-row">└─ 风险上限：<strong style="color:#ffd700;">{position}</strong></div>')
    st.markdown(f'<div class="trade-card trade-card-{kind}"><div class="trade-title" style="color:{color};font-weight:700;">{title}</div>{body}</div>', unsafe_allow_html=True)


with st.sidebar:
    st.header("⚙️ 风险设置")
    minimum = st.slider("最低规则评分", 60, 85, 70, help="低于此分数会强制观望。")
    account = st.number_input("账户规模（美元）", min_value=0., value=10_000., step=500.)
    risk_pct = st.slider("每笔最大风险 (%)", .25, 2., 1., .25)
    if st.button("🔄 刷新行情", use_container_width=True):
        get_historical_data.clear(); st.rerun()

with st.spinner("🔄 正在获取市场数据…"):
    raw, data_source, is_demo = get_historical_data(configured_key())
    df = add_indicators(raw)

if df.empty:
    st.error("数据不足，暂时无法计算技术指标。请稍后刷新。")
    st.stop()

latest, current_price = df.iloc[-1], float(df.Close.iloc[-1])
prob, reasons = rule_signal(df, minimum)
targets = calculate_dynamic_targets(df, current_price, prob)
atr = float(latest.ATR)

col_title, col_time = st.columns([3, 1])
with col_title:
    st.markdown('<span class="main-title">🏆 TOKONG 黄金交易</span>', unsafe_allow_html=True)
with col_time:
    st.markdown(f'<p style="text-align:right;color:#8892b0;font-size:14px;margin-top:10px;">🕐 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>', unsafe_allow_html=True)
st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)

if is_demo:
    st.warning(f"⚠️ {data_source}。不会显示可执行的交易参数。")
else:
    st.caption(f"📡 数据来源：{data_source} · 最后一根 K 线：{df.index[-1].strftime('%Y-%m-%d %H:%M UTC')}")

price_change = current_price - float(df.Close.iloc[-2])
symbol, change_class = ("▲", "price-change-positive") if price_change >= 0 else ("▼", "price-change-negative")
st.markdown(f'''<div style="text-align:center;padding:20px 0 15px;"><div style="color:#8892b0;font-size:14px;text-transform:uppercase;letter-spacing:2px;">💰 最近收盘价</div><div class="price-display">${current_price:,.2f}</div><div class="{change_class}">{symbol} ${abs(price_change):.2f}</div><div style="color:#495670;font-size:12px;margin-top:5px;">📡 {data_source}</div></div>''', unsafe_allow_html=True)
st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)

col_rsi, col_macd, col_rule = st.columns(3)
with col_rsi:
    status = "超买 🔴" if latest.RSI > 70 else "超卖 🟢" if latest.RSI < 30 else "中性 ⚪"
    st.markdown(f'<div class="brand-card"><div class="metric-label">📈 RSI (14)</div><div class="metric-value">{latest.RSI:.1f}</div><div style="color:#8892b0;font-size:14px;">{status}</div></div>', unsafe_allow_html=True)
with col_macd:
    status = "多头 📈" if latest.MACD > latest.MACD_Signal else "空头 📉"
    st.markdown(f'<div class="brand-card"><div class="metric-label">📊 MACD</div><div class="metric-value">{latest.MACD:.2f}</div><div style="color:#8892b0;font-size:14px;">{status}</div></div>', unsafe_allow_html=True)
with col_rule:
    if prob >= .60: css, text = "signal-bullish", "偏多 📈"
    elif prob <= .40: css, text = "signal-bearish", "偏空 📉"
    else: css, text = "signal-wait", "观望 ⏸️"
    st.markdown(f'<div class="brand-card"><div class="metric-label">🤖 规则评分</div><div class="metric-value">{max(prob, 1-prob)*100:.1f}%</div><div><span class="{css}">{text}</span></div></div>', unsafe_allow_html=True)

st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)
up, down = prob * 100, (1 - prob) * 100
p1, p2 = st.columns(2)
with p1: st.markdown(f"📈 **偏多评分：{up:.1f}%**"); st.progress(up / 100)
with p2: st.markdown(f"📉 **偏空评分：{down:.1f}%**"); st.progress(down / 100)
if .40 < prob < .60:
    st.warning("⏸️ **当前判断：观望**（规则评分不足，暂不建立新仓位）")
elif prob >= .60:
    st.success(f"✅ **当前判断：偏多**（规则评分：{up:.0f}%；非胜率承诺）")
else:
    st.error(f"❌ **当前判断：偏空**（规则评分：{down:.0f}%；非胜率承诺）")

st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)
col_trade, col_market = st.columns([2, 1])
with col_trade:
    st.markdown('<p style="color:#f7971e;font-weight:700;font-size:16px;">🎯 交易建议</p>', unsafe_allow_html=True)
    st.caption(f"📊 市场状态：{targets['style']} | 趋势强度：{targets['strength'] * 100:.0f}%")
    if is_demo:
        trade_card("neutral", "🤔 建议：仅浏览演示", lines=["原因：当前不是可验证的实时行情", "请配置 API 密钥后重新评估", "└─ 不应依据演示数据交易"])
    elif prob >= .70:
        trade_card("buy", "✅ 偏多 · 风险规划参考", current_price, targets["long_stop"], targets["long_take"], targets["rr"], f"最多亏损 ${account * risk_pct / 100:,.2f}")
    elif .60 <= prob < .70:
        trade_card("buy", "⚠️ 偏多 · 仅在风险承受范围内", current_price, targets["long_stop"], targets["long_take"], targets["rr"], f"最多亏损 ${account * risk_pct / 100:,.2f}")
    elif prob <= .30:
        trade_card("sell", "❌ 偏空 · 风险规划参考", current_price, targets["short_stop"], targets["short_take"], targets["rr"], f"最多亏损 ${account * risk_pct / 100:,.2f}")
    elif .30 < prob <= .40:
        trade_card("sell", "⚠️ 偏空 · 仅在风险承受范围内", current_price, targets["short_stop"], targets["short_take"], targets["rr"], f"最多亏损 ${account * risk_pct / 100:,.2f}")
    else:
        trade_card("wait", "⏸️ 建议：暂时观望", lines=["原因：市场信号尚不明确", "等待多项指标同向后再评估", "└─ 耐心等待，不勉强交易"])
    with st.expander("查看评分依据"):
        for reason in reasons: st.write(f"• {reason}")

with col_market:
    change_24h = float(df.Close.iloc[-1] - df.Close.iloc[-24])
    bias = (current_price - latest.MA20) / latest.MA20 * 100
    st.markdown('<p style="color:#f7971e;font-weight:700;font-size:16px;">📊 市场状态</p>', unsafe_allow_html=True)
    st.markdown(f'''<div style="background:rgba(255,255,255,.03);border-radius:12px;padding:16px;border:1px solid rgba(255,255,255,.06);"><div style="color:#c9d1d9;font-size:14px;margin:4px 0;">📅 {df.index[-1].strftime('%Y-%m-%d %H:%M UTC')}</div><div style="color:#c9d1d9;font-size:14px;margin:4px 0;">📈 24小时变化：<strong style="color:{'#00ff88' if change_24h >= 0 else '#ff4757'};">${change_24h:.2f}</strong></div><div style="color:#c9d1d9;font-size:14px;margin:4px 0;">📊 布林带宽：<strong style="color:#ffd700;">${latest.BB_Width:.2f}</strong></div><div style="color:#c9d1d9;font-size:14px;margin:4px 0;">📍 偏离均线：<strong style="color:{'#00ff88' if bias >= 0 else '#ff4757'};">{bias:.2f}%</strong></div><div style="color:#c9d1d9;font-size:14px;margin:4px 0;">📊 波动率（ATR）：<strong style="color:#ffd700;">${atr:.2f}</strong></div></div>''', unsafe_allow_html=True)

st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)
st.markdown('<p style="color:#f7971e;font-weight:700;font-size:16px;">📈 价格走势</p>', unsafe_allow_html=True)
fig = go.Figure()
fig.add_scatter(x=df.index, y=df.Close, mode="lines", name="价格", line=dict(color="#f7971e", width=2.5))
fig.add_scatter(x=df.index, y=df.MA20, mode="lines", name="MA20", line=dict(color="#ffd700", width=1.5, dash="dash"))
fig.add_scatter(x=df.index, y=df.BB_Upper, mode="lines", name="布林上轨", line=dict(color="rgba(255,255,255,.25)", width=1, dash="dot"))
fig.add_scatter(x=df.index, y=df.BB_Lower, mode="lines", name="布林下轨", line=dict(color="rgba(255,255,255,.25)", width=1, dash="dot"), fill="tonexty", fillcolor="rgba(255,255,255,.03)")
fig.update_layout(height=400, template="plotly_dark", xaxis_title="时间", yaxis_title="价格（美元）", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=0, r=0, t=20, b=20), legend=dict(yanchor="top", y=.99, xanchor="left", x=.01))
fig.update_xaxes(gridcolor="rgba(255,255,255,.05)"); fig.update_yaxes(gridcolor="rgba(255,255,255,.05)")
st.plotly_chart(fig, use_container_width=True)

st.markdown('''<div class="footer"><p>🏆 TOKONG 黄金交易 · 市场观察系统</p><p style="color:#2d3850;">⚠️ 仅供研究与教育，不构成投资建议，也不会自动执行交易。价格与指标可能出错或延迟，请独立核实并谨慎决策。</p></div>''', unsafe_allow_html=True)
