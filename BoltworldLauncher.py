"""
╔══════════════════════════════════════════════════════════════╗
║           BOLTWORLD ORDER AUTOMATION LAUNCHER                ║
║           ZED Management Systems — zed149.com                ║
╚══════════════════════════════════════════════════════════════╝

Double-click this file in the morning to start the system.
It will:
  1. Check internet connection and dependencies
  2. Run the order check immediately
  3. Re-run automatically every 15 minutes until you close it

"""

import subprocess
import sys
import os
import time
import socket
from datetime import datetime

# ── Config ─────────────────────────────────────────────────────────────────
INTERVAL_MINUTES = 15

# When frozen as .exe, files sit next to the executable
# When running as .py, files sit next to this script
if getattr(sys, 'frozen', False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Colours for terminal output ────────────────────────────────────────────
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    CYAN   = "\033[96m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    DIM    = "\033[2m"
    WHITE  = "\033[97m"


def banner():
    os.system('cls')
    print(f"{C.CYAN}{C.BOLD}")
    print("  ╔══════════════════════════════════════════════════════════╗")
    print("  ║         BOLTWORLD ORDER AUTOMATION SYSTEM                ║")
    print("  ║         Powered by ZED Management Systems                ║")
    print("  ╚══════════════════════════════════════════════════════════╝")
    print(f"{C.RESET}")


def log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    colours = {
        "INFO":  C.WHITE,
        "OK":    C.GREEN,
        "WARN":  C.YELLOW,
        "ERROR": C.RED,
        "STEP":  C.CYAN,
        "DIM":   C.DIM,
    }
    col = colours.get(level, C.WHITE)
    prefix = {
        "INFO":  "  ●",
        "OK":    "  ✓",
        "WARN":  "  ⚠",
        "ERROR": "  ✗",
        "STEP":  "\n  ──",
        "DIM":   "   ",
    }.get(level, "  ●")
    print(f"{C.DIM}[{ts}]{C.RESET} {col}{prefix} {msg}{C.RESET}")


def divider():
    print(f"  {C.DIM}{'─' * 58}{C.RESET}")


# ── Step 1: Check internet ─────────────────────────────────────────────────
def check_internet():
    log("Checking internet connection...", "STEP")
    for attempt in range(1, 4):
        try:
            socket.setdefaulttimeout(5)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('8.8.8.8', 53))
            sock.close()
            log("Internet connected", "OK")
            return True
        except OSError:
            log(f"Attempt {attempt}/3 failed...", "WARN")
            time.sleep(2)

    log("No internet connection. Please check your network.", "ERROR")
    return False


# ── Step 2: Check Python dependencies ─────────────────────────────────────
def check_dependencies():
    log("Checking dependencies...", "STEP")

    required = [
        ("requests",      "requests"),
        ("reportlab",     "reportlab"),
        ("win32api",      "pywin32"),
        ("pypdf",         "pypdf"),
        ("dotenv",        "python-dotenv"),
    ]

    missing = []
    for module, package in required:
        try:
            __import__(module)
            log(f"{package}", "OK")
        except ImportError:
            log(f"{package} — not installed", "WARN")
            missing.append(package)

    if missing:
        log(f"Installing {len(missing)} missing package(s)...", "INFO")
        for package in missing:
            log(f"pip install {package}", "DIM")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package, "-q"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                log(f"{package} installed", "OK")
            else:
                log(f"Failed to install {package}: {result.stderr.strip()}", "ERROR")
                return False

    return True


# ── Step 3: Check .env file ───────────────────────────────────────────────
def check_files():
    log("Checking .env file...", "STEP")
    env_path = os.path.join(SCRIPT_DIR, ".env")
    if os.path.exists(env_path):
        log(".env", "OK")
        return True
    log(".env — NOT FOUND", "ERROR")
    log("Please place the .env file in the same folder as this exe.", "WARN")
    return False


# ── Step 4: Run the main script ────────────────────────────────────────────
def run_order_script(run_number):
    divider()
    log(f"RUN #{run_number} — {datetime.now().strftime('%A %d %b %Y, %I:%M:%S %p')}", "STEP")
    divider()

    try:
        from check_orders import CheckOrders
        CheckOrders.check_new_orders()
        log("Run completed successfully", "OK")
        return True

    except Exception as e:
        log(f"Run failed: {e}", "ERROR")
        return False


# ── Countdown timer shown between runs ────────────────────────────────────
def countdown(minutes):
    next_run_time = datetime.now().replace(second=0, microsecond=0)
    next_run_time = next_run_time.replace(
        minute=(next_run_time.minute + minutes) % 60,
        hour=next_run_time.hour + (next_run_time.minute + minutes) // 60,
    )

    print()
    log(f"Next run at {next_run_time.strftime('%I:%M %p')}", "INFO")
    log("Press Ctrl+C to stop the automation.", "DIM")
    print()

    total_seconds = minutes * 60
    for remaining in range(total_seconds, 0, -1):
        mins = remaining // 60
        secs = remaining % 60
        print(
            f"\r  {C.DIM}Next run in: {C.RESET}"
            f"{C.CYAN}{C.BOLD}{mins:02d}:{secs:02d}{C.RESET}   ",
            end='', flush=True
        )
        time.sleep(1)

    print(f"\r  {C.GREEN}Starting next run...{' ' * 20}{C.RESET}")


# ── Main ───────────────────────────────────────────────────────────────────
def main():
    banner()

    log("BOLTWORLD ORDER AUTOMATION", "STEP")
    log(f"Interval : every {INTERVAL_MINUTES} minutes", "DIM")
    divider()

    if not check_internet():
        input("\n  Press Enter to exit...")
        sys.exit(1)

    if not check_dependencies():
        input("\n  Press Enter to exit...")
        sys.exit(1)

    if not check_files():
        input("\n  Press Enter to exit...")
        sys.exit(1)

    run_number = 1
    print()
    log("All checks passed. Automation started.", "OK")
    log("Keep this window open while the warehouse is running.", "WARN")

    while True:
        try:
            run_order_script(run_number)
            run_number += 1
            countdown(INTERVAL_MINUTES)

        except KeyboardInterrupt:
            print()
            divider()
            log("Automation stopped by user.", "WARN")
            log(f"Total runs completed: {run_number - 1}", "INFO")
            divider()
            input("\n  Press Enter to close...")
            sys.exit(0)

        except Exception as e:
            log(f"Unexpected error: {e}", "ERROR")
            log("Retrying in 2 minutes...", "WARN")
            try:
                countdown(2)
            except KeyboardInterrupt:
                sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n  FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        time.sleep(30)   # keeps window open 30 seconds so you can read it