"""
main.py — Command-line entry point for the Mini Voice Assistant.

Usage:
    python main.py           # interactive CLI mode
    streamlit run gui.py     # full GUI mode (recommended)
"""

from speech_engine import SpeechEngine, TTSEngine
from command_processor import CommandProcessor
import sys


def run_cli():
    print("=" * 55)
    print("       Mini Voice Assistant  —  CLI Mode")
    print("  Say a command, or type it and press Enter.")
    print("  Type 'exit' to quit.")
    print("=" * 55)

    tts = TTSEngine(rate=175)
    engine = SpeechEngine(tts=tts)
    processor = CommandProcessor()

    tts.speak("Mini Voice Assistant ready.")

    while True:
        print("\nOptions: [1] Listen  [2] Type command  [3] Exit")
        choice = input("Choice: ").strip()

        if choice == "1":
            print("Listening… (speak now)")
            text = engine.listen_once(timeout=8)
            if not text:
                print("Nothing heard.")
                continue
            if text.startswith("__"):
                print(f"Error: {text}")
                continue
            print(f"You said: {text}")
        elif choice == "2":
            text = input("Type command: ").strip().lower()
        elif choice == "3" or choice.lower() in ("exit", "quit"):
            tts.speak("Goodbye!")
            sys.exit(0)
        else:
            continue

        response = processor.process(text)
        if response == "__EXIT__":
            tts.speak("Goodbye!")
            print("Exiting.")
            break

        print(f"\nAssistant: {response}\n")
        tts.speak(response)


if __name__ == "__main__":
    run_cli()
