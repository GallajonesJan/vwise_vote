import os
import sys
import subprocess
import socket
import time

# =========================
# CONFIGURATION
# =========================

REQUIRED_PACKAGES = {
    "flask": "flask",
    "mysql-connector-python": "mysql.connector",
    "flask-cors": "flask_cors",
}

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "vwise_vote",
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_FILE = os.path.join(BASE_DIR, "app.py")
FRONTEND_COMPONENTS = os.path.abspath(
    os.path.join(BASE_DIR, "..", "frontend", "components")
)
ASSETS_SVG = os.path.abspath(
    os.path.join(BASE_DIR, "..", "frontend", "assets", "svg")
)

FLASK_PORT = 5000


# =========================
# UTILITIES
# =========================

def print_header(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def run_command(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


# =========================
# CHECKS
# =========================

def ensure_packages():
    print_header("Checking Python Packages")
    missing = []

    for pip_name, import_name in REQUIRED_PACKAGES.items():
        try:
            __import__(import_name)
            print(f"✔ {pip_name}")
        except ImportError:
            print(f"✖ {pip_name} (missing)")
            missing.append(pip_name)

    if not missing:
        return True

    resp = input("\nInstall missing packages now? [Y/n]: ").strip().lower()
    if resp not in ("", "y", "yes"):
        return False

    for pkg in missing:
        print(f"Installing {pkg}...")
        result = run_command([sys.executable, "-m", "pip", "install", pkg])
        if result.returncode != 0:
            print(result.stderr.decode())
            return False

    print("✔ Packages installed successfully.")
    return True


def check_mysql_connection():
    print_header("Checking MySQL Connection")
    try:
        import mysql.connector

        conn = mysql.connector.connect(
            connection_timeout=5,
            **DB_CONFIG
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()  # IMPORTANT
        cursor.close()
        conn.close()

        print("✔ MySQL connection successful.")
        return True

    except mysql.connector.Error as e:
        print("✖ MySQL error:", e)
        return False

    except Exception as e:
        print("✖ Unexpected DB error:", e)
        return False


def check_paths():
    print_header("Checking Required Files & Folders")
    ok = True

    def check(path, kind="file"):
        nonlocal ok
        exists = os.path.isfile(path) if kind == "file" else os.path.isdir(path)
        print(("✔" if exists else "✖"), path)
        if not exists:
            ok = False

    check(APP_FILE, "file")
    check(FRONTEND_COMPONENTS, "dir")
    check(ASSETS_SVG, "dir")

    return ok


def check_port_free(port):
    print_header(f"Checking Port {port}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            print(f"✔ Port {port} is free.")
            return True
        except OSError:
            print(f"✖ Port {port} is already in use.")
            return False


# =========================
# APP RUNNER
# =========================

def run_app():
    print_header("Starting Flask App")
    print("Using Python:", sys.executable)

    process = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=BASE_DIR,
        env=os.environ.copy(),
    )

    try:
        while True:
            time.sleep(0.5)
            if process.poll() is not None:
                print("App exited with code", process.returncode)
                break
    except KeyboardInterrupt:
        print("\nStopping app...")
        process.terminate()


# =========================
# MAIN
# =========================

def main():
    no_run = "--no-run" in sys.argv

    print_header("Environment Check")
    print("Python executable:", sys.executable)
    print("Python version:", sys.version.split()[0])

    if not ensure_packages():
        return

    paths_ok = check_paths()
    db_ok = check_mysql_connection()
    port_ok = check_port_free(FLASK_PORT)

    print_header("Summary")
    print("Files & folders OK :", paths_ok)
    print("Database OK        :", db_ok)
    print("Port free          :", port_ok)

    if not (paths_ok and db_ok):
        print("\nFix the above issues before running the app.")
        return

    if no_run:
        print("Checks passed. Exiting (--no-run).")
        return

    if not port_ok:
        resp = input("Port in use. Start anyway? [y/N]: ").strip().lower()
        if resp not in ("y", "yes"):
            return

    run_app()


if __name__ == "__main__":
    main()
