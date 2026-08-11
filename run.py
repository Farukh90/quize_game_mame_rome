import sys
from pathlib import Path
from streamlit.web import cli as stcli


BASE_DIR = Path(__file__).resolve().parent
APP_FILE = BASE_DIR / "app.py"


if __name__ == "__main__":
    sys.argv = [
        "streamlit",
        "run",
        str(APP_FILE),
        "--server.address=0.0.0.0",
        "--server.port=8588",
        "--server.headless=true",
    ]

    sys.exit(stcli.main())