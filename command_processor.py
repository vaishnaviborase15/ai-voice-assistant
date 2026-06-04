"""
Module 2: Command Processor  (v2 — enhanced with smart NLP-style parsing)
Handles specific commands like "search meaning of X", "play X on YouTube", etc.
"""

import datetime
import random
import re
import logging

logger = logging.getLogger(__name__)

try:
    import pyjokes
    _JOKES_AVAILABLE = True
except ImportError:
    _JOKES_AVAILABLE = False

from automation import (
    open_application, open_website, open_named_website,
    search_google, google_meaning, google_news, google_images,
    google_maps, google_translate,
    search_youtube, play_youtube,
    search_wikipedia, weather_search, calculate,
    get_system_info,
)
from notes_manager import create_note, read_notes, clear_notes

_FALLBACK_JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs!",
    "I told my computer I needed a break. Now it won't stop sending me Kit-Kat ads.",
    "Why did the developer go broke? Because he used up all his cache.",
    "There are 10 types of people: those who understand binary, and those who don't.",
    "A SQL query walks into a bar and asks two tables: 'Can I join you?'",
    "Why was the math book sad? It had too many problems.",
    "What do you call a fish without eyes? A fsh.",
    "I'm reading a book on anti-gravity. It's impossible to put down.",
]

def _joke() -> str:
    return pyjokes.get_joke() if _JOKES_AVAILABLE else random.choice(_FALLBACK_JOKES)

# ─────────────────────────────────────────────────────────────────────────────
# Helper: extract query after a pattern
# ─────────────────────────────────────────────────────────────────────────────

def _after(text: str, *phrases) -> str:
    """Return text after the first matching phrase (longest first)."""
    for p in sorted(phrases, key=len, reverse=True):
        if p in text:
            return text.split(p, 1)[1].strip()
    return ""


def _between(text: str, start: str, end_words=None) -> str:
    """Return text between start phrase and optional end word."""
    if start not in text:
        return ""
    part = text.split(start, 1)[1].strip()
    if end_words:
        for w in end_words:
            if w in part:
                part = part.split(w, 1)[0].strip()
    return part


# ─────────────────────────────────────────────────────────────────────────────
# All supported sites list (for "open X" fallback)
# ─────────────────────────────────────────────────────────────────────────────
_KNOWN_SITES = [
    "youtube","google","github","stackoverflow","gmail","whatsapp",
    "linkedin","twitter","instagram","facebook","reddit","netflix",
    "amazon","flipkart","wikipedia","maps","translate","chatgpt",
]

_KNOWN_APPS = [
    "chrome","notepad","calculator","vs code","vscode","file explorer",
    "terminal","cmd","word","excel","powerpoint","paint","task manager",
    "settings","camera","spotify","vlc","snipping tool",
]


class CommandProcessor:

    def process(self, text: str) -> str:
        t = text.lower().strip()

        # ── Error tokens ──────────────────────────────────────────────────
        if t == "__mic_error__":
            return "No microphone detected. Please check your audio input device."
        if t == "__network_error__":
            return "Network unavailable. Please check your internet connection."

        # ── Exit ──────────────────────────────────────────────────────────
        if any(w in t for w in ("exit","quit","goodbye","bye","stop assistant","shut down")):
            return "__EXIT__"

        # ── Greet ─────────────────────────────────────────────────────────
        if re.match(r"^(hi|hello|hey|howdy|what's up|whatsup)(\s|$)", t):
            return "Hello! I'm your Mini Voice Assistant. How can I help you?"

        # ── Help ──────────────────────────────────────────────────────────
        if "help" in t or "what can you do" in t or "commands" in t:
            return self._help()

        # ── Time & Date ───────────────────────────────────────────────────
        if re.search(r"\btime\b", t) and "what" in t or t == "time":
            return "The current time is " + datetime.datetime.now().strftime("%I:%M %p")
        if "date" in t or "today" in t and "day" in t:
            return "Today is " + datetime.datetime.now().strftime("%A, %B %d, %Y")
        if "day" in t and "what" in t:
            return "Today is " + datetime.datetime.now().strftime("%A")
        if "year" in t:
            return "The current year is " + datetime.datetime.now().strftime("%Y")

        # ── Jokes ─────────────────────────────────────────────────────────
        if "joke" in t:
            return _joke()

        # ── System info ───────────────────────────────────────────────────
        if ("system" in t and ("info" in t or "information" in t)) or "cpu" in t or "ram" in t or "memory" in t:
            return get_system_info()

        # ═══════════════════════════════════════════════════════════════════
        # SPECIFIC / SMART SEARCHES
        # ═══════════════════════════════════════════════════════════════════

        # ── Meaning / definition ──────────────────────────────────────────
        # "search the meaning of conspiracy on google"
        # "what is the meaning of serendipity"
        # "define quantum"
        m = re.search(r"(?:meaning of|definition of|define|what does .+ mean|what is .+)\s+(.+?)(?:\s+on google)?$", t)
        if m and ("meaning" in t or "definition" in t or "define" in t):
            word = _after(t, "meaning of", "definition of", "define", "meaning").split(" on ")[0].strip()
            if not word:
                word = m.group(1).strip()
            return google_meaning(word) if word else "What word would you like me to look up?"

        # ── Play a song on YouTube ────────────────────────────────────────
        # "play hamasafar song on youtube" / "play despacito" / "play some jazz"
        if "play" in t:
            query = _after(t, "play")
            for stop in [" on youtube", " on yt", " song", " music", " video"]:
                query = query.replace(stop, "")
            query = query.strip()
            if query:
                return play_youtube(query + " song")
            return "What song or video would you like me to play?"

        # ── YouTube search (generic) ──────────────────────────────────────
        for pat in ("search youtube for", "youtube search for", "search on youtube for",
                    "search on youtube", "look up on youtube"):
            if pat in t:
                q = _after(t, pat)
                return search_youtube(q) if q else "What should I search on YouTube?"

        # ── Google Images ─────────────────────────────────────────────────
        if ("image" in t or "images" in t or "photo" in t or "picture" in t) and "google" in t:
            q = _after(t, "images of", "image of", "pictures of", "photo of", "photos of", "google images")
            q = q.replace(" on google", "").replace(" google", "").strip()
            return google_images(q) if q else search_google("images")

        # ── Weather ───────────────────────────────────────────────────────
        if "weather" in t:
            city = _after(t, "weather in", "weather of", "weather for", "weather at", "weather")
            city = city.replace(" today", "").replace(" now", "").strip()
            return weather_search(city) if city else weather_search("current location")

        # ── Maps / directions ─────────────────────────────────────────────
        if "map" in t or "direction" in t or "navigate to" in t or "where is" in t:
            loc = _after(t, "map of", "maps for", "directions to", "navigate to",
                         "where is", "location of", "map", "maps")
            return google_maps(loc) if loc else open_website("https://maps.google.com", "Google Maps")

        # ── Translate ─────────────────────────────────────────────────────
        if "translate" in t:
            phrase = _after(t, "translate", "translation of")
            # detect target language e.g. "translate hello to french"
            lang_map = {"hindi":"hi","french":"fr","spanish":"es","german":"de",
                        "japanese":"ja","arabic":"ar","chinese":"zh","marathi":"mr",
                        "telugu":"te","tamil":"ta","kannada":"kn","bengali":"bn"}
            tl = "en"
            for lang, code in lang_map.items():
                if lang in phrase:
                    phrase = phrase.replace(f" to {lang}", "").strip()
                    tl = code
                    break
            return google_translate(phrase, tl) if phrase else open_website("https://translate.google.com", "Google Translate")

        # ── Wikipedia ─────────────────────────────────────────────────────
        if "wikipedia" in t or ("wiki" in t and "search" in t):
            q = _after(t, "search wikipedia for", "wikipedia for", "wikipedia about", "wiki")
            return search_wikipedia(q) if q else open_website("https://www.wikipedia.org", "Wikipedia")

        # ── News ──────────────────────────────────────────────────────────
        if "news" in t:
            topic = _after(t, "news about", "news on", "news for", "latest news on",
                           "latest news about", "news")
            topic = topic.replace(" today", "").replace(" latest", "").strip()
            return google_news(topic)

        # ── Calculate ─────────────────────────────────────────────────────
        if "calculate" in t or "what is" in t and any(op in t for op in ["+","-","*","/","x","percent","square","root"]):
            expr = _after(t, "calculate", "what is", "compute", "solve")
            return calculate(expr) if expr else open_application("calculator")

        # ── Google search (specific patterns) ────────────────────────────
        for pat in ("search google for","search for","google search for","search on google for",
                    "search on google","look up on google","look up","search"):
            if pat in t:
                q = _after(t, pat)
                if q:
                    return search_google(q)

        # ── Open website (named) ──────────────────────────────────────────
        for site in _KNOWN_SITES:
            if site in t and "open" in t:
                return open_named_website(site)

        # ── Open application ──────────────────────────────────────────────
        for app in _KNOWN_APPS:
            if app in t and ("open" in t or "launch" in t or "start" in t):
                return open_application(app)
        # Shorthand (no "open" keyword needed)
        for app in ["calculator","notepad","paint","task manager","terminal","cmd"]:
            if app in t:
                return open_application(app)

        # ── Notes ─────────────────────────────────────────────────────────
        if "read" in t and "note" in t:
            return read_notes()
        if "clear" in t and "note" in t:
            return clear_notes()
        if any(k in t for k in ("create note","save note","take note","write note","note that","add note")):
            content = _after(t, "create note","save note","take note","write note","note that","add note","note")
            return create_note(content) if content else "What would you like to note?"

        # ── Generic "open <thing>" fallback ──────────────────────────────
        if "open" in t or "launch" in t:
            target = _after(t, "open", "launch").strip()
            if target:
                # check if it looks like a website
                if any(c in target for c in [".", "www", "http"]):
                    return open_website(f"https://{target}" if not target.startswith("http") else target, target)
                # try as app, then as site
                res = open_application(target)
                if "don't know" in res:
                    return open_named_website(target)
                return res

        # ── Unknown ───────────────────────────────────────────────────────
        return (
            f"I heard: '{text}'. I'm not sure how to handle that. "
            "Say 'help' to see all available commands."
        )

    # ─────────────────────────────────────────────────────────────────────
    @staticmethod
    def _help() -> str:
        return (
            "Here's what I can do:\n"
            "• Open apps: Chrome, Notepad, Calculator, VS Code, Word, Excel, Paint, Spotify…\n"
            "• Open websites: YouTube, Google, GitHub, Gmail, WhatsApp, Netflix…\n"
            "• Play a song: 'Play Hamasafar on YouTube'\n"
            "• Search Google: 'Search Google for Python tutorials'\n"
            "• Get meaning: 'Search the meaning of conspiracy on Google'\n"
            "• Weather: 'Weather in Mumbai'\n"
            "• Translate: 'Translate hello to Hindi'\n"
            "• Maps: 'Show map of Nashik'\n"
            "• News: 'Latest news about technology'\n"
            "• Wikipedia: 'Search Wikipedia for black hole'\n"
            "• Tell the time or date\n"
            "• Tell a joke | System information\n"
            "• Create / Read / Clear notes\n"
            "• Say 'exit' to quit"
        )
