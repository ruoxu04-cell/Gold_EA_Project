"""
黄金EA项目 - 阶段3：训练AI模型（随机森林）
预测未来5小时黄金是否上涨超过0.5%
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

print("🤖 开始训练 AI 模型...")

# 读取带指标的数据
df = pd.read_csv('XAUUSD_H1_with_indicators.csv', parse_dates=['Date'])

# -------- 定义目标变量（Y）：未来5根K线是否上涨超过0.5% --------
# 如果未来5小时内涨幅 > 0.5%，标记为1（买入信号），否则为0
# 方案A：降低目标涨幅到 0.3%（约30-40点）
# 预测未来3小时，涨幅超过0.2%
# 只要未来3小时上涨，就标记为买入信号
future_returns = df['Close'].shift(-3) / df['Close'] - 1
df['Target'] = (future_returns > 0).astype(int)  # 只要 > 0 就算涨

# 删除最后5行（因为没有未来数据来定义目标）
df = df.dropna()

print(f"📊 数据总量：{len(df)} 条")
print(f"📈 目标变量分布：")
print(f"   买入信号 (1)：{df['Target'].sum()} 条 ({df['Target'].mean()*100:.1f}%)")
print(f"   不买入 (0)：{(len(df) - df['Target'].sum())} 条 ({(1-df['Target'].mean())*100:.1f}%)")

# -------- 选择特征（X）：只使用技术指标 --------
features = ['MACD', 'MACD_Signal', 'MACD_Histogram', 'RSI', 'BB_Upper', 'BB_Lower', 'BB_Width', 'MA20']
X = df[features]
y = df['Target']

# 标准化（对树模型不是必须的，但有助于稳定）
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 按时间切分：前70%训练，后30%测试（避免未来函数）
split_idx = int(len(X) * 0.7)
X_train, X_test = X_scaled[:split_idx], X_scaled[split_idx:]
y_train, y_test = y[:split_idx], y[split_idx:]

print(f"\n📊 训练集：{len(X_train)} 条，测试集：{len(X_test)} 条")

# -------- 训练随机森林模型 --------
print("\n🔄 训练随机森林模型...")
model = RandomForestClassifier(
    n_estimators=200,        # 200棵决策树
    max_depth=12,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1
)
model.fit(X_train, y_train)

# -------- 评估胜率 --------
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f"\n✅ 模型在测试集上的准确率（胜率）: {accuracy*100:.2f}%")

# 打印混淆矩阵
print("\n📊 混淆矩阵（行=真实，列=预测）:")
print(confusion_matrix(y_test, y_pred))

# 打印详细分类报告
print("\n📊 分类报告：")
print(classification_report(y_test, y_pred, target_names=['不买入 (0)', '买入 (1)']))

# 查看哪些指标最重要
importance = pd.DataFrame({
    'Feature': features,
    'Importance': model.feature_importances_
}).sort_values('Importance', ascending=False)
print("\n📊 指标重要性排名（越重要数值越大）：")
print(importance)

# 保存模型和标准化器（供后面EA调用）
joblib.dump(model, 'gold_ai_model.pkl')
joblib.dump(scaler, 'scaler.pkl')
print("\n✅ 模型已保存为 gold_ai_model.pkl")
print("✅ 标准化器已保存为 scaler.pkl")

# 模拟预测示例
print("\n🔮 模拟预测示例（最后5条数据）：")
sample = X_scaled[-5:]
probabilities = model.predict_proba(sample)
for i, prob in enumerate(probabilities):
    print(f"   数据 {i+1}：上涨概率 {prob[1]*100:.1f}%，买入信号：{'✅ 是' if prob[1] > 0.5 else '❌ 否'}")

print("\n✅ 阶段3完成！")
