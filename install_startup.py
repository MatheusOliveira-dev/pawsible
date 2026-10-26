import argparse
import os
import sys
from pathlib import Path

if sys.platform == "win32":
    import winreg


ROOT = Path(__file__).resolve().parent
DESTINATION = Path.home() / ".config" / "autostart" / "jamun.desktop"
LEGACY_DESTINATION = DESTINATION.with_name("pengu.desktop")

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "Pawsible"


def desktop_exec_arg(value):
    # Desktop-entry Exec quoting has two escaping layers, unlike shell quoting.
    escaped = []
    for char in str(value):
        if char == "%":
            escaped.append("%%")
        elif char == "\\":
            escaped.append("\\" * 4)
        elif char in ('"', "`", "$"):
            escaped.append("\\" * 2 + char)
        else:
            escaped.append(char)
    return '"' + "".join(escaped) + '"'


def remove_legacy_entry():
    if LEGACY_DESTINATION.exists() and str(ROOT / "main.py") in LEGACY_DESTINATION.read_text():
        LEGACY_DESTINATION.unlink()
        print(f"Removed old startup entry {LEGACY_DESTINATION}")


def install_linux():
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    launch = f"{desktop_exec_arg(sys.executable)} {desktop_exec_arg(ROOT / 'main.py')} --command hide"
    DESTINATION.write_text(
        "[Desktop Entry]\nType=Application\nName=Pawsible\nComment=Desktop pet companion\n"
        f"Exec={launch}\n"
        "Terminal=false\nX-GNOME-Autostart-enabled=true\n"
    )
    print(f"Installed {DESTINATION}")
    remove_legacy_entry()


def remove_linux():
    if DESTINATION.exists():
        DESTINATION.unlink()
        print(f"Removed {DESTINATION}")
    remove_legacy_entry()


def windows_launch_command():
    launcher = Path(sys.executable)
    # pythonw runs without a console window, which is what you want on login.
    windowless = launcher.with_name("pythonw.exe")
    if windowless.exists():
        launcher = windowless
    return f'"{launcher}" "{ROOT / "main.py"}" --command hide'


def install_windows():
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, windows_launch_command())
    print(f"Installed startup entry {APP_NAME}")


def remove_windows():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, APP_NAME)
            print(f"Removed startup entry {APP_NAME}")
    except FileNotFoundError:
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["install", "remove"])
    args = parser.parse_args()
    if os.name == "nt":
        install_windows() if args.action == "install" else remove_windows()
    else:
        install_linux() if args.action == "install" else remove_linux()


if __name__ == "__main__":
    main()
