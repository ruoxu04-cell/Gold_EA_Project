"""黄金市场观察面板（仅供教育与研究使用，不会自动下单）。"""

from __future__ import annotations

import os
import hashlib
import re
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

TWELVE_DATA_API_KEY = "b3b8143cd542493b9de1fb5aa13a9d07"

st.set_page_config(page_title="TOKONG 黄金市场观察", page_icon="🏆", layout="wide")


@dataclass(frozen=True)
class Signal:
    direction: str
    confidence: float
    action: str
    reasons: list[str]


# 管理员账号。密码以不可逆哈希保存；管理员本人也必须先登录。
DATABASE_PATH = Path(__file__).with_name("users.db")
OWNER_USERNAME = "GS4896"
OWNER_PASSWORD_HASH = (
    "af1166da60b40bfcde0dc1422c720b13$"
    "c37e4f6e6a785573c842b0185690a1ad57dab2d81e05805751cce76e7a2a61f6"
)


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, _ = stored.split("$", 1)
        return secrets.compare_digest(hash_password(password, bytes.fromhex(salt_hex)), stored)
    except ValueError:
        return False


def init_database() -> None:
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL, approved INTEGER NOT NULL DEFAULT 0,
            is_admin INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL)""")
        # 兼容之前没有审批栏位的旧 users.db。
        columns = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
        if "approved" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN approved INTEGER DEFAULT 0")
        if "is_admin" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
        conn.execute("""INSERT INTO users (username, password_hash, approved, is_admin, created_at)
            VALUES (?, ?, 1, 1, ?)
            ON CONFLICT(username) DO UPDATE SET password_hash=excluded.password_hash,
            approved=1, is_admin=1""",
            (OWNER_USERNAME, OWNER_PASSWORD_HASH, datetime.now(timezone.utc).isoformat()))


def create_user(username: str, password: str) -> tuple[bool, str]:
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.execute("""INSERT INTO users (username, password_hash, created_at)
                VALUES (?, ?, ?)""", (username, hash_password(password), datetime.now(timezone.utc).isoformat()))
        return True, "注册申请已提交，等待管理员审核。"
    except sqlite3.IntegrityError:
        return False, "这个用户名已经被注册。"


def check_login(username: str, password: str) -> tuple[str, bool]:
    with sqlite3.connect(DATABASE_PATH) as conn:
        user = conn.execute("SELECT password_hash, approved, is_admin FROM users WHERE username=?", (username,)).fetchone()
    if not user or not verify_password(password, user[0]):
        return "invalid", False
    if not user[1]:
        return "pending", False
    return "success", bool(user[2])


def session_is_active() -> bool:
    """每次页面重跑时验证账号仍然获准，避免旧登录会话继续访问。"""
    username = st.session_state.get("username")
    if not username:
        return False
    with sqlite3.connect(DATABASE_PATH) as conn:
        user = conn.execute(
            "SELECT approved FROM users WHERE username=?", (username,)
        ).fetchone()
    return bool(user and user[0])


def login_required() -> None:
    if st.session_state.get("logged_in") and session_is_active():
        return
    if st.session_state.get("logged_in"):
        st.session_state.clear()
        st.warning("此账号的访问权限已被管理员取消。")
    st.title("🏆 TOKONG 黄金交易系统")
    st.caption("请登录或注册后进入市场观察页面。")
    login_tab, register_tab = st.tabs(["登录", "注册"])
    with login_tab:
        with st.form("login"):
            username = st.text_input("用户名")
            password = st.text_input("密码", type="password")
            login = st.form_submit_button("登录")
        if login:
            status, is_admin = check_login(username.strip(), password)
            if status == "success":
                st.session_state.update(logged_in=True, username=username.strip(), is_admin=is_admin)
                st.rerun()
            elif status == "pending":
                st.warning("你的账号正在等待管理员审核。")
            else:
                st.error("用户名或密码不正确。")
    with register_tab:
        with st.form("register"):
            username = st.text_input("创建用户名")
            password = st.text_input("创建密码", type="password")
            confirm = st.text_input("确认密码", type="password")
            register = st.form_submit_button("提交注册申请")
        if register:
            username = username.strip()
            if not re.fullmatch(r"[A-Za-z0-9_]{3,32}", username):
                st.error("用户名必须为 3 至 32 个英文、数字或底线。")
            elif len(password) < 8:
                st.error("密码至少需要 8 个字符。")
            elif password != confirm:
                st.error("两次输入的密码不一致。")
            else:
                ok, message = create_user(username, password)
                (st.success if ok else st.error)(message)
    st.stop()


def api_key() -> str:
    return TWELVE_DATA_API_KEY


def demo_data(periods: int = 200) -> pd.DataFrame:
    """仅用于页面预览；调用方必须在 UI 中清楚标示为模拟数据。"""
    rng = np.random.default_rng(42)
    index = pd.date_range(end=datetime.now(timezone.utc), periods=periods, freq="h")
    close = 2_350 * np.exp(np.cumsum(rng.normal(0, 0.0018, periods)))
    spread = close * rng.uniform(0.0004, 0.0018, periods)
    return pd.DataFrame(
        {"Open": np.r_[close[0], close[:-1]], "High": close + spread,
         "Low": close - spread, "Close": close, "Volume": 0}, index=index
    )


@st.cache_data(ttl=30, show_spinner=False)
def load_candles(key: str) -> tuple[pd.DataFrame, str, float | None]:
    """读取小时 K 线和独立实时价；失败时不伪造报价。"""
    if not key or "粘贴在这里" in key:
        return pd.DataFrame(), "请先在代码顶部填入有效的 Twelve Data API Key。", None
    try:
        response = requests.get(
            "https://api.twelvedata.com/time_series",
            params={"symbol": "XAU/USD", "interval": "1h", "outputsize": 200, "apikey": key},
            timeout=12,
        )
        response.raise_for_status()
        payload = response.json()
        values = payload.get("values", [])
        if not values:
            raise ValueError(payload.get("message", "供应商没有返回 K 线数据"))
        frame = pd.DataFrame(values)
        frame["datetime"] = pd.to_datetime(frame["datetime"], utc=True)
        frame = frame.set_index("datetime").sort_index()
        frame = frame.rename(columns=str.title)
        for column in ["Open", "High", "Low", "Close"]:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
        frame = frame.dropna(subset=["Open", "High", "Low", "Close"])
        if len(frame) < 50:
            raise ValueError("可用 K 线数量不足")
        quote = requests.get(
            "https://api.twelvedata.com/price",
            params={"symbol": "XAU/USD", "apikey": key}, timeout=12,
        )
        quote.raise_for_status()
        quote_data = quote.json()
        live_price = float(quote_data["price"])
        if live_price <= 0:
            raise ValueError("实时价格无效")
        return frame, "Twelve Data（实时价 + 1 小时 K 线）", live_price
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        return pd.DataFrame(), f"无法取得真实行情：{exc}", None


def add_indicators(frame: pd.DataFrame) -> pd.DataFrame:
    df = frame.copy()
    df["MA20"] = df["Close"].rolling(20).mean()
    delta = df["Close"].diff()
    gain, loss = delta.clip(lower=0), -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    avg_loss = loss.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    df["RSI"] = 100 - 100 / (1 + avg_gain / avg_loss.replace(0, np.nan))
    fast = df["Close"].ewm(span=12, adjust=False).mean()
    slow = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = fast - slow
    df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["BB_upper"] = df["MA20"] + 2 * df["Close"].rolling(20).std()
    df["BB_lower"] = df["MA20"] - 2 * df["Close"].rolling(20).std()
    previous_close = df["Close"].shift()
    true_range = pd.concat([df["High"] - df["Low"], (df["High"] - previous_close).abs(),
                            (df["Low"] - previous_close).abs()], axis=1).max(axis=1)
    df["ATR"] = true_range.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    return df.dropna()


def score_signal(df: pd.DataFrame, threshold: float) -> Signal:
    """透明的规则评分，不把技术指标伪装成预测模型。"""
    row = df.iloc[-1]
    score, reasons = 0, []
    if row.Close > row.MA20:
        score += 1; reasons.append("价格位于 20 小时均线上方")
    else:
        score -= 1; reasons.append("价格位于 20 小时均线下方")
    if row.MACD > row.MACD_signal:
        score += 1; reasons.append("MACD 位于信号线上方")
    else:
        score -= 1; reasons.append("MACD 位于信号线下方")
    if row.RSI >= 55:
        score += 1; reasons.append("RSI 显示偏强动能")
    elif row.RSI <= 45:
        score -= 1; reasons.append("RSI 显示偏弱动能")
    else:
        reasons.append("RSI 处于中性区域")

    confidence = 50 + abs(score) / 3 * 35
    if abs(score) < 2 or confidence < threshold:
        return Signal("观望", confidence, "不建立新仓位", reasons)
    direction = "偏多" if score > 0 else "偏空"
    return Signal(direction, confidence, "仅在风险参数允许时考虑", reasons)


def trade_levels(price: float, atr: float, direction: str) -> tuple[float, float, float]:
    risk = atr * 1.5
    reward = risk * 2
    if direction == "偏多":
        return price - risk, price + reward, 2.0
    return price + risk, price - reward, 2.0


st.markdown("""
<style>
 .stApp {background: linear-gradient(135deg,#0b1020,#17223a);}
 .hero {padding: 1rem 0 .3rem; color:#f6c453; font-size:2rem; font-weight:800;}
 .notice {padding:.75rem 1rem; border-left:4px solid #f6c453; background:#ffffff0d; border-radius:6px;}
</style>
""", unsafe_allow_html=True)

init_database()
login_required()

with st.sidebar:
    st.success(f"👤 已登录：{st.session_state.username}")
    if st.button("退出登录", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    if st.session_state.get("is_admin"):
        st.divider()
        st.subheader("👑 注册审核")
        with sqlite3.connect(DATABASE_PATH) as conn:
            waiting_users = conn.execute(
                "SELECT id, username FROM users WHERE approved=0 ORDER BY created_at"
            ).fetchall()
        if not waiting_users:
            st.caption("目前没有等待审核的用户。")
        for user_id, username in waiting_users:
            left, right = st.columns([2, 1])
            left.write(f"👤 {username}")
            if right.button("通过", key=f"approve_{user_id}"):
                with sqlite3.connect(DATABASE_PATH) as conn:
                    conn.execute("UPDATE users SET approved=1 WHERE id=?", (user_id,))
                st.rerun()

        st.caption("已通过的用户")
        with sqlite3.connect(DATABASE_PATH) as conn:
            active_users = conn.execute(
                "SELECT id, username FROM users WHERE approved=1 AND is_admin=0 ORDER BY username"
            ).fetchall()
        if not active_users:
            st.caption("目前没有其他已通过用户。")
        for user_id, username in active_users:
            left, right = st.columns([2, 1])
            left.write(f"👤 {username}")
            if right.button("取消权限", key=f"revoke_{user_id}"):
                with sqlite3.connect(DATABASE_PATH) as conn:
                    conn.execute("UPDATE users SET approved=0 WHERE id=?", (user_id,))
                st.rerun()

    st.divider()
    st.header("风险设置")
    confidence_threshold = st.slider("最低评分门槛", 60, 85, 70, help="未达到门槛时，只显示观望。")
    account_size = st.number_input("账户规模（美元）", min_value=0.0, value=10_000.0, step=500.0)
    risk_pct = st.slider("每笔最大风险 (%)", 0.25, 2.0, 1.0, 0.25)
    if st.button("刷新数据", use_container_width=True):
        load_candles.clear()
        st.rerun()

with st.spinner("正在读取市场数据…"):
    raw, source, live_price = load_candles(api_key())

if raw.empty or live_price is None:
    st.error(source)
    st.info("请确认 API Key 有效、套餐支持 XAU/USD，并在一分钟后点击“刷新数据”。不会使用模拟价格代替真实行情。")
    st.stop()

with st.spinner("正在计算技术指标…"):
    df = add_indicators(raw)

if df.empty:
    st.error("数据不足，无法计算指标。请稍后刷新。")
    st.stop()

latest, previous = df.iloc[-1], df.iloc[-2]
signal = score_signal(df, confidence_threshold)
current_price = live_price
price_change = current_price - latest.Close

st.markdown('<div class="hero">🏆 TOKONG 黄金市场观察</div>', unsafe_allow_html=True)
st.caption(f"数据来源：{source} · 最近一根小时 K 线：{df.index[-1].strftime('%Y-%m-%d %H:%M UTC')}")

a, b, c, d = st.columns(4)
a.metric("XAU/USD 实时价格", f"${current_price:,.2f}", f"相对最近小时收盘 {price_change:+.2f}")
b.metric("RSI (14)", f"{latest.RSI:.1f}")
c.metric("ATR (14)", f"${latest.ATR:,.2f}")
d.metric("规则评分", f"{signal.confidence:.0f}%", signal.direction)

st.markdown("---")
left, right = st.columns([3, 2])
with left:
    fig = go.Figure()
    fig.add_scatter(x=df.index, y=df.Close, name="收盘价", line={"color": "#f6c453", "width": 2.5})
    fig.add_scatter(x=df.index, y=df.MA20, name="MA20", line={"color": "#76b5ff", "dash": "dash"})
    fig.add_scatter(x=df.index, y=df.BB_upper, name="布林上轨", line={"color": "#8792a5", "width": 1})
    fig.add_scatter(x=df.index, y=df.BB_lower, name="布林下轨", line={"color": "#8792a5", "width": 1}, fill="tonexty", fillcolor="rgba(135,146,165,.08)")
    fig.update_layout(template="plotly_dark", height=430, margin={"l": 0, "r": 0, "t": 30, "b": 0},
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", legend={"orientation": "h"})
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("市场判断")
    tone = {"偏多": st.success, "偏空": st.error, "观望": st.warning}[signal.direction]
    tone(f"{signal.direction} · 规则评分 {signal.confidence:.0f}%\n\n{signal.action}")
    st.caption("评分基于均线、MACD 与 RSI 的一致性；它不是 AI 预测，也不保证结果。")
    st.markdown("**评分依据**")
    for reason in signal.reasons:
        st.write(f"• {reason}")

    if signal.direction != "观望":
        stop, target, rr = trade_levels(current_price, latest.ATR, signal.direction)
        max_loss = account_size * risk_pct / 100
        units = max_loss / abs(latest.Close - stop) if stop != latest.Close else 0
        st.markdown("**风险规划（教育示例）**")
        st.write(f"止损：${stop:,.2f} · 目标：${target:,.2f} · 风险收益比：1:{rr:.1f}")
        st.write(f"按最大亏损 ${max_loss:,.2f} 估算，仓位上限约 {units:.2f} 金衡盎司。")
    else:
        st.info("当前不显示交易参数：规则评分不足。")

st.markdown("---")
st.markdown('<div class="notice">⚠️ 本工具仅供研究与教育用途，不构成投资建议，也不会执行或连接任何交易。黄金价格波动显著，请独立核实行情并自行承担决策风险。</div>', unsafe_allow_html=True)
