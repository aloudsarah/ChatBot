

import cohere
from RealtimeSTT import AudioToTextRecorder
from RealtimeTTS import TextToAudioStream, SystemEngine


COHERE_API_KEY = ""

co = cohere.Client(COHERE_API_KEY)

#
tts_engine = SystemEngine()
tts_stream = TextToAudioStream(tts_engine)


chat_history = []


def speak(text):
    
    print(f"الشات بوت: {text}", flush=True)
    tts_stream.feed(text)
    tts_stream.play()


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
    ai_reply = get_ai_response(text)
    speak(ai_reply)


def main():
    print(">>> جاري تجهيز النظام (تحميل نموذج التعرف على الصوت)...", flush=True)

    recorder = AudioToTextRecorder(
        model="small",
        language="ar",
        device="cpu",
        compute_type="int8",
        spinner=False,
    )

    print(">>> النظام جاهز! تكلمي بالعربي (اضغطي Ctrl+C للخروج)", flush=True)

    try:
        while True:

            recorder.text(on_text_detected)
    except KeyboardInterrupt:
        print(">>> تم إيقاف البرنامج.", flush=True)
    finally:
        recorder.shutdown()


if __name__ == "__main__":
    main()