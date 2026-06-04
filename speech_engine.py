"""
Speech Engine v3 - More reliable mic capture for Streamlit
Key fixes:
- Microphone opened once and reused (not reopened every loop)
- Longer timeout and phrase limit
- Better ambient noise calibration
- Clearer done/cancel signal detection
"""

import speech_recognition as sr
import pyttsx3
import threading
import logging

logger = logging.getLogger(__name__)

DONE_SIGNALS   = {"done", "execute", "go", "submit", "confirm", "do it", "run it", "ok go", "yes go"}
CANCEL_SIGNALS = {"cancel", "never mind", "nevermind", "forget it", "abort", "stop"}


# ─────────────────────────────────────────────────────────────────────────────
# TTS
# ─────────────────────────────────────────────────────────────────────────────

class TTSEngine:
    def __init__(self, rate: int = 175, volume: float = 1.0):
        self._engine = pyttsx3.init()
        self._engine.setProperty("rate", rate)
        self._engine.setProperty("volume", volume)
        voices = self._engine.getProperty("voices")
        for v in voices:
            if "female" in v.name.lower() or "zira" in v.name.lower():
                self._engine.setProperty("voice", v.id)
                break
        self._lock = threading.Lock()

    def speak(self, text: str) -> None:
        if not text:
            return
        with self._lock:
            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except RuntimeError as exc:
                logger.warning("TTS error: %s", exc)

    def speak_async(self, text: str) -> threading.Thread:
        t = threading.Thread(target=self.speak, args=(text,), daemon=True)
        t.start()
        return t

    def set_rate(self, rate: int) -> None:
        self._engine.setProperty("rate", rate)


# ─────────────────────────────────────────────────────────────────────────────
# Speech Recognition
# ─────────────────────────────────────────────────────────────────────────────

class SpeechEngine:
    WAKE_WORD = "hey assistant"

    def __init__(self, tts: TTSEngine = None):
        self.recognizer = sr.Recognizer()
        # More forgiving settings
        self.recognizer.energy_threshold        = 300   # lower = more sensitive
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold          = 1.0  # wait 1s of silence before ending
        self.recognizer.phrase_threshold         = 0.3
        self.recognizer.non_speaking_duration    = 0.5
        self.tts         = tts or TTSEngine()
        self._stop_event = threading.Event()
        self._listening  = False

    # ── Calibrate mic once ───────────────────────────────────────────────
    def _get_calibrated_mic(self):
        mic = sr.Microphone()
        with mic as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
        return mic

    # ── Single capture ───────────────────────────────────────────────────
    def _capture_once(self, mic, timeout=8, phrase_limit=15):
        """Capture one utterance using an already-open mic reference."""
        try:
            with mic as source:
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_limit,
                )
            text = self.recognizer.recognize_google(audio)
            logger.info("Recognized: %s", text)
            return text.lower().strip()
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as exc:
            logger.error("STT API error: %s", exc)
            return "__network_error__"
        except OSError as exc:
            logger.error("Mic error: %s", exc)
            return "__mic_error__"
        except Exception as exc:
            logger.error("Unexpected: %s", exc)
            return ""

    # ── Continuous mode ──────────────────────────────────────────────────
    def listen_continuous(self, on_command, on_status=None, wake_word=False):
        """
        Standard continuous mode — each utterance is an immediate command.
        """
        self._stop_event.clear()
        self._listening = True

        def _s(st): on_status and on_status(st)

        try:
            mic = self._get_calibrated_mic()
        except OSError:
            on_command("__mic_error__")
            self._listening = False
            return

        _s("Listening")
        while not self._stop_event.is_set():
            text = self._capture_once(mic)

            if self._stop_event.is_set():
                break
            if not text:
                continue
            if text in ("__mic_error__", "__network_error__"):
                on_command(text)
                if "mic" in text:
                    break
                continue

            # Wake word filter
            if wake_word and self.WAKE_WORD not in text:
                continue

            # Strip wake word from command
            if wake_word and self.WAKE_WORD in text:
                text = text.replace(self.WAKE_WORD, "").strip()
                if not text:
                    _s("Listening (wake word heard, speak your command)")
                    continue

            _s("Processing")
            on_command(text)
            if not self._stop_event.is_set():
                _s("Listening")

        self._listening = False
        _s("Idle")

    # ── Push-to-Talk mode ────────────────────────────────────────────────
    def listen_push_to_talk(self, on_partial, on_command, on_status=None):
        """
        PTT mode: accumulate speech chunks until user says 'Done' / 'Execute'.
        Say 'Cancel' to clear the buffer and start fresh.
        """
        self._stop_event.clear()
        self._listening = True

        def _s(st): on_status and on_status(st)

        try:
            mic = self._get_calibrated_mic()
        except OSError:
            on_command("__mic_error__")
            self._listening = False
            return

        _s("Push-to-Talk: Speak then say Done")
        accumulated = []

        while not self._stop_event.is_set():
            text = self._capture_once(mic, timeout=10, phrase_limit=20)

            if self._stop_event.is_set():
                break
            if not text:
                continue
            if text in ("__mic_error__", "__network_error__"):
                on_command(text)
                if "mic" in text:
                    break
                continue

            # Check cancel
            if any(sig in text for sig in CANCEL_SIGNALS):
                accumulated = []
                on_partial("(cancelled — speak your new command)")
                _s("Push-to-Talk: Cancelled. Speak again.")
                continue

            # Check for done signal
            done_triggered = any(sig in text for sig in DONE_SIGNALS)

            # Remove done/cancel words from the chunk
            clean = text
            for sig in DONE_SIGNALS | CANCEL_SIGNALS:
                clean = clean.replace(sig, "").strip()
            # Remove filler words
            for filler in [" okay ", " ok ", " please "]:
                clean = clean.replace(filler, " ").strip()

            if clean:
                accumulated.append(clean)
                on_partial(" ".join(accumulated))

            if done_triggered and accumulated:
                final = " ".join(accumulated).strip()
                accumulated = []
                on_partial("")
                _s("Processing")
                on_command(final)
                if not self._stop_event.is_set():
                    _s("Push-to-Talk: Speak then say Done")
            elif done_triggered and not accumulated:
                _s("Push-to-Talk: Nothing heard yet. Speak first then say Done.")

        self._listening = False
        _s("Idle")

    def stop(self):
        self._stop_event.set()

    @property
    def is_listening(self):
        return self._listening