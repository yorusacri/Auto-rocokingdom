from datetime import datetime


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")
