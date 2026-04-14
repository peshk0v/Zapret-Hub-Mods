from __future__ import annotations

import ctypes
import locale
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

from PySide6.QtCore import QSize, QThread, Qt, Signal
from PySide6.QtGui import QIcon, QMouseEvent, QShowEvent
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QProgressBar,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

if sys.platform.startswith("win"):
    import winreg


def _is_ru() -> bool:
    try:
        lang = (locale.getdefaultlocale()[0] or "").lower()  # type: ignore[call-arg]
    except Exception:
        lang = ""
    return lang.startswith("ru")


RU = _is_ru()
UNINSTALL_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\ZapretHub"


def tr(ru: str, en: str) -> str:
    return ru if RU else en


def resource_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parents[1]


def default_install_dir() -> Path:
    return Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Zapret Hub"


def detect_payload_name() -> str:
    machine = platform.machine().lower()
    if "arm" in machine or "aarch64" in machine:
        return "win_arm64.zip"
    return "win_x64.zip"


def is_admin() -> bool:
    if not sys.platform.startswith("win"):
        return True
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())  # type: ignore[attr-defined]
    except Exception:
        return False


def relaunch_as_admin() -> bool:
    if not sys.platform.startswith("win"):
        return True
    if not getattr(sys, "frozen", False):
        return True
    if is_admin():
        return True
    cmd = " ".join(f'"{arg}"' for arg in sys.argv[1:])
    result = ctypes.windll.shell32.ShellExecuteW(  # type: ignore[attr-defined]
        None, "runas", sys.executable, cmd, None, 1
    )
    return int(result) > 32


def set_windows_app_id() -> None:
    if not sys.platform.startswith("win"):
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("goshkow.ZapretHub.Installer")  # type: ignore[attr-defined]
    except Exception:
        return


def disable_native_window_rounding(hwnd: int) -> None:
    if not sys.platform.startswith("win"):
        return
    try:
        DWMWA_WINDOW_CORNER_PREFERENCE = 33
        DWMWCP_DONOTROUND = 1
        value = ctypes.c_int(DWMWCP_DONOTROUND)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(  # type: ignore[attr-defined]
            ctypes.c_void_p(hwnd),
            ctypes.c_uint(DWMWA_WINDOW_CORNER_PREFERENCE),
            ctypes.byref(value),
            ctypes.sizeof(value),
        )
    except Exception:
        return


def bring_widget_to_front(widget: QWidget) -> None:
    widget.raise_()
    widget.activateWindow()
    if not sys.platform.startswith("win"):
        return
    try:
        hwnd = int(widget.winId())
        SW_RESTORE = 9
        HWND_TOPMOST = -1
        HWND_NOTOPMOST = -2
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        SWP_SHOWWINDOW = 0x0040
        ctypes.windll.user32.ShowWindow(hwnd, SW_RESTORE)  # type: ignore[attr-defined]
        ctypes.windll.user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)  # type: ignore[attr-defined]
        ctypes.windll.user32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)  # type: ignore[attr-defined]
        ctypes.windll.user32.SetForegroundWindow(hwnd)  # type: ignore[attr-defined]
    except Exception:
        return


def _run_hidden(command: list[str]) -> None:
    startup = None
    flags = 0
    if sys.platform.startswith("win"):
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
    subprocess.run(command, check=False, capture_output=True, creationflags=flags, startupinfo=startup)


def _terminate_running_instances() -> None:
    if not sys.platform.startswith("win"):
        return
    for image_name in ("zapret_hub.exe", "TgWsProxy_windows.exe", "winws.exe"):
        _run_hidden(["taskkill", "/F", "/T", "/IM", image_name])
    time.sleep(0.35)


def _remove_shortcuts() -> None:
    shortcut_paths = [
        Path(os.environ.get("USERPROFILE", "")) / "Desktop" / "Zapret Hub.lnk",
        Path(os.environ.get("PUBLIC", r"C:\Users\Public")) / "Desktop" / "Zapret Hub.lnk",
        Path(os.environ.get("APPDATA", "")) / r"Microsoft\Windows\Start Menu\Programs\Zapret Hub.lnk",
        Path(os.environ.get("ProgramData", r"C:\ProgramData")) / r"Microsoft\Windows\Start Menu\Programs\Zapret Hub.lnk",
    ]
    for path in shortcut_paths:
        try:
            if path.exists():
                path.unlink()
        except Exception:
            continue


def _safe_remove_item(path: Path) -> None:
    for _ in range(4):
        try:
            if not path.exists():
                return
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=False)
            else:
                path.unlink()
            return
        except PermissionError:
            _terminate_running_instances()
            time.sleep(0.25)
        except Exception:
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
                return
            raise
    if path.exists():
        raise PermissionError(f"cannot replace: {path}")


def _write_uninstall_registry(install_dir: Path, uninstaller_exe: Path, app_exe: Path) -> None:
    if not sys.platform.startswith("win"):
        return
    uninstall_cmd = f'"{uninstaller_exe}" --uninstall --install-dir "{install_dir}"'
    values = {
        "DisplayName": "Zapret Hub",
        "DisplayVersion": "1.0.0",
        "Publisher": "goshkow",
        "InstallLocation": str(install_dir),
        "DisplayIcon": str(app_exe),
        "UninstallString": uninstall_cmd,
        "QuietUninstallString": f'{uninstall_cmd} --silent',
        "NoModify": 1,
        "NoRepair": 1,
    }
    for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            access = winreg.KEY_WRITE
            if root == winreg.HKEY_LOCAL_MACHINE:
                access |= winreg.KEY_WOW64_64KEY
            with winreg.CreateKeyEx(root, UNINSTALL_KEY, 0, access) as key:
                for name, value in values.items():
                    if isinstance(value, int):
                        winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, value)
                    else:
                        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
            return
        except Exception:
            continue


def _remove_uninstall_registry() -> None:
    if not sys.platform.startswith("win"):
        return
    for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            access = winreg.KEY_WRITE
            if root == winreg.HKEY_LOCAL_MACHINE:
                access |= winreg.KEY_WOW64_64KEY
            winreg.DeleteKeyEx(root, UNINSTALL_KEY, access=access, reserved=0)
        except Exception:
            continue


def _install_dir_from_registry() -> Path | None:
    if not sys.platform.startswith("win"):
        return None
    for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            access = winreg.KEY_READ
            if root == winreg.HKEY_LOCAL_MACHINE:
                access |= winreg.KEY_WOW64_64KEY
            with winreg.OpenKey(root, UNINSTALL_KEY, 0, access) as key:
                value, _ = winreg.QueryValueEx(key, "InstallLocation")
                path = Path(str(value))
                if path.exists():
                    return path
        except Exception:
            continue
    return None


def _launch_folder_removal(install_dir: Path) -> None:
    cmd = f'ping 127.0.0.1 -n 3 > nul & rmdir /s /q "{install_dir}"'
    startup = None
    flags = 0
    if sys.platform.startswith("win"):
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
    subprocess.Popen(["cmd", "/c", cmd], creationflags=flags, startupinfo=startup)


class InstallerDialog(QDialog):
    def __init__(self, title: str, text: str, with_yes_no: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._drag_pos = None
        self._result_yes = False
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setModal(True)
        self.setFixedSize(520, 230)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowIcon(QIcon(str(resource_root() / "ui_assets" / "icons" / "app.ico")))

        root = QWidget(self)
        root.setObjectName("DlgRoot")
        root.setGeometry(0, 0, 520, 230)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.title_bar = QFrame()
        self.title_bar.setObjectName("DlgTitle")
        self.title_bar.setFixedHeight(46)
        title_row = QHBoxLayout(self.title_bar)
        title_row.setContentsMargins(12, 8, 12, 8)
        title_row.setSpacing(8)
        icon = QLabel()
        icon.setPixmap(QIcon(str(resource_root() / "ui_assets" / "icons" / "app.png")).pixmap(18, 18))
        title_row.addWidget(icon)
        title_row.addWidget(QLabel(title))
        title_row.addStretch(1)
        close_btn = QToolButton()
        close_btn.setProperty("role", "close")
        close_btn.setIcon(QIcon(str(resource_root() / "ui_assets" / "icons" / "window_close_dark.svg")))
        close_btn.setIconSize(QSize(14, 14))
        close_btn.setFixedSize(26, 26)
        close_btn.clicked.connect(self.reject)
        title_row.addWidget(close_btn)
        layout.addWidget(self.title_bar)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(16, 16, 16, 16)
        body_layout.setSpacing(14)
        message = QLabel(text)
        message.setWordWrap(True)
        body_layout.addWidget(message, 1)

        row = QHBoxLayout()
        row.addStretch(1)
        if with_yes_no:
            no_btn = QPushButton(tr("Нет", "No"))
            no_btn.clicked.connect(self.reject)
            yes_btn = QPushButton(tr("Да", "Yes"))
            yes_btn.setObjectName("primary")
            yes_btn.clicked.connect(self._accept_yes)
            row.addWidget(no_btn)
            row.addWidget(yes_btn)
        else:
            ok_btn = QPushButton("OK")
            ok_btn.setObjectName("primary")
            ok_btn.clicked.connect(self.accept)
            row.addWidget(ok_btn)
        body_layout.addLayout(row)
        layout.addWidget(body, 1)

        self.setStyleSheet(
            """
            #DlgRoot { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #11182a, stop:0.72 #11182a, stop:1 #162344); color: #dbe5fb; border: 1px solid #2a3f61; border-radius: 12px; font-family: Segoe UI; font-size: 10pt; }
            #DlgTitle { background: transparent; border-bottom: 1px solid #243551; }
            QLabel { background: transparent; color: #dbe5fb; }
            QPushButton { background: #253b62; border: 1px solid #396197; border-radius: 12px; padding: 8px 14px; min-width: 88px; color: #dbe5fb; }
            QPushButton#primary { background: #5865f2; border: 1px solid #7481ff; color: #fff; font-weight: 700; }
            QToolButton { border: none; background: transparent; min-width: 26px; min-height: 26px; max-width: 26px; max-height: 26px; border-radius: 12px; padding: 0px; margin: 0px; }
            QToolButton[role="close"]:hover { background: rgba(170, 84, 97, 0.62); border-radius: 12px; }
            """
        )

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        disable_native_window_rounding(int(self.winId()))
        bring_widget_to_front(self)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() <= self.title_bar.height():
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def _accept_yes(self) -> None:
        self._result_yes = True
        self.accept()

    @property
    def result_yes(self) -> bool:
        return self._result_yes


class InstallerWorker(QThread):
    progress = Signal(int)
    done = Signal(bool, str)

    def __init__(self, target_dir: Path) -> None:
        super().__init__()
        self.target_dir = target_dir

    def run(self) -> None:
        try:
            root = resource_root()
            payload_zip = root / "installer_payload" / detect_payload_name()
            if not payload_zip.exists():
                raise FileNotFoundError(f"payload not found: {payload_zip}")

            self.progress.emit(8)
            _terminate_running_instances()
            self.target_dir.mkdir(parents=True, exist_ok=True)
            staging = Path(tempfile.mkdtemp(prefix="zapret_hub_install_"))
            self.progress.emit(18)

            with zipfile.ZipFile(payload_zip, "r") as archive:
                archive.extractall(staging)
            self.progress.emit(45)

            source_root = staging / "zapret_hub"
            if not source_root.exists():
                source_root = staging

            for item in list(self.target_dir.iterdir()) if self.target_dir.exists() else []:
                if item.name.lower() == "logs":
                    continue
                _safe_remove_item(item)

            self.progress.emit(70)
            for item in source_root.iterdir():
                dst = self.target_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, dst, dirs_exist_ok=True)
                else:
                    if dst.exists():
                        _safe_remove_item(dst)
                    shutil.copy2(item, dst)

            shutil.rmtree(staging, ignore_errors=True)
            self.progress.emit(100)
            self.done.emit(True, "")
        except Exception as error:
            self.done.emit(False, str(error))


class InstallerWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._drag_pos = None
        self.worker: InstallerWorker | None = None
        self.install_path = default_install_dir()
        self.setWindowTitle("Zapret Hub Installer")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(580, 380)
        self.setWindowIcon(QIcon(str(resource_root() / "ui_assets" / "icons" / "app.ico")))
        self._build_ui()
        self._load_existing_install()

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        shell = QVBoxLayout(root)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        self.title_bar = QFrame()
        self.title_bar.setObjectName("InstallerTitleBar")
        self.title_bar.setFixedHeight(46)
        title_row = QHBoxLayout(self.title_bar)
        title_row.setContentsMargins(12, 8, 12, 8)
        title_row.setSpacing(8)

        icon = QLabel()
        icon.setPixmap(QIcon(str(resource_root() / "ui_assets" / "icons" / "app.png")).pixmap(19, 19))
        title_row.addWidget(icon)
        title_row.addWidget(QLabel("Zapret Hub"))
        title_row.addStretch(1)
        close_btn = QToolButton()
        close_btn.setProperty("role", "close")
        close_btn.setIcon(QIcon(str(resource_root() / "ui_assets" / "icons" / "window_close_dark.svg")))
        close_btn.setIconSize(QSize(14, 14))
        close_btn.setFixedSize(26, 26)
        close_btn.clicked.connect(self.close)
        title_row.addWidget(close_btn)
        shell.addWidget(self.title_bar)

        self.stack = QStackedWidget()
        shell.addWidget(self.stack, 1)

        self.page_start = QWidget()
        start_layout = QVBoxLayout(self.page_start)
        start_layout.setContentsMargins(20, 20, 20, 20)
        start_layout.setSpacing(12)
        head = QLabel(tr("Добро пожаловать в установщик Zapret Hub", "Welcome to Zapret Hub Installer"))
        head.setObjectName("title")
        start_layout.addWidget(head)
        desc = QLabel(
            tr(
                "Приложение устанавливает Zapret Hub и автоматически выбирает подходящую версию под вашу систему.",
                "This installer deploys Zapret Hub and automatically picks the proper build for your system.",
            )
        )
        desc.setWordWrap(True)
        start_layout.addWidget(desc)
        path_row = QHBoxLayout()
        self.path_edit = QLineEdit(str(self.install_path))
        browse_btn = QPushButton(tr("Обзор", "Browse"))
        browse_btn.clicked.connect(self._choose_dir)
        path_row.addWidget(self.path_edit, 1)
        path_row.addWidget(browse_btn)
        start_layout.addLayout(path_row)
        start_layout.addStretch(1)
        install_btn = QPushButton(tr("Установить", "Install"))
        install_btn.setObjectName("primary")
        install_btn.setMinimumHeight(42)
        install_btn.clicked.connect(self._start_install)
        start_layout.addWidget(install_btn)
        self.stack.addWidget(self.page_start)

        self.page_progress = QWidget()
        progress_layout = QVBoxLayout(self.page_progress)
        progress_layout.setContentsMargins(20, 20, 20, 20)
        progress_layout.setSpacing(12)
        progress_layout.addWidget(QLabel(tr("Установка...", "Installing...")))
        progress_layout.addStretch(1)
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setFixedHeight(24)
        progress_layout.addWidget(self.bar)
        progress_layout.addStretch(1)
        self.stack.addWidget(self.page_progress)

        self.page_done = QWidget()
        done_layout = QVBoxLayout(self.page_done)
        done_layout.setContentsMargins(20, 20, 20, 20)
        done_layout.setSpacing(12)
        done_layout.addWidget(QLabel(tr("Установка завершена", "Installation complete")))
        self.desktop_cb = QCheckBox(tr("Создать ярлык на рабочем столе", "Create desktop shortcut"))
        self.startmenu_cb = QCheckBox(tr("Создать ярлык в меню Пуск", "Create Start Menu shortcut"))
        self.desktop_cb.setChecked(True)
        self.startmenu_cb.setChecked(True)
        done_layout.addWidget(self.desktop_cb)
        done_layout.addWidget(self.startmenu_cb)
        done_layout.addStretch(1)
        finish_btn = QPushButton(tr("Готово", "Finish"))
        finish_btn.setObjectName("primary")
        finish_btn.setMinimumHeight(42)
        finish_btn.clicked.connect(self._finish)
        done_layout.addWidget(finish_btn)
        self.stack.addWidget(self.page_done)

        check_icon = str((resource_root() / "ui_assets" / "icons" / "check.svg").resolve()).replace("\\", "/")
        self.setStyleSheet(
            f"""
            QMainWindow {{ background: transparent; }}
            QWidget#Root {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #11182a, stop:0.7 #11182a, stop:1 #162344); color: #dbe5fb; font-family: Segoe UI; font-size: 10pt; border: 1px solid #2a3f61; border-radius: 12px; }}
            #InstallerTitleBar {{ background: transparent; border-bottom: 1px solid #243551; }}
            QLabel#title {{ font-size: 18pt; font-weight: 800; color: #ffffff; }}
            QLabel {{ background: transparent; }}
            QLineEdit {{ background: #15213a; border: 1px solid #304a73; border-radius: 10px; padding: 9px; font-size: 11pt; }}
            QPushButton {{ background: #253b62; border: 1px solid #396197; border-radius: 12px; padding: 10px 14px; font-size: 11pt; color: #dbe5fb; }}
            QPushButton#primary {{ background: #5865f2; border: 1px solid #7481ff; color: #fff; font-weight: 800; }}
            QToolButton {{ border: none; background: transparent; min-width: 26px; min-height: 26px; max-width: 26px; max-height: 26px; border-radius: 12px; padding: 0px; margin: 0px; }}
            QToolButton[role="close"]:hover {{ background: rgba(170, 84, 97, 0.62); border-radius: 12px; }}
            QProgressBar {{ background: #15213a; border: 1px solid #304a73; border-radius: 10px; text-align: center; }}
            QProgressBar::chunk {{ background: #5865f2; border-radius: 9px; }}
            QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 5px; border: 1px solid #4f6a98; background: transparent; }}
            QCheckBox::indicator:checked {{ background: #5865f2; border: 1px solid #7a86ff; image: url("{check_icon}"); }}
            """
        )

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        disable_native_window_rounding(int(self.winId()))
        bring_widget_to_front(self)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() <= self.title_bar.height():
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def _load_existing_install(self) -> None:
        existing = _install_dir_from_registry()
        if existing:
            self.path_edit.setText(str(existing))

    def _choose_dir(self) -> None:
        picked = QFileDialog.getExistingDirectory(self, tr("Выбор папки", "Choose install directory"), self.path_edit.text())
        if picked:
            self.path_edit.setText(picked)

    def _start_install(self) -> None:
        self.install_path = Path(self.path_edit.text().strip() or str(default_install_dir()))
        self.stack.setCurrentWidget(self.page_progress)
        self.worker = InstallerWorker(self.install_path)
        self.worker.progress.connect(self.bar.setValue)
        self.worker.done.connect(self._on_done)
        self.worker.start()

    def _on_done(self, ok: bool, error: str) -> None:
        if not ok:
            InstallerDialog("Error", error, parent=self).exec()
            self.stack.setCurrentWidget(self.page_start)
            return
        self._register_uninstaller()
        self.stack.setCurrentWidget(self.page_done)

    def _register_uninstaller(self) -> None:
        app_exe = self.install_path / "zapret_hub.exe"
        uninstaller_exe = self.install_path / "uninstall_zaprethub.exe"
        try:
            current_installer = Path(sys.executable).resolve()
            if current_installer.exists() and current_installer.suffix.lower() == ".exe":
                shutil.copy2(current_installer, uninstaller_exe)
            _write_uninstall_registry(self.install_path, uninstaller_exe, app_exe)
        except Exception:
            pass

    def _create_shortcut(self, target: Path, name: str, desktop: bool) -> None:
        if desktop:
            base = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
        else:
            base = Path(os.environ.get("APPDATA", "")) / r"Microsoft\Windows\Start Menu\Programs"
        base.mkdir(parents=True, exist_ok=True)
        lnk_path = base / f"{name}.lnk"
        ps = (
            "$WScriptShell = New-Object -ComObject WScript.Shell; "
            f"$Shortcut = $WScriptShell.CreateShortcut('{str(lnk_path)}'); "
            f"$Shortcut.TargetPath = '{str(target)}'; "
            f"$Shortcut.WorkingDirectory = '{str(target.parent)}'; "
            f"$Shortcut.IconLocation = '{str(target)},0'; "
            "$Shortcut.Save();"
        )
        startup = None
        flags = 0
        if sys.platform.startswith("win"):
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            startup = subprocess.STARTUPINFO()
            startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startup.wShowWindow = 0
        subprocess.run(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
            capture_output=True,
            check=False,
            creationflags=flags,
            startupinfo=startup,
        )

    def _finish(self) -> None:
        exe = self.install_path / "zapret_hub.exe"
        if self.desktop_cb.isChecked():
            self._create_shortcut(exe, "Zapret Hub", desktop=True)
        if self.startmenu_cb.isChecked():
            self._create_shortcut(exe, "Zapret Hub", desktop=False)
        if exe.exists():
            try:
                os.startfile(str(exe))  # type: ignore[attr-defined]
            except Exception:
                pass
        self.close()


def main() -> int:
    if not relaunch_as_admin():
        return 1
    if not is_admin():
        return 0

    set_windows_app_id()
    if "--uninstall" in sys.argv:
        app = QApplication(sys.argv)
        app.setWindowIcon(QIcon(str(resource_root() / "ui_assets" / "icons" / "app.ico")))
        install_arg = ""
        if "--install-dir" in sys.argv:
            try:
                install_arg = sys.argv[sys.argv.index("--install-dir") + 1]
            except Exception:
                install_arg = ""
        install_dir = Path(install_arg) if install_arg else (_install_dir_from_registry() or default_install_dir())
        silent = "--silent" in sys.argv
        if not silent:
            confirm = InstallerDialog(
                tr("Удаление Zapret Hub", "Remove Zapret Hub"),
                tr(
                    "Удалить Zapret Hub и все данные внутри папки установки?\n\nВнешние папки и сторонние файлы не будут затронуты.",
                    "Remove Zapret Hub and all data inside the install folder?\n\nExternal folders and third-party files will not be touched.",
                ),
                with_yes_no=True,
            )
            confirm.exec()
            if not confirm.result_yes:
                return 0
        _terminate_running_instances()
        _remove_shortcuts()
        _remove_uninstall_registry()
        if install_dir.exists():
            _launch_folder_removal(install_dir)
        if not silent:
            InstallerDialog(
                tr("Удаление запущено", "Uninstall started"),
                tr("Приложение будет удалено через несколько секунд.", "The app will be removed in a few seconds."),
            ).exec()
        return 0

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(resource_root() / "ui_assets" / "icons" / "app.ico")))
    window = InstallerWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
