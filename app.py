import streamlit as st
import cv2
from ultralytics import YOLO
import time
from PIL import Image

st.set_page_config(page_title="工地安全 AI 监控", layout="wide")
st.title("🏗️ 工地安全 AI 智能监控系统")

# --- 初始化抓拍历史记录 ---
# session_state 在页面刷新时不会消失
if 'history' not in st.session_state:
    st.session_state.history = []  # 存储图片对象
if 'last_alert_time' not in st.session_state:
    st.session_state.last_alert_time = 0 # 控制抓拍频率

# --- 侧边栏配置 ---
st.sidebar.header("控制面板")
rtsp_url = st.sidebar.text_input("视频源地址", placeholder="rtsp://... 或 0 (本地)")
conf_threshold = st.sidebar.slider("识别灵敏度", 0.1, 1.0, 0.5)
run_button = st.sidebar.button("▶️ 启动监控")
stop_button = st.sidebar.button("⏹️ 停止监控")

# --- 加载模型 ---
@st.cache_resource
def load_models():
    return YOLO("ppe_master.pt"), YOLO("fire_smoke.pt")

ppe_model, fire_model = load_models()

# --- 主界面布局 ---
col_video, col_alerts = st.columns([3, 1]) # 左边看视频，右边看实时报警文字

with col_video:
    video_placeholder = st.empty()

with col_alerts:
    st.subheader("🔔 实时状态")
    status_text = st.empty()

# --- 底部抓拍区 ---
st.write("---")
st.subheader("📸 违规抓拍历史 (最近 5 张)")
history_placeholder = st.columns(5)

# --- 监控逻辑 ---
if run_button and rtsp_url:
    # 兼容处理：如果是数字 0 则转为 int 调本地摄像头
    source = int(rtsp_url) if rtsp_url.isdigit() else rtsp_url
    cap = cv2.VideoCapture(source)
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            st.error("视频流读取失败")
            break
            
        # 1. AI 推理
        res_ppe = ppe_model(frame, conf=conf_threshold, verbose=False)
        # 每隔 15 帧检测一次火灾防止卡顿
        res_fire = fire_model(frame, conf=conf_threshold, verbose=False, half=True)
        
        # 获取标签
        labels = [ppe_model.names[int(c)] for r in res_ppe for c in r.boxes.cls]
        fire_labels = [fire_model.names[int(c)] for r in res_fire for c in r.boxes.cls]

        # 2. 渲染画面
        annotated_frame = res_ppe[0].plot()
        if len(res_fire[0].boxes) > 0:
            annotated_frame = res_fire[0].plot(img=annotated_frame)

        # 3. 抓拍逻辑：如果发现违规 且 距离上次抓拍超过 5 秒
        current_time = time.time()
        is_violation = ('no_helmet' in labels) or ('Fire' in fire_labels) or ('Smoke' in fire_labels)
        
        if is_violation and (current_time - st.session_state.last_alert_time > 5):
            # 将 BGR 转 RGB 并转为 PIL 图片存储
            img_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            snap_img = Image.fromarray(img_rgb)
            
            # 存入历史记录最前面，只留 5 张
            st.session_state.history.insert(0, {
                "img": snap_img,
                "time": time.strftime("%H:%M:%S"),
                "type": "火情" if 'Fire' in fire_labels else "未戴安全帽"
            })
            st.session_state.history = st.session_state.history[:5]
            st.session_state.last_alert_time = current_time
            
            # 刷新底部的图片显示
            for i, item in enumerate(st.session_state.history):
                history_placeholder[i].image(item["img"], caption=f"{item['time']} - {item['type']}")

        # 4. 更新主画面
        frame_display = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
        video_placeholder.image(frame_display, channels="RGB", use_container_width=True)

        # 5. 更新状态文字
        if 'no_helmet' in labels:
            status_text.error("🚨 检测到未佩戴安全帽")
        elif 'Fire' in fire_labels:
            status_text.error("🔥 检测到明火！")
        else:
            status_text.success("✅ 区域安全")

        if stop_button:
            cap.release()
            break
