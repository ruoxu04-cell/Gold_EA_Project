"""
黄金EA项目 - 阶段1：下载10年XAUUSD数据
适用于 VS Code + Python 3.10+
"""

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import os

# 1. 初始化MT5连接
print("🔄 正在连接MetaTrader 5...")
if not mt5.initialize():
    print("❌ MT5初始化失败！请确保：")
    print("   1. MT5软件已打开")
    print("   2. 已登录模拟或实盘账户")
    print("   3. MT5路径正确")
    mt5.shutdown()
    exit()
else:
    print("✅ MT5连接成功！")

# 2. 检查是否登录账户
account_info = mt5.account_info()
if account_info is None:
    print("❌ 未登录账户，请在MT5中登录后再运行")
    mt5.shutdown()
    exit()
else:
    print(f"✅ 已登录账户：{account_info.login}")

# 3. 设置下载参数
SYMBOL = "XAUUSD"  # 黄金品种（部分平台可能是"GOLD"或"XAUUSDm"，请确认）
TIMEFRAME = mt5.TIMEFRAME_H1  # 1小时图
START_DATE = datetime(2021, 7, 7)
END_DATE = datetime.now()

print(f"📊 开始下载 {SYMBOL} 数据...")
print(f"   时间范围：{START_DATE.strftime('%Y-%m-%d')} 到 {END_DATE.strftime('%Y-%m-%d')}")

# 4. 获取数据
rates = mt5.copy_rates_range(SYMBOL, TIMEFRAME, START_DATE, END_DATE)

if rates is None or len(rates) == 0:
    print(f"❌ 未获取到数据！可能原因：")
    print(f"   1. 品种名称错误（尝试改为 'GOLD' 或 'XAUUSDm'）")
    print(f"   2. MT5服务器没有该品种的历史数据")
    mt5.shutdown()
    exit()

# 5. 转换为DataFrame
df = pd.DataFrame(rates)
df['time'] = pd.to_datetime(df['time'], unit='s')
df = df[['time', 'open', 'high', 'low', 'close', 'tick_volume']]
df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']

# 6. 保存为CSV
file_path = 'XAUUSD_H1_10years.csv'
df.to_csv(file_path, index=False)

print(f"✅ 数据下载成功！共 {len(df)} 根K线")
print(f"📁 文件已保存至：{os.path.abspath(file_path)}")
print("\n前5行数据预览：")
print(df.head())

# 7. 显示数据统计
print(f"\n📈 数据统计：")
print(f"   开盘价范围：{df['Open'].min():.2f} - {df['Open'].max():.2f}")
print(f"   数据时间跨度：{df['Date'].min()} 到 {df['Date'].max()}")

# 8. 关闭连接
mt5.shutdown()
print("\n✅ 程序执行完毕！")