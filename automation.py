"""
Module 3: Automation Engine  (v2 — enhanced)
Opens apps, websites, performs specific searches, plays songs, looks up meanings, etc.
"""

import os
import webbrowser
import subprocess
import platform
import logging
import urllib.parse

logger = logging.getLogger(__name__)
SYSTEM = platform.system()   # "Windows" | "Darwin" | "Linux"

# ─────────────────────────────────────────────────────────────────────────────
# App map  (extended)
# ─────────────────────────────────────────────────────────────────────────────
_APP_MAP = {
    "chrome":        {"Windows": "start chrome",          "Darwin": "open -a 'Google Chrome'",      "Linux": "google-chrome"},
    "notepad":       {"Windows": "notepad",               "Darwin": "open -a TextEdit",              "Linux": "gedit"},
    "calculator":    {"Windows": "calc",                  "Darwin": "open -a Calculator",            "Linux": "gnome-calculator"},
    "vs code":       {"Windows": "code",                  "Darwin": "open -a 'Visual Studio Code'",  "Linux": "code"},
    "vscode":        {"Windows": "code",                  "Darwin": "open -a 'Visual Studio Code'",  "Linux": "code"},
    "file explorer": {"Windows": "explorer",              "Darwin": "open .",                        "Linux": "nautilus"},
    "terminal":      {"Windows": "start cmd",             "Darwin": "open -a Terminal",              "Linux": "gnome-terminal"},
    "cmd":           {"Windows": "start cmd",             "Darwin": "open -a Terminal",              "Linux": "gnome-terminal"},
    "word":          {"Windows": "start winword",         "Darwin": "open -a 'Microsoft Word'",      "Linux": "libreoffice --writer"},
    "excel":         {"Windows": "start excel",           "Darwin": "open -a 'Microsoft Excel'",     "Linux": "libreoffice --calc"},
    "powerpoint":    {"Windows": "start powerpnt",        "Darwin": "open -a 'Microsoft PowerPoint'","Linux": "libreoffice --impress"},
    "paint":         {"Windows": "mspaint",               "Darwin": "open -a Paintbrush",            "Linux": "gimp"},
    "task manager":  {"Windows": "taskmgr",               "Darwin": "open -a 'Activity Monitor'",    "Linux": "gnome-system-monitor"},
    "settings":      {"Windows": "start ms-settings:",   "Darwin": "open -a 'System Preferences'",  "Linux": "gnome-control-center"},
    "camera":        {"Windows": "start microsoft.windows.camera:", "Darwin": "open -a Photo Booth", "Linux": "cheese"},
    "spotify":       {"Windows": "start spotify",         "Darwin": "open -a Spotify",               "Linux": "spotify"},
    "vlc":           {"Windows": "start vlc",             "Darwin": "open -a VLC",                   "Linux": "vlc"},
    "snipping tool": {"Windows": "snippingtool",          "Darwin": "open -a Screenshot",            "Linux": "gnome-screenshot"},
}


def open_application(app_name: str) -> str:
    key = app_name.lower().strip()
    entry = _APP_MAP.get(key)
    if not entry:
        return f"Sorry, I don't know how to open '{app_name}'."
    cmd = entry.get(SYSTEM)
    if not cmd:
        return f"Opening '{app_name}' is not supported on {SYSTEM}."
    try:
        if SYSTEM == "Windows":
            os.system(cmd)
        else:
            subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return f"Opening {app_name.title()}."
    except Exception as exc:
        return f"Couldn't open {app_name}: {exc}"


# ─────────────────────────────────────────────────────────────────────────────
# Websites
# ─────────────────────────────────────────────────────────────────────────────

_WEBSITE_MAP = {
    "youtube":      "https://www.youtube.com",
    "google":       "https://www.google.com",
    "github":       "https://github.com",
    "stackoverflow":"https://stackoverflow.com",
    "gmail":        "https://mail.google.com",
    "whatsapp":     "https://web.whatsapp.com",
    "linkedin":     "https://www.linkedin.com",
    "twitter":      "https://www.twitter.com",
    "instagram":    "https://www.instagram.com",
    "facebook":     "https://www.facebook.com",
    "reddit":       "https://www.reddit.com",
    "netflix":      "https://www.netflix.com",
    "amazon":       "https://www.amazon.com",
    "flipkart":     "https://www.flipkart.com",
    "wikipedia":    "https://www.wikipedia.org",
    "maps":         "https://maps.google.com",
    "translate":    "https://translate.google.com",
    "chatgpt":      "https://chat.openai.com",
}


def open_website(url: str, name: str = None) -> str:
    label = name or url
    try:
        webbrowser.open(url)
        return f"Opening {label} in your browser."
    except Exception as exc:
        return f"Couldn't open {label}: {exc}"


def open_named_website(site_name: str) -> str:
    key = site_name.lower().strip()
    url = _WEBSITE_MAP.get(key)
    if url:
        webbrowser.open(url)
        return f"Opening {site_name.title()} in your browser."
    # Fallback: try as a .com domain
    url = f"https://www.{key}.com"
    webbrowser.open(url)
    return f"Trying to open {site_name} in your browser."


# ─────────────────────────────────────────────────────────────────────────────
# Search helpers  (specific & smart)
# ─────────────────────────────────────────────────────────────────────────────

def search_google(query: str) -> str:
    """Generic Google search."""
    url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
    webbrowser.open(url)
    return f"Searching Google for '{query}'."


def google_meaning(word: str) -> str:
    """Search the meaning/definition of a word on Google."""
    url = f"https://www.google.com/search?q=meaning+of+{urllib.parse.quote_plus(word)}"
    webbrowser.open(url)
    return f"Looking up the meaning of '{word}' on Google."


def google_news(topic: str = "") -> str:
    """Open Google News, optionally filtered by topic."""
    if topic:
        url = f"https://news.google.com/search?q={urllib.parse.quote_plus(topic)}"
        webbrowser.open(url)
        return f"Opening Google News for '{topic}'."
    webbrowser.open("https://news.google.com")
    return "Opening Google News."


def google_images(query: str) -> str:
    url = f"https://www.google.com/images?q={urllib.parse.quote_plus(query)}"
    webbrowser.open(url)
    return f"Searching Google Images for '{query}'."


def google_maps(location: str) -> str:
    url = f"https://www.google.com/maps/search/{urllib.parse.quote_plus(location)}"
    webbrowser.open(url)
    return f"Opening Google Maps for '{location}'."


def google_translate(text: str, to_lang: str = "en") -> str:
    url = f"https://translate.google.com/?sl=auto&tl={to_lang}&text={urllib.parse.quote_plus(text)}&op=translate"
    webbrowser.open(url)
    return f"Translating '{text}' on Google Translate."


def search_youtube(query: str) -> str:
    """Generic YouTube search."""
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}"
    webbrowser.open(url)
    return f"Searching YouTube for '{query}'."


def play_youtube(song_or_query: str) -> str:
    """Play/search a specific song or video on YouTube."""
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(song_or_query)}"
    webbrowser.open(url)
    return f"Playing '{song_or_query}' on YouTube."


def search_wikipedia(query: str) -> str:
    url = f"https://en.wikipedia.org/wiki/Special:Search?search={urllib.parse.quote_plus(query)}"
    webbrowser.open(url)
    return f"Searching Wikipedia for '{query}'."


def weather_search(city: str) -> str:
    url = f"https://www.google.com/search?q=weather+in+{urllib.parse.quote_plus(city)}"
    webbrowser.open(url)
    return f"Checking weather for '{city}'."


def calculate(expression: str) -> str:
    url = f"https://www.google.com/search?q={urllib.parse.quote_plus(expression)}"
    webbrowser.open(url)
    return f"Calculating '{expression}' on Google."


# ─────────────────────────────────────────────────────────────────────────────
# System information
# ─────────────────────────────────────────────────────────────────────────────

def get_system_info() -> str:
    import psutil
    cpu   = psutil.cpu_percent(interval=1)
    mem   = psutil.virtual_memory()
    disk  = psutil.disk_usage("/")
    return (
        f"System: {platform.system()} {platform.release()}\n"
        f"Processor: {platform.processor() or 'Unknown'}\n"
        f"CPU Usage: {cpu}%\n"
        f"RAM: {mem.used / 1e9:.1f} GB used of {mem.total / 1e9:.1f} GB ({mem.percent}%)\n"
        f"Disk: {disk.used / 1e9:.1f} GB used of {disk.total / 1e9:.1f} GB ({disk.percent}%)"
    )
