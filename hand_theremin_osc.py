import cv2
import mediapipe as mp
from pythonosc import udp_client
import time

# 初始化 MediaPipe 和 OSC 客户端
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils
client = udp_client.SimpleUDPClient("127.0.0.1", 8000)

# 打开摄像头
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ 无法打开摄像头")
    exit()

print("✅ 摄像头启动成功，按 Q 退出")

while True:
    success, img = cap.read()
    if not success:
        print("⚠️ 摄像头读取失败，跳过当前帧")
        continue

    img = cv2.flip(img, 1)  # 镜像处理使交互更自然
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(imgRGB)
    h, w, _ = img.shape

    if results.multi_hand_landmarks and results.multi_handedness:
        for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            # 获取左右手标签
            label = results.multi_handedness[idx].classification[0].label  # 'Left' or 'Right'
            # 获取食指尖坐标（0~1）
            x = hand_landmarks.landmark[8].x
            y = hand_landmarks.landmark[8].y
            # 转换为像素坐标用于显示
            cx, cy = int(x * w), int(y * h)

            # 画出手部连接和标记点
            mp_drawing.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            cv2.circle(img, (cx, cy), 10, (0, 255, 0), -1)
            cv2.putText(img, f"{label} x:{x:.2f} y:{y:.2f}", (cx + 10, cy - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            # 发送 OSC 消息
            if label == 'Right':
                client.send_message("/pitch_hand", [x, y])
                # print(f"🎵 发送 /pitch_hand: {x:.2f}, {y:.2f}")
            elif label == 'Left':
                client.send_message("/volume_hand", [x, 1-y])
                # print(f"🔊 发送 /volume_hand: {x:.2f}, {y:.2f}")
    else:
        cv2.putText(img, "👋 未检测到手", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # 显示画面
    cv2.imshow("🎛️ Theremin Hand Tracker", img)

    # 退出条件：按下 q
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("👋 退出程序")
        break

    # 加帧率控制（可选，减少CPU负担）
    time.sleep(0.01)

# 清理资源
cap.release()
cv2.destroyAllWindows()
