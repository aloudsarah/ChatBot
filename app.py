import asyncio
import os
import threading
import time
from contextlib import asynccontextmanager
import cohere
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from gtts import gTTS
from playsound import playsound
from RealtimeSTT import AudioToTextRecorder
import pygame
import uvicorn

COHERE_API_KEY = "YOUR_COHERE_API_KEY_HERE"

co = cohere.Client(COHERE_API_KEY)
REPLY_DIR = os.path.dirname(os.path.abspath(__file__))

chat_history = []
recorder = None
active_websocket = None
loop = None

# ============================================
# 2. وظيفة إرسال الحالات للواجهة عبر WebSocket
# ============================================
def send_to_ui(payload):
    global active_websocket, loop
    if active_websocket and loop:
        asyncio.run_coroutine_threadsafe(active_websocket.send_json(payload), loop)

# ============================================
# 3. محرك الصوت والتوليد
# ============================================
pygame.mixer.init()

def speak(text):
    global recorder
    print(f"الشات بوت: {text}", flush=True)

    if recorder is not None:
        recorder.stop()

    send_to_ui({"state": "speaking", "assistant_text": text})

    reply_path = os.path.join(REPLY_DIR, f"_reply_{int(time.time() * 1000)}.mp3")
    
    # 1. حفظ الصوت عبر gTTS
    tts = gTTS(text=text, lang="ar")
    tts.save(reply_path)

    # 2. تشغيل الصوت عبر pygame بدلاً من playsound
    try:
        pygame.mixer.music.load(reply_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        pygame.mixer.music.unload()
    except Exception as e:
        print("خطأ في تشغيل الصوت:", e)

    # 3. حذف الملف المؤقت
    try:
        os.remove(reply_path)
    except OSError:
        pass

    send_to_ui({"state": "listening"})

    if recorder is not None:
        recorder.listen()

def get_ai_response(user_text):
    response = co.chat(
        message=user_text,
        chat_history=chat_history,
    )
    chat_history.append({"role": "USER", "message": user_text})
    chat_history.append({"role": "CHATBOT", "message": response.text})
    return response.text

def on_text_detected(text):
    if not text.strip():
        return

    print(f"أنتِ: {text}", flush=True)
    
    send_to_ui({
        "state": "thinking",
        "user_text": text
    })

    ai_reply = get_ai_response(text)
    speak(ai_reply)

# ============================================
# 4. تشغيل RealtimeSTT في مسار منفصل (Thread)
# ============================================
def run_recorder_loop():
    global recorder
    print(">>> جاري تجهيز RealtimeSTT...", flush=True)
    recorder = AudioToTextRecorder(
        model="small",
        language="ar",
        device="cpu",
        compute_type="int8",
        spinner=False,
    )
    print(">>> المستمع جاهز للتسجيل في الخلفية!", flush=True)
    while True:
        recorder.text(on_text_detected)

# ============================================
# 5. إدارة دورة حياة التطبيق (Lifespan الحديثة بدلاً من on_event)
# ============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # كود الإقلاع (Startup)
    t = threading.Thread(target=run_recorder_loop, daemon=True)
    t.start()
    yield
    # كود الإغلاق (Shutdown)
    if recorder:
        recorder.shutdown()

app = FastAPI(lifespan=lifespan)

# ============================================
# 6. واجهات الويب و WebSocket
# ============================================
@app.get("/")
async def get_ui():
    html_path = os.path.join(REPLY_DIR, "!DOCTYPE html_2.html")
    # إذا كان اسم الملف عندك index.html غيري السطر أعلاه إلى "index.html"
    if not os.path.exists(html_path):
        html_path = os.path.join(REPLY_DIR, "index.html")

    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global active_websocket, loop
    await websocket.accept()
    active_websocket = websocket
    loop = asyncio.get_running_loop()
    print("تم اتصال الواجهة بنجاح!")
    
    send_to_ui({"state": "listening"})
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_websocket = None
        print("انقطع اتصال الواجهة.")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)