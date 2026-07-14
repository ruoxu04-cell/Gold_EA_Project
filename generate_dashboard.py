import datetime

# ============================================
# 第一步：从你的交易程序获取数据
# ============================================

# ⚠️ 这里改成你真正的数据！
# 你可以从 trading_signal.py 或 train_ai_model.py 导入数据

# 示例数据（替换成你的真实数据）
data = {
    'price': 4058.88,              # 当前价格
    'open_price': 4087.70,         # 开盘价（或20日均线）
    'ma20': 4087.70,              # 20日均线
    'rsi': 35.3,                  # RSI值
    'bb_width': 130.80,           # 布林带宽
    'atr': 23.58,                 # ATR波动率
    'ai_confidence': '58%',        # AI置信度
    'signal': 'hold',             # buy / sell / hold
    'signal_text': '观望，不交易',  # 显示的文字
    'signal_reason': '市场方向不明，AI 信心不足',
    'up_probability': 42,          # 上涨概率（%）
    'buy_level': 4059.49,          # 建议买入价位
    'sell_level': 4075.90,         # 建议卖出价位
}

# ============================================
# 第二步：计算衍生数据
# ============================================

# 计算价格变化
change = data['price'] - data['open_price']
change_percent = (change / data['open_price']) * 100

if change >= 0:
    change_class = 'up'
    change_arrow = '▲'
else:
    change_class = 'down'
    change_arrow = '▼'

# RSI 状态
if data['rsi'] > 70:
    rsi_status = '超买'
elif data['rsi'] < 30:
    rsi_status = '超卖'
else:
    rsi_status = '中性'

# 信号对应的样式
signal_map = {
    'buy': {'class': 'buy', 'emoji': '📈'},
    'sell': {'class': 'sell', 'emoji': '📉'},
    'hold': {'class': 'hold', 'emoji': '⏳'},
}

signal_info = signal_map.get(data['signal'], signal_map['hold'])

# 更新时间
update_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# ============================================
# 第三步：读取 HTML 模板并替换数据
# ============================================

with open('template.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

# 替换所有占位符
html_content = html_content.replace('{PRICE}', f"{data['price']:.2f}")
html_content = html_content.replace('{OPEN_PRICE}', f"{data['open_price']:.2f}")
html_content = html_content.replace('{MA20}', f"{data['ma20']:.2f}")
html_content = html_content.replace('{RSI}', f"{data['rsi']:.1f}")
html_content = html_content.replace('{RSI_STATUS}', rsi_status)
html_content = html_content.replace('{BB_WIDTH}', f"{data['bb_width']:.2f}")
html_content = html_content.replace('{ATR}', f"{data['atr']:.2f}")
html_content = html_content.replace('{AI_CONFIDENCE}', data['ai_confidence'])
html_content = html_content.replace('{SIGNAL_TEXT}', data['signal_text'])
html_content = html_content.replace('{SIGNAL_CLASS}', signal_info['class'])
html_content = html_content.replace('{SIGNAL_EMOJI}', signal_info['emoji'])
html_content = html_content.replace('{SIGNAL_REASON}', data['signal_reason'])
html_content = html_content.replace('{UP_PROBABILITY}', str(data['up_probability']))
html_content = html_content.replace('{BUY_LEVEL}', f"{data['buy_level']:.2f}")
html_content = html_content.replace('{SELL_LEVEL}', f"{data['sell_level']:.2f}")
html_content = html_content.replace('{UPDATE_TIME}', update_time)
html_content = html_content.replace('{CHANGE_VALUE}', f"{change:.2f}")
html_content = html_content.replace('{CHANGE_PERCENT}', f"{change_percent:.2f}%")
html_content = html_content.replace('{CHANGE_CLASS}', change_class)
html_content = html_content.replace('{CHANGE_ARROW}', change_arrow)

# ============================================
# 第四步：保存新的 HTML 文件
# ============================================

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("✅ dashboard.html 已生成！")
print(f"🕒 更新时间：{update_time}")
print(f"💰 当前价格：{data['price']:.2f}")
print(f"📊 交易信号：{data['signal_text']}")