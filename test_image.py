import cv2
from ultralytics import YOLO
import os

def test_on_photo(image_path):
    # 1. 检查图片是否存在
    if not os.path.exists(image_path):
        print(f"❌ 找不到图片文件: {image_path}")
        return

    print("🚀 正在加载 AI 模型进行单张图片测试...")

    # 2. 加载模型
    ppe_model = YOLO("ppe_master.pt")
    fire_model = YOLO("fire_smoke.pt") # 这个模型很大，请耐心等待

    # 3. 读取并推理
    frame = cv2.imread(image_path)

    # 执行检测
    ppe_results = ppe_model(frame, conf=0.5)
    fire_results = fire_model(frame, conf=0.4, half=True)

    # 4. 提取标签结果
    ppe_labels = [ppe_model.names[int(c)] for r in ppe_results for c in r.boxes.cls]
    fire_labels = [fire_model.names[int(c)] for r in fire_results for c in r.boxes.cls]

    # 5. 打印识别到的所有东西
    print("\n" + "="*30)
    print(f"🔍 PPE 模型检测到: {ppe_labels}")
    print(f"🔥 烟火模型检测到: {fire_labels}")
    print("="*30)

    # 6. 逻辑判定触发
    if 'no_helmet' in ppe_labels:
        print("🚨 警告：图中有人员未佩戴安全帽！")
    if 'Fire' in fire_labels:
        print("🚩 警告：图中发现明火！")

    # 7. 渲染并保存结果
    # 绘制 PPE 结果
    annotated_frame = ppe_results[0].plot()
    # 绘制 烟火 结果 (叠加)
    annotated_frame = fire_results[0].plot(img=annotated_frame)

    # 保存识别后的图片，方便你直接查看
    output_path = "result_preview.jpg"
    cv2.imwrite(output_path, annotated_frame)
    print(f"\n✅ 识别完成！带有检测框的图片已保存至: {output_path}")

if __name__ == "__main__":
    # 请把下面换成你准备好的测试图片文件名
    # 比如你从工地拍的一张照片
    test_image_file = "test.jpg"
    test_on_photo(test_image_file)
