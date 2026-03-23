from ultralytics import YOLO
import os

# 确保文件名和你复制进去的完全一致
models = ["ppe_master.pt", "construction_safety.pt", "fire_smoke.pt"]

print("🔍 开始扫描模型标签...\n" + "="*30)

for m_path in models:
    if os.path.exists(m_path):
        try:
            model = YOLO(m_path)
            # 打印模型名字和它能识别的所有类别
            print(f"📦 模型文件: {m_path}")
            print(f"🏷️ 识别标签: {model.names}")
            print("-" * 30)
        except Exception as e:
            print(f"❌ 加载 {m_path} 出错: {e}")
    else:
        print(f"⚠️ 未找到文件: {m_path}")
