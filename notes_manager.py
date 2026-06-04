"""
Module 5: Notes Manager
Saves notes to a plain-text file and reads them back.
"""

import os
import datetime
import logging

logger = logging.getLogger(__name__)

NOTES_FILE = os.path.join(os.path.dirname(__file__), "notes.txt")


def create_note(content: str) -> str:
    """Append a timestamped note to the notes file."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"[{timestamp}] {content}\n"
    try:
        with open(NOTES_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
        return f"Note saved: '{content}'"
    except OSError as exc:
        logger.error("Could not write note: %s", exc)
        return f"Failed to save note: {exc}"


def read_notes() -> str:
    """Return all saved notes as a single string."""
    if not os.path.exists(NOTES_FILE):
        return "No notes found. Start by creating one!"
    try:
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
        return content if content else "Your notes file is empty."
    except OSError as exc:
        logger.error("Could not read notes: %s", exc)
        return f"Failed to read notes: {exc}"


def clear_notes() -> str:
    """Delete all saved notes."""
    try:
        if os.path.exists(NOTES_FILE):
            os.remove(NOTES_FILE)
        return "All notes cleared."
    except OSError as exc:
        return f"Failed to clear notes: {exc}"
