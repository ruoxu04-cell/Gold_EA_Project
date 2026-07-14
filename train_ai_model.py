"""
黄金EA项目 - 阶段3：训练AI模型（原始随机森林版本）
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from sklearn.preprocessing import StandardScaler
import joblib
import warnings
warnings.filterwarnings('ignore')

print("🤖 开始训练原始随机森林 AI 模型...")

# 读取数据
df = pd.read_csv('XAUUSD_H1_with_indicators.csv', parse_dates=['Date'])

# 定义目标变量：未来5根K线涨幅 > 0.3%
future_returns = df['Close'].shift(-5) / df['Close'] - 1
df['Target'] = (future_returns > 0.003).astype(int)
df = df.dropna()

print(f"📊 数据总量：{len(df)} 条")
print(f"📈 目标变量分布：")
print(f"   买入信号 (1)：{df['Target'].sum()} 条 ({df['Target'].mean()*100:.1f}%)")
print(f"   不买入 (0)：{(len(df) - df['Target'].sum())} 条 ({(1-df['Target'].mean())*100:.1f}%)")

# 特征
features = ['MACD', 'MACD_Signal', 'MACD_Histogram', 'RSI', 'BB_Upper', 'BB_Lower', 'BB_Width', 'MA20']
X = df[features]
y = df['Target']

# 标准化
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 切分数据
split_idx = int(len(X) * 0.7)
X_train, X_test = X_scaled[:split_idx], X_scaled[split_idx:]
y_train, y_test = y[:split_idx], y[split_idx:]

print(f"\n📊 训练集：{len(X_train)} 条，测试集：{len(X_test)} 条")

# ============================================================
# 原始随机森林模型（最开始你用的那个）
# ============================================================
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=12,
    min_samples_split=5,
    min_samples_leaf=2,
    class_weight='balanced',  # 处理不平衡数据
    random_state=42,
    n_jobs=-1
)

print("🔄 训练随机森林模型...")
model.fit(X_train, y_train)

# 评估
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f"\n✅ 模型在测试集上的准确率（胜率）: {accuracy*100:.2f}%")

print("\n📊 分类报告：")
print(classification_report(y_test, y_pred, target_names=['不买入 (0)', '买入 (1)']))

# 特征重要性
importance = pd.DataFrame({
    'Feature': features,
    'Importance': model.feature_importances_
}).sort_values('Importance', ascending=False)
print("\n📊 指标重要性排名：")
print(importance)

# 保存模型
joblib.dump(model, 'gold_ai_model.pkl')
joblib.dump(scaler, 'scaler.pkl')
print("\n✅ 模型已保存为 gold_ai_model.pkl")
print("✅ 标准化器已保存为 scaler.pkl")

print("\n✅ 阶段3完成！")