# 🎙️ Mini Voice Assistant

A complete Python voice assistant with speech recognition, text-to-speech, desktop automation, notes management, and a sleek dark-mode Streamlit GUI.

---

## 📁 Project Structure

```
voice_assistant/
├── main.py               ← CLI entry point
├── gui.py                ← Streamlit GUI (recommended)
├── speech_engine.py      ← Module 1 & 4: STT + TTS
├── command_processor.py  ← Module 2: Intent matching & routing
├── automation.py         ← Module 3: App/website launcher
├── notes_manager.py      ← Module 5: Notes save/read
├── requirements.txt      ← All dependencies
├── notes.txt             ← Created automatically when you save notes
└── README.md
```

---

## ⚙️ Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.11 + |
| pip | latest |
| Windows | 10 / 11 (recommended) |
| Microphone | Required for voice input |
| Internet | Required for Google Speech API |

---

## 🚀 Installation (Step-by-Step)

### Step 1 — Clone or download the project
```bash
# if using git
git clone https://github.com/your-username/mini-voice-assistant.git
cd mini-voice-assistant

# or just unzip the folder and open a terminal inside it
```

### Step 2 — Create a virtual environment (recommended)
```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
```

### Step 3 — Install PyAudio (Windows-specific fix)
PyAudio requires a pre-built wheel on Windows:
```bash
pip install pipwin
pipwin install pyaudio
```
> **Alternative:** Download the `.whl` from https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio  
> Then: `pip install PyAudio‑0.2.14‑cp311‑cp311‑win_amd64.whl`

### Step 4 — Install all other requirements
```bash
pip install -r requirements.txt
```

### Step 5 — Run the GUI (recommended)
```bash
streamlit run gui.py
```
The app opens automatically at **http://localhost:8501**

### Step 6 (optional) — Run the CLI version
```bash
python main.py
```

---

## 🎤 How to Use

### GUI Mode
1. Open the app in your browser (`streamlit run gui.py`)
2. Click **▶ Start Listening** — the status pill turns green
3. Speak a command clearly into your microphone
4. See the recognized text and assistant response appear live
5. Click **■ Stop Listening** when done
6. Use the **Type a Command** box if you don't have a mic

### CLI Mode
1. Run `python main.py`
2. Choose `[1] Listen` or `[2] Type command`
3. Speak or type your command
4. Type `exit` or choose `[3]` to quit

---

## 🗣️ Supported Voice Commands

| Command | Example |
|---|---|
| Open Chrome | "open chrome" |
| Open Notepad | "open notepad" |
| Open Calculator | "open calculator" |
| Open VS Code | "open vs code" |
| Open YouTube | "open youtube" |
| Open Google | "open google" |
| Search Google | "search google for Python tutorials" |
| Search YouTube | "search youtube for lo-fi music" |
| Tell time | "what time is it" |
| Tell date | "what is today's date" |
| Tell a joke | "tell me a joke" |
| System info | "show system information" |
| Create a note | "create note buy groceries" |
| Read notes | "read my notes" |
| Clear notes | "clear my notes" |
| Exit | "exit" / "goodbye" |

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| `PyAudio` install error | Use `pipwin install pyaudio` (see Step 3) |
| "No microphone detected" | Check Windows Sound settings → Recording devices |
| "Network unavailable" | Check your internet; Google STT needs a connection |
| App doesn't open browser | Make sure Chrome/Edge is your default browser |
| `pyttsx3` silent | Try plugging in headphones or speakers |
| Streamlit not found | Run `pip install streamlit` again |

---

## 📦 Dependencies

```
SpeechRecognition  — Converts mic input to text (Google STT API)
pyttsx3            — Offline text-to-speech engine
streamlit          — Modern web-based GUI framework
pyaudio            — Microphone capture backend
pyjokes            — Random programmer jokes
psutil             — CPU / RAM / Disk system info
pyautogui          — Optional GUI automation
Pillow             — Image handling (Streamlit dependency)
```

---

## 🎛️ Settings (Sidebar)

- **Speech Rate slider** — Adjust how fast the assistant speaks (100–250 wpm)
- **Wake Word Mode** — When ON, the assistant only processes commands after hearing *"Hey Assistant"*

---

## 📝 Notes Storage

Notes are saved to `notes.txt` in the project folder.  
Each note is timestamped automatically:
```
[2025-06-01 14:30] buy groceries
[2025-06-01 15:00] call the dentist
```

---

## 🧩 Module Breakdown

| File | Responsibility |
|---|---|
| `speech_engine.py` | Mic capture, Google STT, pyttsx3 TTS, continuous listening loop |
| `command_processor.py` | Keyword-based intent detection, routes to correct handler |
| `automation.py` | Launches apps (os/subprocess), opens URLs (webbrowser), searches |
| `notes_manager.py` | Appends/reads/clears `notes.txt` |
| `gui.py` | Full Streamlit UI: status pill, speech/response panels, history |
| `main.py` | Minimal CLI for headless/terminal use |

---

## 🔮 Extending the Assistant

To add a new command:
1. Open `command_processor.py`
2. Add a new `if` block in the `process()` method
3. Call your handler function from `automation.py` or inline

Example — add "flip a coin":
```python
if "flip" in text and "coin" in text:
    import random
    return "Heads!" if random.random() > 0.5 else "Tails!"
```

---

*Mini Voice Assistant v1.0 — Built with Python, Streamlit, and ❤️*
