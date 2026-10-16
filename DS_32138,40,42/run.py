"""
Hospital Emergency Management System Runner
Launches the Flask web server on http://127.0.0.1:5055
"""

import sys
import os

# Ensure UTF-8 stdout encoding on Windows
if sys.platform.startswith('win'):
    try:
        stdout = sys.stdout
        if hasattr(stdout, 'reconfigure'):
            getattr(stdout, 'reconfigure')(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5055))
    print("=" * 65)
    print("[+] AuraCare Hospital Emergency Management System")
    print("=" * 65)
    print(f"Server starting on http://127.0.0.1:{port}")
    print("Open this URL in your web browser to interact with the system.")
    print("=" * 65)
    app.run(host="127.0.0.1", port=port, debug=False)
