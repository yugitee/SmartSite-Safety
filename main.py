import cv2
from ultralytics import YOLO

class SafetySystem:
    def __init__(self):
        print("🚀 正在唤醒 AI 安全大脑...")
        
        # 加载 PPE 模型 (使用 ppe_master.pt)
        self.ppe_model = YOLO("ppe_master.pt")
        
        # 加载 烟火模型 (520MB 的大模型，开启半精度提速)
        self.fire_model = YOLO("fire_smoke.pt")
        
        print("✅ 所有模型加载完毕，准备开启监控...")

    def start(self, source=0):
        cap = cv2.VideoCapture(source)
        
        if not cap.isOpened():
            print("❌ 错误：无法打开摄像头，请检查 /dev/video0")
            return

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # 1. 运行 PPE 检测 (主要关注未佩戴情况)
            # verbose=False 减少终端乱跑日志
            ppe_results = self.ppe_model(frame, conf=0.5, verbose=False)
            ppe_labels = [self.ppe_model.names[int(c)] for r in ppe_results for c in r.boxes.cls]

            # 2. 运行 烟火检测 (针对大模型优化)
            fire_results = self.fire_model(frame, conf=0.4, verbose=False, half=True)
            fire_labels = [self.fire_model.names[int(c)] for r in fire_results for c in r.boxes.cls]

            # --- 逻辑判定与报警 ---
            
            # 安全帽判定
            if 'no_helmet' in ppe_labels:
                print("🚨 [危险] 发现人员未佩戴安全帽！")
            
            # 护目镜判定
            if 'no_goggles' in ppe_labels:
                print("👓 [提醒] 请佩戴护目镜")

            # 烟火判定 (注意：模型标签首字母大写 'Fire', 'Smoke')
            if 'Fire' in fire_labels:
                print("🔥 [特级警报] 检测到明火！！")
            if 'Smoke' in fire_labels:
                print("💨 [预警] 检测到疑似烟雾")

            # --- 画面显示 ---
            # 绘制检测框 (这里展示 PPE 的结果，你也可以叠加)
            annotated_frame = ppe_results[0].plot() 
            
            # 如果有火灾，手动在画面上方写个红字
            if 'Fire' in fire_labels:
                cv2.putText(annotated_frame, "FIRE DETECTED!", (50, 50), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)

            cv2.imshow("Multi-Model Safety Monitor (Arch Linux)", annotated_frame)

            # 按下 ESC 键退出
            if cv2.waitKey(1) & 0xFF == 27:
                break

        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    system = SafetySystem()
    system.start(source=0) # 0 是笔记本自带摄像头
