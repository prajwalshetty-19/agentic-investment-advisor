"""Streamlit Frontend Application Launcher."""

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    app_path = Path(__file__).resolve().parent / "frontend" / "app.py"
    print(f"Launching Streamlit Frontend: {app_path}")
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)])
