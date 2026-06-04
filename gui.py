"""
Mini Voice Assistant GUI  v3
Fixed: background thread cannot access st.session_state.
Solution: pass all config as local variables into the thread at start time.
"""

import threading
import queue
import time
import datetime
import streamlit as st
from speech_engine import SpeechEngine, TTSEngine
from command_processor import CommandProcessor

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Mini Voice Assistant",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background: #0a0d14 !important;
    color: #c8d6e5 !important;
    font-family: 'Rajdhani', sans-serif;
}
[data-testid="stSidebar"] { background: #0d1117 !important; border-right: 1px solid #1e2a3a; }
[data-testid="stSidebar"] * { color: #8baabf !important; }

.va-title {
    font-family: 'Orbitron', monospace; font-size: 2.2rem; font-weight: 900;
    letter-spacing: .12em;
    background: linear-gradient(90deg,#00d4ff,#0080ff,#7b2ff7);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    text-align: center; padding: .4rem 0;
}
.va-subtitle {
    text-align: center; color: #4a7a9b; font-size: .9rem;
    letter-spacing: .25em; text-transform: uppercase; margin-bottom: 1rem;
}
.status-pill {
    display:inline-block; padding:.3rem 1.1rem; border-radius:999px;
    font-family:'Orbitron',monospace; font-size:.75rem; letter-spacing:.15em; font-weight:700;
}
.s-idle    { background:#1a2535; color:#4a7a9b; border:1px solid #1e2a3a; }
.s-listen  { background:#003020; color:#00ff80; border:1px solid #00ff8044;
              box-shadow:0 0 12px #00ff8033; animation:pulse 1.5s infinite; }
.s-ptt     { background:#002040; color:#00aaff; border:1px solid #00aaff44;
              box-shadow:0 0 12px #00aaff33; animation:pulse 1.5s infinite; }
.s-process { background:#201500; color:#ffaa00; border:1px solid #ffaa0044;
              box-shadow:0 0 12px #ffaa0033; }
.s-error   { background:#200010; color:#ff4466; border:1px solid #ff446644; }
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}

.va-box {
    background:#0d1117; border:1px solid #1e2a3a; border-radius:10px;
    padding:1rem 1.2rem; min-height:70px; font-size:1rem; color:#c8d6e5;
    line-height:1.6; white-space:pre-wrap; word-break:break-word;
}
.va-box-label {
    font-family:'Orbitron',monospace; font-size:.65rem; letter-spacing:.2em;
    color:#2a4a6a; text-transform:uppercase; margin-bottom:.35rem;
}
.resp-box    { border-color:#0050aa55; background:#080f1a; }
.speech-box  { border-color:#00aa5555; }
.partial-box { border-color:#00aaff44; background:#050d1a; color:#00aaff;
               font-size:.92rem; min-height:40px; }
.mode-info {
    background:#0d1a2a; border:1px solid #0050aa55; border-radius:8px;
    padding:.7rem 1rem; font-size:.88rem; color:#6a9abf; margin:.5rem 0 1rem;
}
.history-item {
    padding:.5rem .8rem; border-left:3px solid #0050aa; margin-bottom:.5rem;
    background:#0d1117; border-radius:0 6px 6px 0; font-size:.85rem;
}
.history-time { font-size:.7rem; color:#2a4a6a; }
.history-cmd  { color:#00aaff; margin:.15rem 0 .05rem; }
.history-resp { color:#7a9ab2; font-size:.82rem; }
.stButton>button {
    font-family:'Orbitron',monospace !important; font-weight:700 !important;
    letter-spacing:.1em !important; border-radius:8px !important;
    border:none !important; transition:all .2s ease !important;
}
hr { border-color:#1e2a3a !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state init ────────────────────────────────────────────────────────
def _init():
    defs = {
        "status":        "Idle",
        "speech_text":   "",
        "partial_text":  "",
        "response_text": "",
        "history":       [],
        "listening":     False,
        "tts_rate":      175,
        "wake_word":     False,
        "ptt_mode":      False,
        # Shared queues — safe to pass into threads
        "cmd_queue":     queue.Queue(),
        "status_queue":  queue.Queue(),
        "partial_queue": queue.Queue(),
        # Engine objects created once
        "tts":           None,
        "processor":     None,
        "engine":        None,
    }
    for k, v in defs.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Create heavy objects once
    if st.session_state["tts"] is None:
        st.session_state["tts"] = TTSEngine(rate=175)
    if st.session_state["processor"] is None:
        st.session_state["processor"] = CommandProcessor()

_init()

# ── Drain queues into session state (runs in main thread) ────────────────────
def drain():
    ss = st.session_state
    while not ss.status_queue.empty():
        ss.status = ss.status_queue.get_nowait()
    while not ss.partial_queue.empty():
        ss.partial_text = ss.partial_queue.get_nowait()
    while not ss.cmd_queue.empty():
        item = ss.cmd_queue.get_nowait()
        ss.speech_text   = item["cmd"]
        ss.partial_text  = ""
        ss.response_text = item["resp"]
        ss.history.insert(0, {
            "time": datetime.datetime.now().strftime("%H:%M:%S"),
            "cmd":  item["cmd"],
            "resp": item["resp"],
        })
        if len(ss.history) > 60:
            ss.history.pop()

drain()

# ── Thread worker — NO session_state access inside here ─────────────────────
def _listening_worker(engine, processor, tts, ptt_mode, wake_word,
                      cmd_q, status_q, partial_q, stop_event):
    """
    Runs entirely in a background thread.
    All config passed as plain Python values — zero st.session_state usage.
    """

    def on_command(text):
        if text in ("__mic_error__", "__network_error__"):
            resp = ("No microphone detected." if "mic" in text
                    else "Network error. Check your internet.")
            cmd_q.put({"cmd": text, "resp": resp})
            return
        resp = processor.process(text)
        display_resp = "Goodbye! Assistant stopped." if resp == "__EXIT__" else resp
        cmd_q.put({"cmd": text, "resp": display_resp})
        tts.speak_async(display_resp)
        if resp == "__EXIT__":
            stop_event.set()

    def on_status(s):
        status_q.put(s)

    def on_partial(p):
        partial_q.put(p)

    if ptt_mode:
        engine.listen_push_to_talk(
            on_partial=on_partial,
            on_command=on_command,
            on_status=on_status,
        )
    else:
        engine.listen_continuous(
            on_command=on_command,
            on_status=on_status,
            wake_word=wake_word,
        )

# ── Start / Stop ─────────────────────────────────────────────────────────────
def start_listening():
    ss = st.session_state
    if ss.listening:
        return

    ss.tts.set_rate(ss.tts_rate)

    # Snapshot config NOW in main thread — pass as plain values to thread
    ptt_mode  = bool(ss.ptt_mode)
    wake_word = bool(ss.wake_word)
    cmd_q     = ss.cmd_queue
    status_q  = ss.status_queue
    partial_q = ss.partial_queue
    processor = ss.processor
    tts       = ss.tts

    engine = SpeechEngine(tts=tts)
    ss.engine    = engine
    ss.listening = True
    ss.status    = "Push-to-Talk: Ready" if ptt_mode else "Listening"

    stop_event = threading.Event()

    t = threading.Thread(
        target=_listening_worker,
        args=(engine, processor, tts, ptt_mode, wake_word,
              cmd_q, status_q, partial_q, stop_event),
        daemon=True,
    )
    t.start()

    greet = ("Activated. Speak your command then say Done to execute."
             if ptt_mode else
             "Mini Voice Assistant activated. How can I help you?")
    tts.speak_async(greet)


def stop_listening():
    ss = st.session_state
    if not ss.listening:
        return
    if ss.engine:
        ss.engine.stop()
    ss.listening    = False
    ss.status       = "Idle"
    ss.partial_text = ""
    ss.tts.speak_async("Assistant stopped.")


def manual_command(text: str):
    ss = st.session_state
    resp = ss.processor.process(text)
    display = "Goodbye!" if resp == "__EXIT__" else resp
    ss.speech_text   = text
    ss.response_text = display
    ss.history.insert(0, {
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        "cmd": text, "resp": display,
    })
    ss.tts.speak_async(display)

# ── Status pill ───────────────────────────────────────────────────────────────
def _status_html(s: str) -> str:
    if "Push" in s or "PTT" in s or "Done" in s:
        cls, icon = "s-ptt",     "🎯"
    elif "Process" in s:
        cls, icon = "s-process", "◍"
    elif "Listen" in s:
        cls, icon = "s-listen",  "⬤"
    elif "Error" in s:
        cls, icon = "s-error",   "✕"
    else:
        cls, icon = "s-idle",    "◎"
    return f'<span class="status-pill {cls}">{icon} {s.upper()}</span>'

# ══════════════════════════════════════════════════════════════════════════════
# LAYOUT
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="va-title">🎙 Mini Voice Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="va-subtitle">V3 · Push-to-Talk · Smart Commands · Dark Mode</div>', unsafe_allow_html=True)
st.markdown(f"<center>{_status_html(st.session_state.status)}</center>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

col_main, col_hist = st.columns([3, 2], gap="large")

with col_main:
    # Mode info banner
    if st.session_state.ptt_mode:
        st.markdown(
            '<div class="mode-info">🎯 <b>Push-to-Talk ON:</b> Speak your command → '
            'say <b>"Done"</b> / "Execute" / "Go" → runs immediately. '
            'Say <b>"Cancel"</b> to clear and retry.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="mode-info">🎤 <b>Continuous Mode:</b> '
            'Every utterance is processed as a command immediately.</div>',
            unsafe_allow_html=True,
        )

    # Control buttons
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("▶  Start Listening", use_container_width=True,
                     disabled=st.session_state.listening):
            start_listening()
            st.rerun()
    with b2:
        if st.button("■  Stop Listening", use_container_width=True,
                     disabled=not st.session_state.listening):
            stop_listening()
            st.rerun()
    with b3:
        if st.button("🗑  Clear History", use_container_width=True):
            st.session_state.history       = []
            st.session_state.speech_text   = ""
            st.session_state.response_text = ""
            st.session_state.partial_text  = ""
            st.rerun()

    st.markdown("---")

    # PTT partial preview
    if st.session_state.ptt_mode:
        st.markdown('<div class="va-box-label">🎯 Building Command (say "Done" to execute)</div>',
                    unsafe_allow_html=True)
        partial = (st.session_state.partial_text
                   or "<span style='color:#1e3a5a'>Waiting for speech…</span>")
        st.markdown(f'<div class="va-box partial-box">{partial}</div>',
                    unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # Recognised speech
    st.markdown('<div class="va-box-label">🎤 Recognised Speech</div>', unsafe_allow_html=True)
    speech = (st.session_state.speech_text
              or "<span style='color:#1e3a5a'>Waiting for voice input…</span>")
    st.markdown(f'<div class="va-box speech-box">{speech}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Assistant response
    st.markdown('<div class="va-box-label">🤖 Assistant Response</div>', unsafe_allow_html=True)
    resp = st.session_state.response_text
    disp = (resp.replace("\n","<br>") if resp
            else "<span style='color:#1e3a5a'>No response yet…</span>")
    st.markdown(f'<div class="va-box resp-box">{disp}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Manual text input
    st.markdown('<div class="va-box-label">⌨️ Type a Command (no mic needed)</div>',
                unsafe_allow_html=True)
    typed = st.text_input(
        "Type command",
        placeholder="e.g. play Hamasafar on YouTube, meaning of serendipity, weather in Nashik",
        label_visibility="hidden",
    )
    if st.button("▶  Send Command", use_container_width=True) and typed.strip():
        manual_command(typed.strip())
        st.rerun()

# History panel
with col_hist:
    st.markdown('<div class="va-box-label">📋 Command History</div>', unsafe_allow_html=True)
    hist = st.session_state.history
    if not hist:
        st.markdown('<div class="va-box" style="color:#1e3a5a">No commands yet.</div>',
                    unsafe_allow_html=True)
    else:
        for item in hist:
            prev = item["resp"][:90] + "…" if len(item["resp"]) > 90 else item["resp"]
            st.markdown(
                f'<div class="history-item">'
                f'<div class="history-time">{item["time"]}</div>'
                f'<div class="history-cmd">▸ {item["cmd"]}</div>'
                f'<div class="history-resp">{prev}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    st.markdown("---")

    new_rate = st.slider("Speech Rate (words/min)", 100, 250,
                         st.session_state.tts_rate, 10)
    if new_rate != st.session_state.tts_rate:
        st.session_state.tts_rate = new_rate
        st.session_state.tts.set_rate(new_rate)

    st.markdown("---")

    ptt = st.toggle("🎯 Push-to-Talk Mode",
                    value=st.session_state.ptt_mode,
                    help="Speak → say 'Done' to execute. No accidental triggers.")
    if ptt != st.session_state.ptt_mode:
        st.session_state.ptt_mode = ptt

    wake = st.toggle("🔔 Wake Word ('Hey Assistant')",
                     value=st.session_state.wake_word,
                     help="Only responds after you say 'Hey Assistant'.")
    if wake != st.session_state.wake_word:
        st.session_state.wake_word = wake

    st.markdown("---")
    st.markdown("### 💬 Commands")

    categories = {
        "🖥 Apps":        ["Open Chrome / Notepad / Calculator",
                           "Open VS Code / Word / Excel / PowerPoint",
                           "Open Terminal / Paint / Spotify / VLC"],
        "🌐 Websites":    ["Open YouTube / Google / Gmail",
                           "Open GitHub / WhatsApp / Netflix",
                           "Open Wikipedia / Reddit / LinkedIn"],
        "🔍 Smart Search":["Search Google for <query>",
                           "Meaning of <word>",
                           "Weather in <city>",
                           "News about <topic>",
                           "Map of <place>",
                           "Translate <text> to Hindi",
                           "Wikipedia <topic>",
                           "Images of <query>"],
        "▶ YouTube":      ["Play <song> on YouTube",
                           "Search YouTube for <query>"],
        "📝 Notes":       ["Create note <text>",
                           "Read my notes", "Clear notes"],
        "⏰ Info":         ["What time is it", "Today's date",
                           "System information", "Tell me a joke"],
        "🎯 PTT Signals": ["Say 'Done' / 'Execute' / 'Go' → run",
                           "Say 'Cancel' → clear and retry"],
    }
    for cat, items in categories.items():
        with st.expander(cat, expanded=False):
            for c in items:
                st.markdown(f"• {c}")

    st.markdown("---")
    st.markdown(
        "<small style='color:#2a4a6a'>Mini Voice Assistant v3<br>"
        "Python · Streamlit · pyttsx3</small>",
        unsafe_allow_html=True,
    )

# Auto-refresh while listening
if st.session_state.listening:
    time.sleep(0.8)
    st.rerun()