import os

START_SEQUENCE = "\033[91m"
END_SEQUENCE = "\033[0m"


def log(text):
    if os.getenv("DEBUG", "false").lower() in ("true", "1", "yes"):
        print(f"  🔧 {START_SEQUENCE}{text}{END_SEQUENCE}")
