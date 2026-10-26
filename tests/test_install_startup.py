import os
import sys

import pytest

import install_startup


@pytest.mark.skipif(not hasattr(os, "getuid"), reason="Autostart .desktop entries are a Linux/GNOME feature")
def test_autostart_exec_quotes_paths_with_spaces(tmp_path, monkeypatch):
    root = tmp_path / "Pawsible project"
    root.mkdir()
    destination = tmp_path / "autostart" / "jamun.desktop"
    executable = tmp_path / "Python environment" / "bin" / "python"
    monkeypatch.setattr(install_startup, "ROOT", root)
    monkeypatch.setattr(install_startup, "DESTINATION", destination)
    monkeypatch.setattr(install_startup, "LEGACY_DESTINATION", destination.with_name("pengu.desktop"))
    monkeypatch.setattr(install_startup.sys, "executable", str(executable))
    monkeypatch.setattr(sys, "argv", ["install_startup.py", "install"])

    install_startup.main()

    assert f'Exec="{executable}" "{root / "main.py"}" --command hide\n' in destination.read_text()
    assert "Name=Pawsible\n" in destination.read_text()


@pytest.mark.skipif(os.name != "nt", reason="Registry autostart is Windows only")
def test_windows_autostart_round_trips(tmp_path, monkeypatch):
    import winreg

    root = tmp_path / "Pawsible project"
    root.mkdir()
    executable = tmp_path / "Python env" / "python.exe"
    key_path = r"Software\Pawsible\test_autostart"
    monkeypatch.setattr(install_startup, "ROOT", root)
    monkeypatch.setattr(install_startup, "RUN_KEY", key_path)
    monkeypatch.setattr(install_startup.sys, "executable", str(executable))

    try:
        monkeypatch.setattr(sys, "argv", ["install_startup.py", "install"])
        install_startup.main()
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            value, _ = winreg.QueryValueEx(key, install_startup.APP_NAME)
        assert value == f'"{executable}" "{root / "main.py"}" --command hide'

        monkeypatch.setattr(sys, "argv", ["install_startup.py", "remove"])
        install_startup.main()
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            with pytest.raises(FileNotFoundError):
                winreg.QueryValueEx(key, install_startup.APP_NAME)
    finally:
        for path in (key_path, r"Software\Pawsible"):
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, path)
            except OSError:
                pass
