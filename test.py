# test.py - 生成黄金交易面板

import datetime

# ===== 你的交易数据 =====
price = 4058.88
ma20 = 4087.70
rsi = 35.3
bb_width = 130.80
atr = 23.58
open_price = 4087.70
signal = "观望，不交易"
signal_reason = "市场方向不明，AI 信心不足"
buy_level = 4059.49
sell_level = 4075.90
up_probability = 42

# ===== 自动计算 =====
change = price - open_price
change_percent = (change / open_price) * 100
arrow = "▲" if change >= 0 else "▼"
change_class = "up" if change >= 0 else "down"

if rsi > 70:
    rsi_status = "超买"
elif rsi < 30:
    rsi_status = "超卖"
else:
    rsi_status = "中性"

now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ===== HTML 网页 =====
html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>黄金交易信号监控</title>
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background: #0b0e14;
            color: #e0e4eb;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }}
        .container {{
            max-width: 750px;
            width: 100%;
            background: #141a24;
            border-radius: 28px;
            padding: 30px 28px 36px;
            border: 1px solid #2a3340;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 22px;
        }}
        .header h1 {{
            font-size: 22px;
            background: linear-gradient(135deg, #f6d365, #fda085);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .badge {{
            background: #1f2a36;
            padding: 5px 16px;
            border-radius: 30px;
            font-size: 13px;
            border: 1px solid #2e3b4a;
            color: #9aaec9;
        }}
        .price-card {{
            background: #1e2633;
            border-radius: 18px;
            padding: 22px 20px;
            margin-bottom: 20px;
            border-left: 6px solid #f6b26b;
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
        }}
        .price-left .label {{ font-size: 14px; color: #8899b0; }}
        .price-left .value {{ font-size: 40px; font-weight: 700; color: #fff; }}
        .price-left .value small {{ font-size: 17px; color: #8899b0; margin-left: 4px; }}
        .price-right {{ text-align: right; }}
        .price-right .change {{ font-size: 18px; font-weight: 500; }}
        .price-right .change.up {{ color: #7ddfb3; }}
        .price-right .change.down {{ color: #f28b82; }}
        .price-right .sub {{ font-size: 13px; color: #8899b0; margin-top: 3px; }}
        .grid-4 {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr 1fr;
            gap: 12px;
            margin-bottom: 20px;
        }}
        .stat-box {{
            background: #1a212c;
            border-radius: 14px;
            padding: 14px 8px;
            text-align: center;
            border: 1px solid #26303e;
        }}
        .stat-box .num {{ font-size: 19px; font-weight: 600; color: #fff; }}
        .stat-box .lbl {{ font-size: 12px; color: #7a8aa0; margin-top: 4px; }}
        .stat-box .lbl i {{ font-style: normal; color: #f6b26b; }}
        .signal-card {{
            background: #1a212c;
            border-radius: 18px;
            padding: 20px 20px 16px;
            margin-bottom: 16px;
            border: 1px solid #2a3442;
        }}
        .signal-row {{
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
        }}
        .signal-label {{ font-size: 15px; color: #a0b2c9; }}
        .signal-value {{ font-size: 26px; font-weight: 700; }}
        .signal-value.buy {{ color: #7ddfb3; }}
        .signal-value.sell {{ color: #f28b82; }}
        .signal-value.hold {{ color: #f6c96e; }}
        .signal-reason {{
            margin-top: 8px;
            font-size: 15px;
            background: #0f151e;
            padding: 10px 14px;
            border-radius: 12px;
            border-left: 4px solid #f6c96e;
            color: #bcc9dd;
        }}
        .condition-box {{
            display: flex;
            flex-wrap: wrap;
            gap: 14px;
            background: #0f151e;
            border-radius: 14px;
            padding: 16px 18px;
            margin: 14px 0 16px;
            border: 1px dashed #2f3b4c;
        }}
        .condition-item .tag {{ font-size: 12px; color: #7a8aa0; }}
        .condition-item .val {{ font-size: 17px; font-weight: 600; }}
        .condition-item .val.green {{ color: #7ddfb3; }}
        .condition-item .val.red {{ color: #f28b82; }}
        .footer-meta {{
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            font-size: 13px;
            color: #6f7f96;
            padding-top: 14px;
            border-top: 1px solid #1f2937;
            margin-top: 6px;
        }}
        .footer-meta .warn {{ color: #f6c96e; }}
        .btn-refresh {{
            background: #2a3442;
            border: none;
            color: #cbd8ec;
            padding: 5px 18px;
            border-radius: 30px;
            font-size: 13px;
            cursor: pointer;
            border: 1px solid #3b485a;
        }}
        .btn-refresh:hover {{ background: #3b485a; color: #fff; }}
        .risk {{ font-size: 12px; color: #4a5a6e; text-align: center; border-top: 1px solid #1b2430; padding-top: 14px; margin-top: 14px; }}
        @media (max-width: 550px) {{
            .grid-4 {{ grid-template-columns: 1fr 1fr; }}
            .price-left .value {{ font-size: 30px; }}
            .container {{ padding: 18px 14px; }}
        }}
    </style>
</head>
<body>

<div class="container">

    <div class="header">
        <h1>⛁ 黄金 EA 监控</h1>
        <div class="badge">🤖 AI 置信度 58%</div>
    </div>

    <div class="price-card">
        <div class="price-left">
            <div class="label">XAUUSD 实时价格</div>
            <div class="value">{price} <small>USD</small></div>
        </div>
        <div class="price-right">
            <div class="change {change_class}">{arrow} {change:.2f} ({change_percent:.2f}%)</div>
            <div class="sub">今日开盘 {open_price}</div>
        </div>
    </div>

    <div class="grid-4">
        <div class="stat-box"><div class="num">{ma20}</div><div class="lbl">📈 20日均线</div></div>
        <div class="stat-box"><div class="num">{rsi}</div><div class="lbl">📊 RSI <i>({rsi_status})</i></div></div>
        <div class="stat-box"><div class="num">{bb_width}</div><div class="lbl">📉 布林带宽</div></div>
        <div class="stat-box"><div class="num">{atr}</div><div class="lbl">⚡ ATR 波动率</div></div>
    </div>

    <div class="signal-card">
        <div class="signal-row">
            <span class="signal-label">📌 交易建议</span>
            <span class="signal-value hold">⏳ {signal}</span>
        </div>
        <div class="signal-reason">⚠️ {signal_reason} &nbsp;·&nbsp; 上涨概率 {up_probability}%</div>
    </div>

    <div class="condition-box">
        <div class="condition-item">
            <div class="tag">📈 建议买入</div>
            <div class="val green">突破 {buy_level} 做多</div>
        </div>
        <div class="condition-item">
            <div class="tag">📉 建议卖出</div>
            <div class="val red">跌破 {sell_level} 做空</div>
        </div>
    </div>

    <div class="footer-meta">
        <div><span class="warn">⏱ 建议每 30-60 分钟刷新</span></div>
        <div class="time">🕒 数据时间：{now}</div>
        <button class="btn-refresh" onclick="location.reload()">⟳ 刷新数据</button>
    </div>

    <div class="risk">⚡ 建议仅供参考 · 请自行判断风险</div>

</div>

</body>
</html>'''

# ===== 保存 dashboard.html =====
with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("=" * 50)
print("✅ dashboard.html 已生成！")
print("=" * 50)
print(f"🕒 更新时间：{now}")
print(f"💰 当前价格：{price}")
print(f"📊 交易信号：{signal}")
print("=" * 50)
print("📁 现在右键 dashboard.html → Open with Live Server")
print("=" * 50)