"""
Nutrition Label Generator - Demo Launcher

Double-click this to start the application.
Browser will open automatically.
Close this window to quit.
"""

import webbrowser
import sys
import os
import threading
import time


def open_browser():
    """Open browser after server starts."""
    time.sleep(2)  # Wait for server to start
    webbrowser.open("http://127.0.0.1:8000")


def main():
    print("=" * 50)
    print("  Nutrition Label Generator")
    print("=" * 50)
    print()
    print("Starting server...")
    print("Browser will open automatically in a moment.")
    print()
    print("To quit: Close this window or press Ctrl+C")
    print()

    # Determine paths for PyInstaller vs development
    if getattr(sys, 'frozen', False):
        # Running as compiled executable (PyInstaller)
        base_dir = sys._MEIPASS
        backend_path = os.path.join(base_dir, 'backend')
        # Also look for .env in the directory containing the exe
        exe_dir = os.path.dirname(sys.executable)
        env_file = os.path.join(exe_dir, '.env')
        if os.path.exists(env_file):
            os.environ.setdefault('ENV_FILE', env_file)
    else:
        # Running as script (development)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        backend_path = os.path.join(base_dir, 'backend')
        env_file = os.path.join(base_dir, '.env')
        if os.path.exists(env_file):
            os.environ.setdefault('ENV_FILE', env_file)

    # Add backend to Python path
    sys.path.insert(0, backend_path)

    # Change to backend directory so relative paths work
    os.chdir(backend_path)

    # Open browser in background thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Import and run uvicorn
    try:
        import uvicorn
        uvicorn.run(
            "main:app",
            host="127.0.0.1",
            port=8000,
            log_level="warning",
            access_log=False
        )
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"\nError: {e}")
        print("\nPress Enter to close...")
        input()


if __name__ == "__main__":
    main()
