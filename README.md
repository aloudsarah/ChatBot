# Voice-to-Voice AI assistant
In this repository, you will find the complete implementation of a real-time Arabic voice assistant and its interactive holographic web interface. The system creates an end-to-end speech-to-speech pipeline combining local speech recognition (STT), Cohere's Large Language Model (LLM), and speech synthesis (TTS) synchronized via WebSockets.
## Project Structure
- ```app.py```: The backend server managing STT, Cohere API, TTS playback, and WebSocket broadcasting.  
- ```index.html```: The state-driven frontend interface featuring dynamic orb animations, a sliding chat drawer, and theme toggling.
## Prerequisites
- Python 3.9-3.11
- API key from the **[Cohere Dashboard](https://dashboard.cohere.com/)**
## Setup and Installation
### 1. Prepare the Folder
Ensure that both `app.py` and `index.html` are located in the same directory.
### 2. Dependencies 
Open  your terminal (Terminal / PowerShell / Anaconda Prompt) and install the required dependencies:
```bash
pip install fastapi uvicorn websockets cohere gTTS pygame RealtimeSTT
```
### 3. Configure Cohere API key
Open ```app.py``` file and insert your personal Cohere API key:
```python
COHERE_API_KEY = "YOUR_COHERE_API_KEY_HERE"
```
### 4. Run the Project
Start the application server using Python:
```bash
python app.py
```
### 5. Access the Web Interface
Open your web browser and navigate to:
[http://127.0.0.1:8000](http://127.0.0.1:8000)
## Python Code Analysis ```app.py```
The backend script coordinates concurrent local audio processing, asynchronous networking, and LLM inference.
### Imports and Dependencies
- ```asyncio```: Handles asynchronous I/O and threadsafe message dispatching across event loops.
- ```threading```: Runs the continuous audio listening loop in a background daemon thread to prevent blocking the server.
- ```FastAPI``` and ```WebSocket```: Powers the web server and full-duplex communication channel for live state updates.
- ```cohere```: Connects to Cohere's API for natural language understanding and contextual response generation.
- ```gTTS```: Synthesizes Arabic response strings into temporary .mp3 audio files.   
- ```pygame.mixer```: Manages local audio playback reliably across platforms without file-path encoding conflicts 
- ```RealtimeSTT.AudioToTextRecorder```: Provides local, real-time Arabic speech-to-text inference running on CPU
### Core Functions Breakdown
##### 1. WebSocket Notification ```send_to_ui```
```python
def send_to_ui(payload):
    global active_websocket, loop
    if active_websocket and loop:
        asyncio.run_coroutine_threadsafe(active_websocket.send_json(payload), loop)
```
- **Role:** Sends JSON status updates to the browser interface.
- **Mechanism:** Uses ```asyncio.run_coroutine_threadsafe``` to safely bridge background worker threads with FastAPI's main async event loop.
#### 2. Speech Synthesis and Playback ```speak```
```python
def speak(text):
    ...
```
- **Role:** Converts generated text to speech and updates visual state.
- **Workflow:**
  1. Calls ```recorder.stop()``` to pause the microphone and avoid capturing self-audio.
  2. Broadcasts the ```speaking``` state and assistant text to the UI.
  3. Synthesizes Arabic audio with ```gTTS``` and saves it to a unique timestamped file.
  4. Plays audio via  ```pygame.mixer.music ``` until playback finishes.
  5. Cleans up temporary audio files, notifies the UI to return to ```listening```, and resumes microphone recording (```recorder.listen()```).
#### 3. LLM Generation and Context Tracking ```get_ai_response```
```python
def get_ai_response(user_text):
    response = co.chat(
        message=user_text,
        chat_history=chat_history,
    )
    chat_history.append({"role": "USER", "message": user_text})
    chat_history.append({"role": "CHATBOT", "message": response.text})
    return response.text
```
- **Role:** Sends prompt data to Cohere's chat endpoint while preserving chat history.
- **Mechanism:** Maintains the ```chat_history``` list by appending ```USER``` and ```CHATBOT``` turns, allowing the assistant to follow multi-turn dialogue context.
#### 4. Real-Time Speech Callback ```on_text_detected```
```python
def on_text_detected(text):
    if not text.strip():
        return
    send_to_ui({"state": "thinking", "user_text": text})
    ai_reply = get_ai_response(text)
    speak(ai_reply)
```
- **Role:** Triggered automatically whenever ```RealtimeSTT```detects and transcribes a completed spoken sentence.
- **Mechanism:** Filters out empty strings, switches the UI state to ```thinking```, displays the user query, queries Cohere, and invokes ```speak()```.
#### 5. Lifecycle and Server Startup ```lifespan```
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    t = threading.Thread(target=run_recorder_loop, daemon=True)
    t.start()
    yield
    if recorder:
        recorder.shutdown()
```
- **Role:** Manages application startup and teardown.
- **Mechanism:** Spawns ```run_recorder_loop``` in a background daemon thread upon server boot and ensures ```recorder.shutdown()``` executes on exit.
## Frontend Code Analysis ```index.html```
The frontend is a single-file, state-driven interface built with HTML5, CSS3, and JavaScript
- **State-Driven Holographic Orb:** Utilizes dynamic CSS keyframes (```pulseListening```, ```rotateThinking```, ```speakWave```) that reflect real-time backend pipeline states (```idle```, ```listening```, ```thinking```, ```speaking```).
- **Responsive Layout Adaptation:** Automatically shrinks the central orb into a compact header widget when the chat transcript is opened (```.container.chat-open```), preventing layout overlap.
- **Live WebSocket Client:** Connects to ```/ws``` on load to receive real-time state flags and render chat bubbles.
- **Theme Switching:** Supports toggling between Dark Mode and Light Mode with synced color variables and glow effects.
### Interface Preview
- Light Mode
<img width="679" height="906" alt="‫المساعد الصوتي - Light" src="https://github.com/user-attachments/assets/2a67c855-4b41-4dfe-9a82-b7a1066a8932" />

- Dark Mode
<img width="672" height="896" alt="‫المساعد الصوتي - Dark" src="https://github.com/user-attachments/assets/49d085d2-b196-4222-857c-ee1b92273a13" />

