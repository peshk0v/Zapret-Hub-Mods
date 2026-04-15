from __future__ import annotations

import ctypes
import sys
import threading
import webbrowser
from dataclasses import dataclass
from pathlib import Path

from zapret_hub import __version__
from PySide6.QtCore import QCoreApplication, QEvent, QObject, QPoint, QRect, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QCloseEvent, QIcon, QMouseEvent, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QMainWindow,
    QMenu,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
    QScrollArea,
    QStackedWidget,
    QSystemTrayIcon,
    QTextEdit,
    QInputDialog,
    QProgressBar,
    QToolButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from zapret_hub.bootstrap import ApplicationContext
from zapret_hub.ui.theme import build_stylesheet


@dataclass(slots=True)
class NavItem:
    key: str
    icon_file: str
    tooltip: str


@dataclass(slots=True)
class StatusBadge:
    key: str
    icon_file: str
    title: str
    title_label: QLabel
    icon_label: QLabel
    value_label: QLabel


class _UiSignals(QObject):
    toggle_done = Signal()
    component_action_done = Signal(str)
    general_test_progress = Signal(int, int, str)
    general_test_done = Signal(object)
    update_check_done = Signal(object, bool)
    update_prepare_done = Signal(object)


class SidebarPanel(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._border_color = QColor("#24304a")
        self._cut_size = 18

    def set_theme(self, theme: str) -> None:
        self._border_color = QColor("#d2ddeb" if theme == "light" else "#24304a")
        self.update()

    def paintEvent(self, event: QEvent) -> None:
        super().paintEvent(event)


def _disable_native_window_rounding(widget: QWidget) -> None:
    if not sys.platform.startswith("win"):
        return
    try:
        hwnd = int(widget.winId())
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


def _bring_widget_to_front(widget: QWidget) -> None:
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


class AppDialog(QDialog):
    def __init__(self, parent: QWidget, context: ApplicationContext, title: str) -> None:
        super().__init__(parent)
        self.context = context
        self._drag_pos: QPoint | None = None
        self.setObjectName("AppDialogWindow")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlag(Qt.WindowType.Dialog, True)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setWindowFlag(Qt.WindowType.NoDropShadowWindowHint, True)
        self.setModal(True)
        self.setWindowTitle(title)
        self.setMinimumWidth(420)

        shell = QVBoxLayout(self)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        root = QFrame()
        root.setObjectName("DialogRoot")
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        title_bar = QFrame()
        title_bar.setObjectName("DialogTitleBar")
        title_bar.setFixedHeight(42)
        title_row = QHBoxLayout(title_bar)
        title_row.setContentsMargins(10, 8, 10, 8)
        title_row.setSpacing(8)

        title_label = QLabel(title)
        title_label.setProperty("class", "title")
        title_row.addWidget(title_label)
        title_row.addStretch(1)

        close_btn = QToolButton()
        close_btn.setProperty("class", "window")
        close_btn.setProperty("role", "close")
        suffix = "dark" if context.settings.get().theme == "dark" else "light"
        close_btn.setIcon(QIcon(str(context.paths.ui_assets_dir / "icons" / f"window_close_{suffix}.svg")))
        close_btn.setIconSize(QSize(14, 14))
        close_btn.clicked.connect(self.reject)
        title_row.addWidget(close_btn)

        root_layout.addWidget(title_bar)
        self.body = QWidget()
        self.body.setObjectName("DialogBody")
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(14, 12, 14, 12)
        self.body_layout.setSpacing(10)
        root_layout.addWidget(self.body)
        shell.addWidget(root)
        _disable_native_window_rounding(self)

    def prepare_and_center(self) -> None:
        self.adjustSize()
        if self.parentWidget() is not None:
            parent_rect = self.parentWidget().frameGeometry()
            target = parent_rect.center() - self.rect().center()
            self.move(target)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() <= 42:
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

    def showEvent(self, event: QEvent) -> None:
        _disable_native_window_rounding(self)
        super().showEvent(event)
        QTimer.singleShot(0, lambda: _bring_widget_to_front(self))


class SettingsDialog(AppDialog):
    def __init__(self, parent: QWidget, context: ApplicationContext) -> None:
        self.context = context
        super().__init__(parent, context, self._t("Настройки", "Settings"))
        self.setMinimumWidth(430)
        layout = self.body_layout

        form = QFormLayout()
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        self.language_combo = QComboBox()
        self.language_combo.addItems(["ru", "en"])
        self.tg_host_input = QLineEdit()
        self.tg_port_input = QLineEdit()
        self.tg_secret_input = QLineEdit()
        self.ipset_mode_combo = QComboBox()
        self.ipset_mode_combo.addItem("loaded", "loaded")
        self.ipset_mode_combo.addItem("none", "none")
        self.ipset_mode_combo.addItem("any", "any")
        self.game_mode_combo = QComboBox()
        self.game_mode_combo.addItem(self._t("выключен", "disabled"), "disabled")
        self.game_mode_combo.addItem(self._t("tcp + udp", "tcp + udp"), "all")
        self.game_mode_combo.addItem(self._t("только tcp", "tcp only"), "tcp")
        self.game_mode_combo.addItem(self._t("только udp", "udp only"), "udp")
        self.autostart_checkbox = QCheckBox(self._t("Запускать вместе с Windows", "Run with Windows"))
        self.tray_checkbox = QCheckBox(self._t("Стартовать в трее", "Start in tray"))
        self.auto_components_checkbox = QCheckBox(self._t("Автозапуск компонентов", "Auto-run components"))
        form.addRow(self._t("Тема", "Theme"), self.theme_combo)
        form.addRow(self._t("Язык", "Language"), self.language_combo)
        form.addRow(self._t("Хост TG proxy", "TG proxy host"), self.tg_host_input)
        form.addRow(self._t("Порт TG proxy", "TG proxy port"), self.tg_port_input)
        form.addRow(self._t("Секрет TG proxy", "TG proxy secret"), self.tg_secret_input)
        form.addRow("IPSet mode", self.ipset_mode_combo)
        form.addRow(self._t("Gaming mode", "Gaming mode"), self.game_mode_combo)
        form.addRow("", self.autostart_checkbox)
        form.addRow("", self.tray_checkbox)
        form.addRow("", self.auto_components_checkbox)
        layout.addLayout(form)

        credits = QLabel(
            self._t(
                "Credits: original zapret bundle and tg-ws-proxy by Flowseal.\n"
                "Original zapret ecosystem by bol-van.\n"
                f"This app is a separate management UI.\nVersion: {__version__}",
                "Credits: original zapret bundle and tg-ws-proxy by Flowseal.\n"
                "Original zapret ecosystem by bol-van.\n"
                f"This app is a separate management UI.\nVersion: {__version__}",
            )
        )
        credits.setProperty("class", "muted")
        layout.addWidget(credits)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel_btn = QPushButton(self._t("Отмена", "Cancel"))
        save_btn = QPushButton(self._t("Сохранить", "Save"))
        save_btn.setProperty("class", "primary")
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self.accept)
        buttons.addWidget(cancel_btn)
        buttons.addWidget(save_btn)
        layout.addLayout(buttons)
        self._load()

    def _t(self, ru: str, en: str) -> str:
        return ru if self.context.settings.get().language == "ru" else en

    def _load(self) -> None:
        settings = self.context.settings.get()
        self.theme_combo.setCurrentText(settings.theme)
        self.language_combo.setCurrentText(settings.language)
        self.tg_host_input.setText(settings.tg_proxy_host)
        self.tg_port_input.setText(str(settings.tg_proxy_port))
        self.tg_secret_input.setText(settings.tg_proxy_secret)
        ipset_idx = self.ipset_mode_combo.findData(settings.zapret_ipset_mode)
        self.ipset_mode_combo.setCurrentIndex(ipset_idx if ipset_idx >= 0 else 0)
        game_idx = self.game_mode_combo.findData(settings.zapret_game_filter_mode)
        self.game_mode_combo.setCurrentIndex(game_idx if game_idx >= 0 else 0)
        self.autostart_checkbox.setChecked(self.context.autostart.is_enabled() or settings.autostart_windows)
        self.tray_checkbox.setChecked(settings.start_in_tray)
        self.auto_components_checkbox.setChecked(settings.auto_run_components)

    def payload(self) -> dict[str, object]:
        try:
            tg_port = int(self.tg_port_input.text().strip() or "1443")
        except ValueError:
            tg_port = 1443
        return {
            "theme": self.theme_combo.currentText(),
            "active_profile_id": self.context.settings.get().active_profile_id,
            "language": self.language_combo.currentText(),
            "mods_index_url": self.context.settings.get().mods_index_url,
            "tg_proxy_host": self.tg_host_input.text().strip() or "127.0.0.1",
            "tg_proxy_port": tg_port,
            "tg_proxy_secret": self.tg_secret_input.text().strip(),
            "zapret_ipset_mode": self.ipset_mode_combo.currentData() or "loaded",
            "zapret_game_filter_mode": self.game_mode_combo.currentData() or "disabled",
            "autostart_windows": self.autostart_checkbox.isChecked(),
            "start_in_tray": self.tray_checkbox.isChecked(),
            "auto_run_components": self.auto_components_checkbox.isChecked(),
        }


class MainWindow(QMainWindow):
    def __init__(self, context: ApplicationContext, launch_hidden: bool = False) -> None:
        super().__init__()
        self.context = context
        self._launch_hidden = launch_hidden
        self._skip_next_show_focus = launch_hidden
        self._drag_pos: QPoint | None = None
        self._tray_notifications_shown = False
        self._force_exit = False
        self._shutdown_started = False
        self._nav_buttons: list[QToolButton] = []
        self._status_badges: dict[str, StatusBadge] = {}
        self._min_btn: QToolButton | None = None
        self._close_btn: QToolButton | None = None
        self._toggle_in_progress = False
        self._loading_frame = 0
        self._loading_timer = QTimer(self)
        self._loading_timer.setInterval(220)
        self._loading_timer.timeout.connect(self._advance_loading_caption)
        self._component_loading_timer = QTimer(self)
        self._component_loading_timer.setInterval(200)
        self._component_loading_timer.timeout.connect(self._advance_component_loading)
        self._ui_signals = _UiSignals()
        self._ui_signals.toggle_done.connect(self._on_master_toggle_finished)
        self._ui_signals.component_action_done.connect(self._on_component_action_done)
        self._ui_signals.general_test_progress.connect(self._on_general_test_progress)
        self._ui_signals.general_test_done.connect(self._on_general_test_done)
        self._ui_signals.update_check_done.connect(self._on_update_check_done)
        self._ui_signals.update_prepare_done.connect(self._on_update_prepare_done)
        self._updating_general_combo = False
        self._pending_info_message: tuple[str, str] | None = None
        self._components_cards_root: QWidget | None = None
        self._components_cards_layout: QHBoxLayout | None = None
        self._component_loading_buttons: dict[str, QPushButton] = {}
        self._component_loading_base_text: dict[str, str] = {}
        self._component_loading_frame = 0
        self._general_loading_combo: QComboBox | None = None
        self._general_loading_label: QLabel | None = None
        self._general_test_dialog: AppDialog | None = None
        self._general_test_status_label: QLabel | None = None
        self._general_test_progress_bar: QProgressBar | None = None
        self._general_test_running = False
        self._general_test_cancelled = False
        self._general_test_show_results = True
        self._loading_action = "connect"
        self._tools_btn: QToolButton | None = None
        self._settings_btn: QToolButton | None = None
        self._dashboard_title_label: QLabel | None = None
        self._components_title_label: QLabel | None = None
        self._mods_title_label: QLabel | None = None
        self._mods_subtitle_label: QLabel | None = None
        self._mods_add_btn: QPushButton | None = None
        self._files_title_label: QLabel | None = None
        self._editor_title_label: QLabel | None = None
        self._logs_title_label: QLabel | None = None
        self._logs_refresh_btn: QPushButton | None = None
        self._tray_show_action: QAction | None = None
        self._tray_quit_action: QAction | None = None
        self._update_check_in_progress = False
        self._update_prepare_dialog: AppDialog | None = None
        self._last_prompted_update_version = ""

        self._icons_dir = self.context.paths.ui_assets_dir / "icons"
        self._nav_items = [
            NavItem("home", "home.svg", self._t("Главная", "Dashboard")),
            NavItem("components", "components.svg", self._t("Компоненты", "Components")),
            NavItem("mods", "mods.svg", self._t("Модификации", "Mods")),
            NavItem("files", "files.svg", self._t("Файлы", "Files")),
            NavItem("logs", "logs.svg", self._t("Логи", "Logs")),
        ]

        self.resize(860, 520)
        self.setMinimumSize(820, 480)
        self.setMaximumSize(980, 680)
        self.setWindowTitle("Zapret Hub")
        self.setWindowIcon(self._icon("app.ico"))
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)
        self._build_ui()
        self._setup_tray()
        self._apply_theme()
        self.refresh_all()
        if not self._launch_hidden:
            QTimer.singleShot(800, self._maybe_run_first_general_autotest)
            QTimer.singleShot(1400, self._check_updates_on_start)
            QTimer.singleShot(0, lambda: _bring_widget_to_front(self))

    def _t(self, ru: str, en: str) -> str:
        return ru if self.context.settings.get().language == "ru" else en

    def _icon(self, filename: str) -> QIcon:
        icon_path = self._icons_dir / filename
        return QIcon(str(icon_path))

    def showEvent(self, event: QEvent) -> None:
        super().showEvent(event)
        _disable_native_window_rounding(self)
        if self._skip_next_show_focus:
            self._skip_next_show_focus = False
            return
        QTimer.singleShot(0, lambda: _bring_widget_to_front(self))

    def _build_ui(self) -> None:
        shell = QWidget()
        shell.setObjectName("WindowShell")
        root = QVBoxLayout(shell)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(0)

        frame = QFrame()
        frame.setObjectName("RootFrame")
        root_frame = QVBoxLayout(frame)
        root_frame.setContentsMargins(0, 0, 0, 0)
        root_frame.setSpacing(0)

        title_bar = self._build_title_bar()
        root_frame.addWidget(title_bar)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        root_frame.addLayout(body)

        body.addWidget(self._build_sidebar())
        body.addWidget(self._build_content(), 1)

        root.addWidget(frame)
        self.setCentralWidget(shell)

    def _build_title_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("TitleBar")
        bar.setFixedHeight(52)
        row = QHBoxLayout(bar)
        row.setContentsMargins(12, 9, 12, 9)
        row.setSpacing(8)

        icon = QLabel()
        icon.setPixmap(self._icon("app.png").pixmap(20, 20))
        row.addWidget(icon)

        title = QLabel("Zapret Hub")
        title.setProperty("class", "title")
        row.addWidget(title)

        author = QLabel("by goshkow")
        author.setProperty("class", "muted")
        row.addWidget(author)
        row.addStretch(1)

        tools_btn = QToolButton()
        tools_btn.setProperty("class", "action")
        tools_btn.setIcon(self._icon("tool.svg"))
        tools_btn.setIconSize(QSize(16, 16))
        tools_btn.setToolTip(self._t("Инструменты", "Tools"))
        tools_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        tools_btn.setMenu(self._build_tools_menu())
        self._attach_button_animations(tools_btn)
        self._tools_btn = tools_btn
        row.addWidget(tools_btn)

        settings_btn = QToolButton()
        settings_btn.setProperty("class", "action")
        settings_btn.setIcon(self._icon("settings.svg"))
        settings_btn.setIconSize(QSize(16, 16))
        settings_btn.setToolTip(self._t("Настройки", "Settings"))
        settings_btn.clicked.connect(self._open_settings_dialog)
        self._attach_button_animations(settings_btn)
        self._settings_btn = settings_btn
        row.addWidget(settings_btn)

        min_btn = self._window_btn("", "min")
        self._min_btn = min_btn
        min_btn.setIconSize(QSize(15, 15))
        min_btn.clicked.connect(self._minimize_window_native)
        self._attach_button_animations(min_btn)
        close_btn = self._window_btn("", "close")
        self._close_btn = close_btn
        close_btn.setIconSize(QSize(15, 15))
        close_btn.clicked.connect(self.close)
        self._attach_button_animations(close_btn)
        row.addWidget(min_btn)
        row.addWidget(close_btn)
        return bar

    def _window_btn(self, text: str, role: str) -> QToolButton:
        btn = QToolButton()
        btn.setText(text)
        btn.setProperty("class", "window")
        btn.setProperty("role", role)
        return btn

    def _build_tools_menu(self) -> QMenu:
        menu = QMenu(self)
        run_tests = QAction(self._t("Проверить конфигурации", "Run general tests"), self)
        run_tests.triggered.connect(self._run_general_tests_popup)
        menu.addAction(run_tests)

        run_diag = QAction(self._t("Запустить диагностику", "Run diagnostics"), self)
        run_diag.triggered.connect(self._run_diagnostics_popup)
        menu.addAction(run_diag)

        check_updates = QAction(self._t("Проверить обновления", "Check updates"), self)
        check_updates.triggered.connect(self._check_updates_popup)
        menu.addAction(check_updates)

        rebuild = QAction(self._t("Пересобрать merged", "Rebuild merged"), self)
        rebuild.triggered.connect(self._rebuild_runtime)
        menu.addAction(rebuild)

        refresh = QAction(self._t("Обновить всё", "Refresh all"), self)
        refresh.triggered.connect(self.refresh_all)
        menu.addAction(refresh)
        return menu

    def _build_sidebar(self) -> QWidget:
        side = SidebarPanel()
        side.setObjectName("Sidebar")
        side.setFixedWidth(72)
        col = QVBoxLayout(side)
        col.setContentsMargins(12, 12, 12, 12)
        col.setSpacing(10)

        for idx, item in enumerate(self._nav_items):
            btn = QToolButton()
            btn.setProperty("class", "nav")
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setIcon(self._icon(item.icon_file))
            btn.setIconSize(QSize(20, 20))
            btn.setToolTip(item.tooltip)
            btn.clicked.connect(lambda _=False, index=idx: self._switch_page(index))
            self._attach_button_animations(btn)
            self._nav_buttons.append(btn)
            col.addWidget(btn)

        col.addStretch(1)
        if self._nav_buttons:
            self._nav_buttons[0].setChecked(True)
        return side

    def _build_content(self) -> QWidget:
        pane = QFrame()
        pane.setObjectName("Content")
        layout = QVBoxLayout(pane)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        body = QFrame()
        body.setObjectName("ContentSurface")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(12, 12, 12, 12)
        body_layout.setSpacing(8)

        self.pages = QStackedWidget()
        self.pages.addWidget(self._build_dashboard_page())
        self.pages.addWidget(self._build_components_page())
        self.pages.addWidget(self._build_mods_page())
        self.pages.addWidget(self._build_files_page())
        self.pages.addWidget(self._build_logs_page())
        body_layout.addWidget(self.pages)
        layout.addWidget(body, 1)
        return pane

    def _card(self) -> tuple[QFrame, QVBoxLayout]:
        card = QFrame()
        card.setProperty("class", "card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 6, 14, 14)
        layout.setSpacing(10)
        return card, layout

    def _build_dashboard_page(self) -> QWidget:
        page = QWidget()
        page.setProperty("class", "pageRoot")
        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)

        top, top_layout = self._card()
        top_layout.setContentsMargins(14, 14, 14, 14)
        title = QLabel(self._t("Быстрое управление", "Quick control"))
        title.setObjectName("DashboardTitle")
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        title.setContentsMargins(0, 0, 0, 0)
        title.setMaximumHeight(22)
        self._dashboard_title_label = title
        top_layout.addWidget(title)

        # настройка general перенесена в компоненты
        general_label = QLabel(self._t("Конфигурация", "General"))
        self.general_combo = QComboBox()
        self.general_combo.currentIndexChanged.connect(self._on_general_selected)
        self.general_combo.hide()

        self.power_button = QToolButton()
        self.power_button.setProperty("class", "power")
        self.power_button.setIcon(self._icon("power.svg"))
        self.power_button.setIconSize(QSize(42, 42))
        self.power_button.clicked.connect(self._toggle_master_runtime)
        self._attach_button_animations(self.power_button)

        self.power_caption = QLabel("OFF")
        self.power_caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.power_caption.setProperty("class", "title")
        power_block = QWidget()
        power_block.setObjectName("DashboardPowerBlock")
        power_block_layout = QVBoxLayout(power_block)
        power_block_layout.setContentsMargins(0, 0, 0, 0)
        power_block_layout.setSpacing(8)
        power_block_layout.addWidget(self.power_button, 0, Qt.AlignmentFlag.AlignHCenter)
        power_block_layout.addWidget(self.power_caption, 0, Qt.AlignmentFlag.AlignHCenter)

        top_layout.addStretch(1)
        top_layout.addWidget(power_block, 0, Qt.AlignmentFlag.AlignHCenter)
        top_layout.addStretch(1)

        badges_row = QHBoxLayout()
        badges_row.setSpacing(10)
        for key, icon_name, title_text in [
            ("app", "status_ok.svg", self._t("Приложение", "App")),
            ("zapret", "status_warn.svg", "Zapret"),
            ("tg", "status_warn.svg", "TG Proxy"),
            ("mods", "status_mod.svg", "Mods"),
            ("theme", "status_theme.svg", self._t("Тема", "Theme")),
        ]:
            badge = self._build_status_badge(key, icon_name, title_text)
            badges_row.addWidget(badge)
        badges_row.setStretch(0, 1)
        badges_row.setStretch(1, 1)
        badges_row.setStretch(2, 1)
        badges_row.setStretch(3, 1)
        badges_row.setStretch(4, 1)
        top_layout.addLayout(badges_row)
        root.addWidget(top)

        return page

    def _build_status_badge(self, key: str, icon_name: str, title: str) -> QWidget:
        card, layout = self._card()
        card.setMinimumHeight(96)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        head = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(self._icon(icon_name).pixmap(18, 18))
        text_label = QLabel(title)
        text_label.setProperty("class", "muted")
        head.addWidget(icon_label)
        head.addWidget(text_label)
        head.addStretch(1)
        layout.addLayout(head)

        value = QLabel("...")
        value.setProperty("class", "title")
        value.setWordWrap(False)
        layout.addWidget(value)
        self._status_badges[key] = StatusBadge(key, icon_name, title, text_label, icon_label, value)
        return card

    def _build_components_page(self) -> QWidget:
        page = QWidget()
        page.setProperty("class", "pageRoot")
        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)
        label = QLabel(self._t("Компоненты", "Components"))
        label.setProperty("class", "title")
        self._components_title_label = label
        root.addWidget(label)

        self.components_list = QListWidget()
        self.components_list.setObjectName("ComponentList")
        self.components_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.components_list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.components_list.setSpacing(8)
        self.components_list.hide()
        root.addWidget(self.components_list)
        self._components_cards_root = QWidget()
        self._components_cards_root.setProperty("class", "pageCanvas")
        self._components_cards_layout = QHBoxLayout(self._components_cards_root)
        self._components_cards_layout.setContentsMargins(0, 0, 0, 0)
        self._components_cards_layout.setSpacing(12)
        root.addWidget(self._components_cards_root, 1)
        return page

    def _build_mods_page(self) -> QWidget:
        page = QWidget()
        page.setProperty("class", "pageRoot")
        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        hero, hero_layout = self._card()
        hero.setProperty("class", "modHero")

        hero_top = QHBoxLayout()
        hero_top.setContentsMargins(0, 0, 0, 0)
        hero_top.setSpacing(10)

        title_wrap = QVBoxLayout()
        title_wrap.setContentsMargins(0, 0, 0, 0)
        title_wrap.setSpacing(4)
        label = QLabel(self._t("Модификации", "Mods"))
        label.setProperty("class", "title")
        self._mods_title_label = label
        subtitle = QLabel(
            self._t(
                "Здесь можно аккуратно подключать свои сборки, не ломая базовую конфигурацию.",
                "This is where you can attach your own packs without touching the base configuration.",
            )
        )
        subtitle.setProperty("class", "muted")
        subtitle.setWordWrap(True)
        self._mods_subtitle_label = subtitle
        title_wrap.addWidget(label)
        title_wrap.addWidget(subtitle)
        hero_top.addLayout(title_wrap, 1)

        import_btn = QPushButton(self._t("Добавить", "Add"))
        import_btn.setProperty("class", "primary")
        import_btn.setIcon(self._icon("plus.svg"))
        import_btn.setIconSize(QSize(14, 14))
        import_btn.setMinimumHeight(38)
        import_btn.clicked.connect(self._import_mod_any)
        self._attach_button_animations(import_btn)
        self._mods_add_btn = import_btn
        hero_top.addWidget(import_btn)
        hero_layout.addLayout(hero_top)

        summary_row = QHBoxLayout()
        summary_row.setContentsMargins(0, 0, 0, 0)
        summary_row.setSpacing(10)

        self.mods_summary_chip = QLabel()
        self.mods_summary_chip.setObjectName("ModsSummaryChip")
        self.mods_summary_chip.setProperty("class", "modMeta")
        summary_row.addWidget(self.mods_summary_chip)

        self.mods_enabled_chip = QLabel()
        self.mods_enabled_chip.setObjectName("ModsEnabledChip")
        self.mods_enabled_chip.setProperty("class", "modMeta")
        summary_row.addWidget(self.mods_enabled_chip)

        self.mods_import_hint = QLabel(
            self._t(
                "Можно добавить папку, ZIP, отдельные файлы или целый GitHub-репозиторий. Приложение само заберет только совместимые файлы.",
                "You can add a folder, ZIP, selected files, or a full GitHub repository. The app will keep only compatible files.",
            )
        )
        self.mods_import_hint.setProperty("class", "modHint")
        self.mods_import_hint.setWordWrap(True)
        summary_row.addWidget(self.mods_import_hint, 1)
        hero_layout.addLayout(summary_row)
        root.addWidget(hero)

        self.mods_scroll = QScrollArea()
        self.mods_scroll.setObjectName("ModsScroll")
        self.mods_scroll.setWidgetResizable(True)
        self.mods_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.mods_canvas = QWidget()
        self.mods_canvas.setObjectName("ModsCanvas")
        self.mods_canvas.setProperty("class", "pageCanvas")
        self.mods_cards_layout = QVBoxLayout(self.mods_canvas)
        self.mods_cards_layout.setContentsMargins(0, 0, 0, 0)
        self.mods_cards_layout.setSpacing(12)
        self.mods_scroll.setWidget(self.mods_canvas)
        root.addWidget(self.mods_scroll, 1)
        return page

    def _build_files_page(self) -> QWidget:
        page = QWidget()
        page.setProperty("class", "pageRoot")
        root = QHBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        left, left_layout = self._card()
        left_title = QLabel(self._t("Файлы", "Files"))
        left_title.setProperty("class", "title")
        self._files_title_label = left_title
        left_layout.addWidget(left_title)
        self.files_list = QListWidget()
        self.files_list.setObjectName("FilesList")
        self.files_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.files_list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.files_list.setSpacing(8)
        self.files_list.currentItemChanged.connect(self._load_selected_file)
        left_layout.addWidget(self.files_list)
        root.addWidget(left, 1)

        right, right_layout = self._card()
        right_title = QLabel(self._t("Редактор", "Editor"))
        right_title.setProperty("class", "title")
        self._editor_title_label = right_title
        right_layout.addWidget(right_title)
        self.file_path_label = QLabel(self._t("Выберите файл", "Select a file"))
        self.file_path_label.setProperty("class", "muted")
        path_row = QHBoxLayout()
        path_row.addWidget(self.file_path_label, 1)
        self.rename_file_btn = QToolButton()
        self.rename_file_btn.setProperty("class", "action")
        self.rename_file_btn.setIcon(self._icon("edit.svg"))
        self.rename_file_btn.setToolTip(self._t("Переименовать выбранный файл", "Rename selected file"))
        self.rename_file_btn.clicked.connect(self._rename_current_file)
        self._attach_button_animations(self.rename_file_btn)
        path_row.addWidget(self.rename_file_btn)
        right_layout.addLayout(path_row)
        self.file_editor = QTextEdit()
        self.file_editor.setObjectName("FileEditor")
        right_layout.addWidget(self.file_editor, 1)
        save_btn = QPushButton(self._t("Сохранить файл", "Save file"))
        save_btn.clicked.connect(self._save_current_file)
        self._attach_button_animations(save_btn)
        right_layout.addWidget(save_btn)
        root.addWidget(right, 2)
        return page

    def _build_logs_page(self) -> QWidget:
        page = QWidget()
        page.setProperty("class", "pageRoot")
        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)
        top = QHBoxLayout()
        label = QLabel(self._t("Логи", "Logs"))
        label.setProperty("class", "title")
        self._logs_title_label = label
        top.addWidget(label)
        top.addStretch(1)
        refresh_btn = QPushButton(self._t("Обновить", "Refresh"))
        refresh_btn.clicked.connect(self.refresh_logs)
        self._attach_button_animations(refresh_btn)
        self._logs_refresh_btn = refresh_btn
        top.addWidget(refresh_btn)
        root.addLayout(top)
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        root.addWidget(self.logs_text)
        return page

    def _setup_tray(self) -> None:
        self.tray_icon = QSystemTrayIcon(self._icon("app.ico"), self)
        menu = QMenu(self)
        show_action = QAction(self._t("Открыть", "Open"), self)
        quit_action = QAction(self._t("Выход", "Exit"), self)
        show_action.triggered.connect(self._restore_from_tray)
        quit_action.triggered.connect(self._exit_application)
        self._tray_show_action = show_action
        self._tray_quit_action = quit_action
        menu.addAction(show_action)
        menu.addAction(quit_action)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.setToolTip("Zapret Hub")
        self.tray_icon.show()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() <= 48:
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

    def closeEvent(self, event: QCloseEvent) -> None:
        if not self._force_exit:
            if self._should_minimize_to_tray():
                event.ignore()
                self.hide()
                if not self._tray_notifications_shown:
                    self.tray_icon.showMessage("Zapret Hub", self._t("Приложение свернуто в трей.", "Minimized to tray."), QSystemTrayIcon.MessageIcon.Information, 2200)
                    self._tray_notifications_shown = True
                return
            self._force_exit = True
        self._shutdown_runtime()
        event.accept()
        app = QCoreApplication.instance()
        if app is not None:
            QTimer.singleShot(0, app.quit)
        super().closeEvent(event)

    def _restore_from_tray(self) -> None:
        self.refresh_all()
        self.showNormal()
        _bring_widget_to_front(self)

    def restore_from_external_launch(self) -> None:
        self._restore_from_tray()

    def _exit_application(self) -> None:
        self._force_exit = True
        self._shutdown_runtime()
        self.close()
        app = QCoreApplication.instance()
        if app is not None:
            QTimer.singleShot(0, app.quit)

    def _shutdown_runtime(self) -> None:
        if self._shutdown_started:
            return
        self._shutdown_started = True
        self._loading_timer.stop()
        self._component_loading_timer.stop()
        self._general_test_running = False
        try:
            self.context.processes.stop_all()
        except Exception:
            pass
        if hasattr(self, "tray_icon") and self.tray_icon is not None:
            try:
                self.tray_icon.hide()
                self.tray_icon.setContextMenu(None)
                self.tray_icon.deleteLater()
            except Exception:
                pass

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._restore_from_tray()

    def _should_minimize_to_tray(self) -> bool:
        # в трей уходим только когда реально есть активный runtime
        try:
            states = {state.component_id: state for state in self.context.processes.list_states()}
        except Exception:
            return False
        for component_id in ("zapret", "tg-ws-proxy"):
            state = states.get(component_id)
            if state and state.status == "running":
                return True
        return False

    def _attach_button_animations(self, widget: QWidget) -> None:
        # анимации кнопок временно выключены: на части систем резалась отрисовка текста
        return

    def _animate_button_opacity(self, widget: QWidget, target: float, duration: int) -> None:
        return

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        return super().eventFilter(watched, event)

    def _switch_page(self, index: int) -> None:
        for i, btn in enumerate(self._nav_buttons):
            btn.setChecked(i == index)
        if index != self.pages.currentIndex():
            self.pages.setCurrentIndex(index)


    def _open_settings_dialog(self) -> None:
        dialog = SettingsDialog(self, self.context)
        dialog.prepare_and_center()
        if dialog.exec():
            before = self.context.settings.get()
            tg_before = (before.tg_proxy_host, int(before.tg_proxy_port), before.tg_proxy_secret)
            zapret_before = (before.zapret_ipset_mode, before.zapret_game_filter_mode, before.selected_zapret_general)
            payload = dialog.payload()
            self.context.settings.update(**payload)
            self.context.autostart.set_enabled(bool(payload["autostart_windows"]))
            tg_after = (str(payload["tg_proxy_host"]), int(payload["tg_proxy_port"]), str(payload["tg_proxy_secret"]))
            zapret_after = (
                str(payload.get("zapret_ipset_mode", "loaded")),
                str(payload.get("zapret_game_filter_mode", "disabled")),
                self.context.settings.get().selected_zapret_general,
            )
            if tg_before != tg_after:
                states = {s.component_id: s for s in self.context.processes.list_states()}
                tg_running = states.get("tg-ws-proxy") and states["tg-ws-proxy"].status == "running"
                if tg_running:
                    self.context.processes.stop_component("tg-ws-proxy")
                    self.context.processes.start_component("tg-ws-proxy")
            if zapret_before != zapret_after:
                states = {s.component_id: s for s in self.context.processes.list_states()}
                zapret_running = states.get("zapret") and states["zapret"].status == "running"
                if zapret_running:
                    self.context.processes.stop_component("zapret")
                    self.context.processes.start_component("zapret")
            self._apply_theme()
            self._retranslate_ui()
            self.refresh_all()

    def _apply_theme(self) -> None:
        theme = self.context.settings.get().theme
        chevron = str((self._icons_dir / "chevron_down.svg").resolve())
        check = str((self._icons_dir / "check.svg").resolve())
        self.setStyleSheet(build_stylesheet(theme, chevron_icon=chevron, check_icon=check))
        if hasattr(self, "power_button") and self.power_button is not None:
            power_icon = "power_dark.svg" if theme == "dark" else "power_light.svg"
            self.power_button.setIcon(self._icon(power_icon))
        sidebar = self.findChild(SidebarPanel, "Sidebar")
        if sidebar is not None:
            sidebar.set_theme(theme)
        self._apply_titlebar_icons(theme)

    def _apply_titlebar_icons(self, theme: str) -> None:
        if self._min_btn is None or self._close_btn is None:
            return
        suffix = "dark" if theme == "dark" else "light"
        self._min_btn.setIcon(self._icon(f"window_min_{suffix}.svg"))
        self._close_btn.setIcon(self._icon(f"window_close_{suffix}.svg"))

    def _retranslate_ui(self) -> None:
        nav_tooltips = [
            self._t("Главная", "Dashboard"),
            self._t("Компоненты", "Components"),
            self._t("Модификации", "Mods"),
            self._t("Файлы", "Files"),
            self._t("Логи", "Logs"),
        ]
        for index, btn in enumerate(self._nav_buttons):
            if index < len(nav_tooltips):
                btn.setToolTip(nav_tooltips[index])

        if self._tools_btn is not None:
            self._tools_btn.setToolTip(self._t("Инструменты", "Tools"))
            self._tools_btn.setMenu(self._build_tools_menu())
        if self._settings_btn is not None:
            self._settings_btn.setToolTip(self._t("Настройки", "Settings"))

        if self._dashboard_title_label is not None:
            self._dashboard_title_label.setText(self._t("Быстрое управление", "Quick control"))
        if self._components_title_label is not None:
            self._components_title_label.setText(self._t("Компоненты", "Components"))
        if self._mods_title_label is not None:
            self._mods_title_label.setText(self._t("Модификации", "Mods"))
        if self._mods_subtitle_label is not None:
            self._mods_subtitle_label.setText(
                self._t(
                    "Здесь можно аккуратно подключать свои сборки, не ломая базовую конфигурацию.",
                    "This is where you can attach your own packs without touching the base configuration.",
                )
            )
        if self._mods_add_btn is not None:
            self._mods_add_btn.setText(self._t("Добавить", "Add"))
        if hasattr(self, "mods_import_hint") and self.mods_import_hint is not None:
            self.mods_import_hint.setText(
                self._t(
                    "Можно добавить папку, ZIP, отдельные файлы или целый GitHub-репозиторий. Приложение само заберет только совместимые файлы.",
                    "You can add a folder, ZIP, selected files, or a full GitHub repository. The app will keep only compatible files.",
                )
            )
        if self._files_title_label is not None:
            self._files_title_label.setText(self._t("Файлы", "Files"))
        if self._editor_title_label is not None:
            self._editor_title_label.setText(self._t("Редактор", "Editor"))
        if self._logs_title_label is not None:
            self._logs_title_label.setText(self._t("Логи", "Logs"))
        if self._logs_refresh_btn is not None:
            self._logs_refresh_btn.setText(self._t("Обновить", "Refresh"))

        title_map = {
            "app": self._t("Приложение", "App"),
            "zapret": "Zapret",
            "tg": "TG Proxy",
            "mods": "Mods",
            "theme": self._t("Тема", "Theme"),
        }
        for key, title in title_map.items():
            badge = self._status_badges.get(key)
            if badge is None:
                continue
            badge.title = title
            badge.title_label.setText(title)

        if self._tray_show_action is not None:
            self._tray_show_action.setText(self._t("Открыть", "Open"))
        if self._tray_quit_action is not None:
            self._tray_quit_action.setText(self._t("Выход", "Exit"))

        if self.files_list.currentItem() is None:
            self.file_path_label.setText(self._t("Выберите файл", "Select a file"))

    def _format_general_option_label(self, option: dict[str, str]) -> str:
        bundle = (option.get("bundle") or "").strip()
        name = option.get("name", "").strip()
        if not bundle:
            return name
        return f"({bundle}) {name}"

    def _start_component_loading(self, component_id: str, button: QPushButton, base_text: str) -> None:
        self._component_loading_buttons[component_id] = button
        self._component_loading_base_text[component_id] = base_text
        button.setEnabled(False)
        self._component_loading_frame = 0
        if not self._component_loading_timer.isActive():
            self._component_loading_timer.start()
        self._advance_component_loading()

    def _stop_component_loading(self, component_id: str) -> None:
        button = self._component_loading_buttons.pop(component_id, None)
        base_text = self._component_loading_base_text.pop(component_id, None)
        if button is not None:
            try:
                button.setEnabled(True)
                if base_text is not None:
                    button.setText(base_text)
            except RuntimeError:
                pass
        if not self._component_loading_buttons and self._general_loading_label is None:
            self._component_loading_timer.stop()

    def _advance_component_loading(self) -> None:
        frames = [".", "..", "..."]
        frame = frames[self._component_loading_frame % len(frames)]
        self._component_loading_frame += 1
        for button in list(self._component_loading_buttons.values()):
            try:
                button.setText(frame)
            except RuntimeError:
                continue
        if self._general_loading_label is not None:
            try:
                self._general_loading_label.setText(f"{self._t('Применение', 'Applying')}{frame}")
            except RuntimeError:
                self._general_loading_label = None
        if not self._component_loading_buttons and self._general_loading_label is None:
            self._component_loading_timer.stop()

    def _minimize_window_native(self) -> None:
        self.showMinimized()

    def _selected_component_id(self) -> str | None:
        item = self.components_list.currentItem()
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def _selected_mod_id(self) -> str | None:
        if not hasattr(self, "mods_list"):
            return None
        item = self.mods_list.currentItem()
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def _selected_file_path(self) -> str | None:
        item = self.files_list.currentItem()
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def _toggle_master_runtime(self) -> None:
        if self._toggle_in_progress:
            return
        states = {s.component_id: s for s in self.context.processes.list_states()}
        active_ids = self._master_active_components()
        running_ids = {cid for cid in active_ids if states.get(cid) and states[cid].status == "running"}
        self._loading_action = "disconnect" if active_ids and running_ids == set(active_ids) else "connect"
        self._toggle_in_progress = True
        self.power_button.setEnabled(False)
        self._loading_frame = 0
        self._loading_timer.start()
        self._advance_loading_caption()
        thread = threading.Thread(target=self._toggle_master_runtime_worker, daemon=True)
        thread.start()

    def _toggle_master_runtime_worker(self) -> None:
        try:
            states = {s.component_id: s for s in self.context.processes.list_states()}
            active_ids = self._master_active_components()
            if not active_ids:
                return
            running_ids = {cid for cid in active_ids if states.get(cid) and states[cid].status == "running"}
            if running_ids == set(active_ids):
                for cid in active_ids:
                    self.context.processes.stop_component(cid)
            else:
                for cid in active_ids:
                    if cid not in running_ids:
                        self.context.processes.start_component(cid)
        finally:
            self._ui_signals.toggle_done.emit()

    def _on_master_toggle_finished(self) -> None:
        self._loading_timer.stop()
        self._toggle_in_progress = False
        self.power_button.setEnabled(True)
        self.refresh_all()
        if self._pending_info_message is not None:
            title, text = self._pending_info_message
            self._pending_info_message = None
            self._show_info(title, text)

    def _advance_loading_caption(self) -> None:
        if not self._toggle_in_progress:
            return
        base = self._t("Подключение", "Connecting") if self._loading_action == "connect" else self._t("Отключение", "Disconnecting")
        frames = [base, f"{base}.", f"{base}..", f"{base}..."]
        self.power_caption.setText(frames[self._loading_frame % len(frames)])
        self._loading_frame += 1

    def _start_selected_component(self) -> None:
        component_id = self._selected_component_id()
        if component_id:
            self.context.processes.start_component(component_id)
            self.refresh_all()

    def _stop_selected_component(self) -> None:
        component_id = self._selected_component_id()
        if component_id:
            self.context.processes.stop_component(component_id)
            self.refresh_all()

    def _toggle_selected_component_enabled(self) -> None:
        component_id = self._selected_component_id()
        if component_id:
            self.context.processes.toggle_component_enabled(component_id)
            self.refresh_all()

    def _toggle_selected_component_autostart(self) -> None:
        component_id = self._selected_component_id()
        if component_id:
            self.context.processes.toggle_component_autostart(component_id)
            self.refresh_all()

    def _toggle_component_card(self, component_id: str, button: QPushButton) -> None:
        if component_id in self._component_loading_buttons:
            return
        self._start_component_loading(component_id, button, button.text())
        thread = threading.Thread(target=self._toggle_component_card_worker, args=(component_id,), daemon=True)
        thread.start()

    def _toggle_component_card_worker(self, component_id: str) -> None:
        self.context.processes.toggle_component_enabled(component_id)
        self._ui_signals.component_action_done.emit(component_id)

    def _install_selected_mod(self) -> None:
        mod_id = self._selected_mod_id()
        if mod_id:
            self.context.mods.install(mod_id)
            self.refresh_all()

    def _toggle_selected_mod(self) -> None:
        mod_id = self._selected_mod_id()
        if not mod_id:
            return
        installed = {item.id: item for item in self.context.mods.list_installed()}
        if mod_id not in installed:
            self._show_info(self._t("Модификация", "Mod"), self._t("Сначала установите модификацию, затем включайте её.", "Install selected mod before enabling it."))
            return
        self.context.mods.set_enabled(mod_id, not installed[mod_id].enabled)
        self.refresh_all()

    def _remove_selected_mod(self) -> None:
        mod_id = self._selected_mod_id()
        if mod_id:
            self.context.mods.remove(mod_id)
            self.refresh_all()

    def _import_mod_any(self) -> None:
        chooser = AppDialog(self, self.context, self._t("Добавить модификацию", "Add modification"))
        chooser.setMinimumWidth(520)
        chooser_text = QLabel(
            self._t(
                "Выберите удобный источник. Хаб сам вытащит только совместимые general-файлы, списки и нужные runtime-файлы.",
                "Choose the source you want. The hub will keep only compatible general files, lists, and required runtime files.",
            )
        )
        chooser_text.setWordWrap(True)
        chooser_text.setProperty("class", "muted")
        chooser.body_layout.addWidget(chooser_text)

        buttons = QGridLayout()
        buttons.setHorizontalSpacing(10)
        buttons.setVerticalSpacing(10)
        folder_btn = QPushButton(self._t("Папка", "Folder"))
        folder_btn.setProperty("class", "primary")
        zip_btn = QPushButton(self._t("ZIP-архив", "ZIP archive"))
        zip_btn.setProperty("class", "primary")
        files_btn = QPushButton(self._t("Файл(ы)", "File(s)"))
        files_btn.setProperty("class", "primary")
        github_btn = QPushButton(self._t("GitHub", "GitHub"))
        github_btn.setProperty("class", "primary")
        cancel_btn = QPushButton(self._t("Отмена", "Cancel"))
        self._attach_button_animations(folder_btn)
        self._attach_button_animations(zip_btn)
        self._attach_button_animations(files_btn)
        self._attach_button_animations(github_btn)
        self._attach_button_animations(cancel_btn)
        buttons.addWidget(folder_btn, 0, 0)
        buttons.addWidget(zip_btn, 0, 1)
        buttons.addWidget(files_btn, 1, 0)
        buttons.addWidget(github_btn, 1, 1)
        buttons.addWidget(cancel_btn, 2, 0, 1, 2)
        chooser.body_layout.addLayout(buttons)

        selected_kind: dict[str, str] = {"kind": ""}
        folder_btn.clicked.connect(lambda: (selected_kind.__setitem__("kind", "folder"), chooser.accept()))
        zip_btn.clicked.connect(lambda: (selected_kind.__setitem__("kind", "zip"), chooser.accept()))
        files_btn.clicked.connect(lambda: (selected_kind.__setitem__("kind", "files"), chooser.accept()))
        github_btn.clicked.connect(lambda: (selected_kind.__setitem__("kind", "github"), chooser.accept()))
        cancel_btn.clicked.connect(chooser.reject)
        chooser.prepare_and_center()
        if chooser.exec() != QDialog.DialogCode.Accepted:
            return

        path = ""
        paths: list[str] = []
        if selected_kind["kind"] == "folder":
            path = QFileDialog.getExistingDirectory(self, self._t("Выберите папку модификации", "Select modification folder"))
            if path:
                paths = [path]
        elif selected_kind["kind"] == "zip":
            path, _ = QFileDialog.getOpenFileName(
                self,
                self._t("Выберите ZIP-архив модификации", "Select modification ZIP archive"),
                filter=self._t("ZIP-архив (*.zip)", "ZIP archive (*.zip)"),
            )
            if path:
                paths = [path]
        elif selected_kind["kind"] == "files":
            paths, _ = QFileDialog.getOpenFileNames(
                self,
                self._t("Выберите файлы модификации", "Select modification files"),
                filter=self._t(
                    "Совместимые файлы (*.bat *.cmd *.txt *.json *.yaml *.yml *.zip);;Все файлы (*.*)",
                    "Compatible files (*.bat *.cmd *.txt *.json *.yaml *.yml *.zip);;All files (*.*)",
                ),
            )
        elif selected_kind["kind"] == "github":
            repo_url = self._ask_text_value(
                self._t("GitHub-модификация", "GitHub modification"),
                self._t("Вставьте ссылку на GitHub-репозиторий.", "Paste a GitHub repository link."),
                self._t("Например: https://github.com/user/repo", "Example: https://github.com/user/repo"),
            )
            if not repo_url:
                return
            try:
                self.context.mods.import_from_github(repo_url)
                self.refresh_all()
            except Exception as error:
                self._show_error(self._t("Модификации", "Mods"), f"{self._t('Не удалось импортировать репозиторий', 'Failed to import repository')}:\n{error}")
            return

        if not paths:
            return
        try:
            self.context.mods.import_from_paths(paths)
            self.refresh_all()
        except Exception as error:
            self._show_error(self._t("Модификации", "Mods"), f"{self._t('Не удалось импортировать модификацию', 'Failed to import modification')}:\n{error}")

    def _import_mod_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select mod folder")
        if not path:
            return
        try:
            self.context.mods.import_from_path(path)
            self.refresh_all()
        except Exception as error:
            self._show_error(self._t("Модификации", "Mods"), f"{self._t('Не удалось импортировать папку', 'Failed to import folder')}:\n{error}")

    def _import_mod_archive(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select mod archive", filter="ZIP archive (*.zip)")
        if not path:
            return
        try:
            self.context.mods.import_from_path(path)
            self.refresh_all()
        except Exception as error:
            self._show_error(self._t("Модификации", "Mods"), f"{self._t('Не удалось импортировать архив', 'Failed to import archive')}:\n{error}")

    def _rebuild_runtime(self) -> None:
        self.context.merge.rebuild()
        self.refresh_all()

    def _check_updates_popup(self) -> None:
        self._start_update_check(manual=True)

    def _check_updates_on_start(self) -> None:
        if self._launch_hidden:
            return
        if not self.context.settings.get().check_updates_on_start:
            return
        self._start_update_check(manual=False)

    def _start_update_check(self, manual: bool) -> None:
        if self._update_check_in_progress:
            return
        self._update_check_in_progress = True
        thread = threading.Thread(target=self._run_update_check_worker, args=(manual,), daemon=True)
        thread.start()

    def _run_update_check_worker(self, manual: bool) -> None:
        release = self.context.updates.fetch_latest_application_release()
        self._ui_signals.update_check_done.emit(release, manual)

    def _on_update_check_done(self, release: object, manual: bool) -> None:
        self._update_check_in_progress = False
        if not isinstance(release, dict):
            if manual:
                self._show_error(self._t("Обновления", "Updates"), self._t("Не удалось проверить обновления.", "Failed to check for updates."))
            return

        status = str(release.get("status", "error"))
        latest_version = str(release.get("latest_version", ""))
        if status == "available":
            if manual or self._last_prompted_update_version != latest_version:
                self._last_prompted_update_version = latest_version
                self._show_update_prompt(release)
            return
        if manual:
            if status == "up-to-date":
                self._show_info(
                    self._t("Обновления", "Updates"),
                    self._t(
                        f"У вас уже установлена последняя версия: {release.get('current_version', '')}.",
                        f"You already have the latest version: {release.get('current_version', '')}.",
                    ),
                )
            else:
                self._show_error(
                    self._t("Обновления", "Updates"),
                    str(release.get("error", self._t("Не удалось проверить обновления.", "Failed to check for updates."))),
                )

    def _show_update_prompt(self, release: dict[str, str]) -> None:
        dialog = AppDialog(self, self.context, self._t("Доступно обновление", "Update available"))
        message = QLabel(
            self._t(
                f"Вышла новая версия Zapret Hub.\n\nТекущая версия: {release.get('current_version', '')}\nНовая версия: {release.get('latest_version', '')}",
                f"A new Zapret Hub version is available.\n\nCurrent version: {release.get('current_version', '')}\nNew version: {release.get('latest_version', '')}",
            )
        )
        message.setWordWrap(True)
        dialog.body_layout.addWidget(message)

        body = str(release.get("body", "")).strip()
        if body:
            notes = QLabel(body[:800])
            notes.setWordWrap(True)
            notes.setProperty("class", "muted")
            dialog.body_layout.addWidget(notes)

        row = QHBoxLayout()
        row.addStretch(1)
        close_btn = QPushButton(self._t("Закрыть", "Close"))
        link_btn = QPushButton(self._t("Открыть ссылку", "Open link"))
        update_btn = QPushButton(self._t("Обновить сейчас", "Update now"))
        update_btn.setProperty("class", "primary")
        close_btn.clicked.connect(dialog.reject)
        link_btn.clicked.connect(lambda: self._open_update_link(str(release.get("html_url", ""))))
        update_btn.clicked.connect(lambda: self._start_update_apply(dialog, release))
        row.addWidget(close_btn)
        row.addWidget(link_btn)
        row.addWidget(update_btn)
        dialog.body_layout.addLayout(row)
        dialog.prepare_and_center()
        dialog.exec()

    def _open_update_link(self, url: str) -> None:
        if not url:
            return
        try:
            if sys.platform.startswith("win"):
                import os

                os.startfile(url)  # type: ignore[attr-defined]
            else:
                webbrowser.open(url)
        except Exception:
            webbrowser.open(url)

    def _start_update_apply(self, parent_dialog: AppDialog, release: dict[str, str]) -> None:
        parent_dialog.accept()
        if self._update_prepare_dialog is not None:
            return
        dialog = AppDialog(self, self.context, self._t("Подготовка обновления", "Preparing update"))
        label = QLabel(self._t("Скачиваем и подготавливаем новую версию. Приложение перезапустится автоматически.", "Downloading and preparing the new version. The app will restart automatically."))
        label.setWordWrap(True)
        dialog.body_layout.addWidget(label)
        bar = QProgressBar()
        bar.setRange(0, 0)
        dialog.body_layout.addWidget(bar)
        dialog.prepare_and_center()
        dialog.show()
        self._update_prepare_dialog = dialog
        thread = threading.Thread(target=self._run_update_prepare_worker, args=(release,), daemon=True)
        thread.start()

    def _run_update_prepare_worker(self, release: dict[str, str]) -> None:
        try:
            prepared = self.context.updates.prepare_update(release)
            self._ui_signals.update_prepare_done.emit({"ok": True, "prepared": prepared})
        except Exception as error:
            self._ui_signals.update_prepare_done.emit({"ok": False, "error": str(error)})

    def _on_update_prepare_done(self, payload: object) -> None:
        if self._update_prepare_dialog is not None:
            self._update_prepare_dialog.accept()
            self._update_prepare_dialog = None
        if not isinstance(payload, dict) or not payload.get("ok"):
            self._show_error(
                self._t("Обновления", "Updates"),
                str((payload or {}).get("error", self._t("Не удалось подготовить обновление.", "Failed to prepare the update."))) if isinstance(payload, dict) else self._t("Не удалось подготовить обновление.", "Failed to prepare the update."),
            )
            return
        prepared = payload.get("prepared")
        if not isinstance(prepared, dict):
            self._show_error(self._t("Обновления", "Updates"), self._t("Некорректный пакет обновления.", "Invalid update package."))
            return
        try:
            self.context.updates.launch_update(prepared)
        except Exception as error:
            self._show_error(self._t("Обновления", "Updates"), str(error))
            return
        self._force_exit = True
        self.close()

    def _run_diagnostics_popup(self) -> None:
        results = self.context.diagnostics.run_all()
        text = "\n".join(f"{item.name}: {item.status}" for item in results)
        self._show_info(self._t("Диагностика", "Diagnostics"), text or self._t("Нет данных диагностики.", "No diagnostics data."))

    def _load_selected_file(self, *_args: object) -> None:
        full_path = self._selected_file_path()
        if not full_path:
            return
        item = self.files_list.currentItem()
        label_text = item.text().split("\n")[0] if item else full_path
        self.file_path_label.setText(label_text)
        self.file_editor.setPlainText(self.context.files.read_text(full_path))

    def _save_current_file(self) -> None:
        full_path = self._selected_file_path()
        if not full_path:
            self._show_info(self._t("Файлы", "Files"), self._t("Выберите файл перед сохранением.", "Select a file before saving."))
            return
        self.context.files.write_text(full_path, self.file_editor.toPlainText())
        self.context.logging.log("info", "File saved", path=full_path)
        self.refresh_logs()

    def _rename_current_file(self) -> None:
        full_path = self._selected_file_path()
        if not full_path:
            self._show_info(self._t("Файлы", "Files"), self._t("Выберите файл перед переименованием.", "Select a file before renaming."))
            return
        path = Path(full_path)
        new_name, ok = QInputDialog.getText(self, "Rename file", "New file name:", text=path.name)
        if not ok:
            return
        new_name = new_name.strip()
        if not new_name or new_name == path.name:
            return
        target = path.with_name(new_name)
        if target.exists():
            self._show_warning(self._t("Файлы", "Files"), self._t("Файл с таким именем уже существует.", "A file with this name already exists."))
            return
        try:
            path.rename(target)
            self.context.logging.log("info", "File renamed", source=str(path), target=str(target))
            self.refresh_files()
            self.refresh_logs()
        except Exception as error:
            self._show_error(self._t("Файлы", "Files"), f"{self._t('Не удалось переименовать файл', 'Failed to rename file')}:\n{error}")

    def refresh_all(self) -> None:
        self.refresh_dashboard()
        self.refresh_components()
        self.refresh_mods()
        self.refresh_files()
        self.refresh_logs()

    def refresh_dashboard(self) -> None:
        settings = self.context.settings.get()
        self._refresh_general_combo(settings.selected_zapret_general)
        states = {state.component_id: state for state in self.context.processes.list_states()}
        components = {component.id: component for component in self.context.processes.list_components()}
        active_ids = self._master_active_components()
        zapret_state = states.get("zapret", None)
        tg_state = states.get("tg-ws-proxy", None)
        running_ids = {cid for cid in active_ids if states.get(cid) and states[cid].status == "running"}
        any_running = len(running_ids) > 0
        fully_running = bool(active_ids) and set(active_ids) == running_ids

        self.power_button.setProperty("state", "on" if fully_running else "off")
        self.power_button.style().unpolish(self.power_button)
        self.power_button.style().polish(self.power_button)
        if not active_ids:
            self.power_caption.setText(self._t("НЕТ КОМПОНЕНТОВ", "NO COMPONENTS"))
        else:
            self.power_caption.setText(self._t("ВКЛ", "ON") if fully_running else (self._t("ЧАСТИЧНО", "PARTIAL") if any_running else self._t("ВЫКЛ", "OFF")))

        installed_mods = self.context.mods.list_installed()
        enabled_mods = [mod.id for mod in installed_mods if mod.enabled]
        merge_state = self.context.merge.get_state()

        self._set_badge("app", self._t("Работает", "Running") if fully_running else (self._t("Частично", "Partial") if any_running else self._t("Ожидание", "Idle")), "status_ok.svg" if fully_running else ("status_warn.svg" if any_running else "status_off.svg"))
        zapret_text, zapret_icon = self._component_badge_state(components.get("zapret"), zapret_state, any_running)
        tg_text, tg_icon = self._component_badge_state(components.get("tg-ws-proxy"), tg_state, any_running)
        self._set_badge("zapret", zapret_text, zapret_icon)
        self._set_badge("tg", tg_text, tg_icon)
        self._set_badge("mods", f"{len(enabled_mods)} {self._t('Активно', 'Active')}", "status_mod.svg")
        self._set_badge("theme", settings.theme.title(), "status_theme.svg")

        if merge_state is None and enabled_mods:
            self.context.merge.rebuild()

    def _component_badge_state(self, component: object, state: object, any_running: bool) -> tuple[str, str]:
        status = str(getattr(state, "status", "unknown") or "unknown").lower()
        last_error = str(getattr(state, "last_error", "") or "").strip()
        enabled = bool(getattr(component, "enabled", False))
        if status == "running":
            return self._t("Работает", "Running"), "status_ok.svg"
        if last_error or (enabled and any_running):
            return self._t("Ошибка", "Error") if last_error else self._t("Не Запущен", "Not Running"), "status_warn.svg"
        if status == "stopped":
            return self._t("Остановлен", "Stopped"), "status_off.svg"
        return self._t("Неизвестно", "Unknown"), "status_off.svg"

    def _refresh_general_combo(self, selected_id: str) -> None:
        options = self.context.processes.list_zapret_generals()
        self._updating_general_combo = True
        try:
            self.general_combo.clear()
            for option in options:
                label = self._format_general_option_label(option)
                self.general_combo.addItem(label, option["id"])
            if self.general_combo.count() == 0:
                return
            target_id = selected_id
            if not target_id:
                target_id = self.general_combo.itemData(0)
                if target_id:
                    self.context.settings.update(selected_zapret_general=target_id)
            for i in range(self.general_combo.count()):
                if self.general_combo.itemData(i) == target_id:
                    self.general_combo.setCurrentIndex(i)
                    break
        finally:
            self._updating_general_combo = False

    def _on_general_selected(self, _index: int) -> None:
        if self._updating_general_combo:
            return
        selected = self.general_combo.currentData()
        if not selected:
            return
        current = self.context.settings.get().selected_zapret_general
        if selected == current:
            return
        self.context.settings.update(selected_zapret_general=selected)
        states = {s.component_id: s for s in self.context.processes.list_states()}
        zapret_running = states.get("zapret") and states["zapret"].status == "running"
        if zapret_running:
            self._loading_action = "connect"
            self._toggle_in_progress = True
            self.power_button.setEnabled(False)
            self._loading_frame = 0
            self._loading_timer.start()
            self._advance_loading_caption()
            thread = threading.Thread(target=self._restart_zapret_worker, daemon=True)
            thread.start()
        else:
            self.refresh_all()

    def _on_general_selected_from_components(self, selected: str, combo: QComboBox, status_label: QLabel) -> None:
        if not selected:
            return
        current = self.context.settings.get().selected_zapret_general
        if selected == current:
            return
        if self._general_loading_combo is not None:
            return
        self._general_loading_combo = combo
        self._general_loading_label = status_label
        combo.setEnabled(False)
        status_label.show()
        self._component_loading_frame = 0
        if not self._component_loading_timer.isActive():
            self._component_loading_timer.start()
        self._advance_component_loading()
        thread = threading.Thread(target=self._apply_general_selection_worker, args=(selected,), daemon=True)
        thread.start()

    def _apply_general_selection_worker(self, selected: str) -> None:
        self.context.settings.update(selected_zapret_general=selected)
        states = {s.component_id: s for s in self.context.processes.list_states()}
        zapret_running = states.get("zapret") and states["zapret"].status == "running"
        if zapret_running:
            self.context.processes.stop_component("zapret")
            self.context.processes.start_component("zapret")
        self._ui_signals.component_action_done.emit("__general__")

    def _master_active_components(self) -> list[str]:
        return [c.id for c in self.context.processes.list_components() if c.id in ("zapret", "tg-ws-proxy") and c.enabled]

    def _maybe_run_first_general_autotest(self) -> None:
        settings = self.context.settings.get()
        options = self.context.processes.list_zapret_generals()
        if not options:
            return
        if settings.selected_zapret_general and any(item["id"] == settings.selected_zapret_general for item in options):
            if not settings.general_autotest_done:
                self.context.settings.update(general_autotest_done=True)
            return
        answer = self._ask_yes_no(
            self._t("Первичная настройка", "First setup"),
            self._t("Конфигурация пока не выбрана.\n\nЗапустить автоподбор сейчас?", "No configuration is selected yet.\n\nRun auto-check now to find a working one?"),
        )
        if not answer:
            self.context.settings.update(general_autotest_done=True)
            self.refresh_all()
            return
        self._loading_action = "connect"
        self._toggle_in_progress = True
        self.power_button.setEnabled(False)
        self._loading_frame = 0
        self._loading_timer.start()
        self._advance_loading_caption()
        thread = threading.Thread(target=self._run_general_autotest_worker, daemon=True)
        thread.start()

    def _run_general_autotest_worker(self) -> None:
        result = self.context.processes.auto_select_working_general()
        self.context.settings.update(general_autotest_done=True)
        if result and result.get("id"):
            self.context.logging.log("info", "Auto-test selected general", general=result.get("id"))
            full = str(result.get("status")) == "ok"
            self._pending_info_message = (
                self._t("Настройка завершена", "Setup complete") if full else self._t("Лучший результат", "Best result"),
                self._t("Рабочая конфигурация найдена.\nОна выбрана автоматически.", "A working configuration was found.\nIt is now selected automatically.")
                if full
                else self._t(
                    f"Полностью рабочая конфигурация не найдена.\nВыбран лучший результат: {int(result.get('passed_targets', 0))}/{int(result.get('total_targets', 0))} тестов.",
                    f"No fully working configuration was found.\nBest result selected: {int(result.get('passed_targets', 0))}/{int(result.get('total_targets', 0))} tests.",
                ),
            )
        else:
            self._pending_info_message = (
                self._t("Результат настройки", "Setup result"),
                self._t("Автоматически рабочая конфигурация не найдена.\nВыберите её вручную из списка.", "No working configuration was found automatically.\nPlease pick one manually from the list."),
            )
        self._ui_signals.toggle_done.emit()

    def _restart_zapret_worker(self) -> None:
        self.context.processes.stop_component("zapret")
        self.context.processes.start_component("zapret")
        self._ui_signals.toggle_done.emit()

    def _on_component_action_done(self, action_id: str) -> None:
        if action_id == "__general__":
            if self._general_loading_combo is not None:
                try:
                    self._general_loading_combo.setEnabled(True)
                except RuntimeError:
                    pass
            if self._general_loading_label is not None:
                try:
                    self._general_loading_label.hide()
                    self._general_loading_label.setText("")
                except RuntimeError:
                    pass
            self._general_loading_combo = None
            self._general_loading_label = None
            if not self._component_loading_buttons:
                self._component_loading_timer.stop()
            self.refresh_all()
            return

        self._stop_component_loading(action_id)
        self.refresh_all()

    def _run_general_tests_popup(self) -> None:
        if self._general_test_running:
            return
        options = self.context.processes.list_zapret_generals()
        if not options:
            self._show_info(self._t("Проверка конфигураций", "Run general tests"), self._t("Список конфигураций пока пуст.", "The configuration list is empty."))
            return

        self._general_test_running = True
        self._general_test_cancelled = False
        self._general_test_show_results = True
        dialog = AppDialog(self, self.context, self._t("Проверка конфигураций", "Run general tests"))
        title = QLabel(
            self._t(
                "Сейчас приложение по очереди проверит все доступные конфигурации и посмотрит, какие из них действительно дают подключение ко всем тестовым серверам. Этот процесс может занять много времени.",
                "The app will now test each available configuration and show which ones can actually reach all test servers. This process may take a while.",
            )
        )
        title.setWordWrap(True)
        dialog.body_layout.addWidget(title)
        status = QLabel(self._t("Подготовка...", "Preparing..."))
        status.setProperty("class", "muted")
        dialog.body_layout.addWidget(status)
        bar = QProgressBar()
        bar.setRange(0, len(options))
        bar.setValue(0)
        dialog.body_layout.addWidget(bar)
        dialog.prepare_and_center()
        dialog.show()
        self._general_test_dialog = dialog
        self._general_test_status_label = status
        self._general_test_progress_bar = bar
        dialog.rejected.connect(self._cancel_general_tests)
        thread = threading.Thread(target=self._run_general_tests_worker, daemon=True)
        thread.start()

    def _run_general_tests_worker(self) -> None:
        results = self.context.processes.run_general_diagnostics(
            progress_callback=lambda current, total, name: self._ui_signals.general_test_progress.emit(current, total, name),
            stop_callback=lambda: self._general_test_cancelled,
        )
        self._ui_signals.general_test_done.emit(results)

    def _cancel_general_tests(self) -> None:
        self._general_test_cancelled = True
        self._general_test_show_results = False
        try:
            self.context.processes.stop_all()
        except Exception:
            pass

    def _on_general_test_progress(self, current: int, total: int, name: str) -> None:
        if self._general_test_progress_bar is not None:
            self._general_test_progress_bar.setMaximum(total)
            self._general_test_progress_bar.setValue(current)
        if self._general_test_status_label is not None:
            self._general_test_status_label.setText(
                self._t(
                    f"Проверяется: {name} ({current}/{total})",
                    f"Checking: {name} ({current}/{total})",
                )
            )

    def _on_general_test_done(self, results: object) -> None:
        self._general_test_running = False
        if self._general_test_dialog is not None:
            self._general_test_dialog.accept()
        self._general_test_dialog = None
        self._general_test_status_label = None
        self._general_test_progress_bar = None

        checked = results if isinstance(results, list) else []
        working: list[str] = []
        failed: list[str] = []
        best_label = ""
        best_score = -1
        best_total = 0
        for raw in checked:
            if not isinstance(raw, dict):
                continue
            label = self._format_general_option_label(
                {
                    "bundle": str(raw.get("bundle", "")),
                    "name": str(raw.get("name", "")),
                }
            )
            passed = int(str(raw.get("passed_targets", 0)) or 0)
            total = int(str(raw.get("total_targets", 0)) or 0)
            if passed > best_score:
                best_score = passed
                best_total = total
                best_label = label
            if raw.get("status") == "ok":
                working.append(label)
            else:
                error_text = str(raw.get("error", "")).strip() or self._t("не удалось запустить", "failed to start")
                failed.append(f"{label} - {error_text}")

        if not self._general_test_show_results:
            self.refresh_all()
            return

        dialog = AppDialog(self, self.context, self._t("Результаты проверки", "Test results"))
        title = QLabel(self._t("Проверка завершена.", "Testing is complete."))
        title.setProperty("class", "title")
        dialog.body_layout.addWidget(title)
        summary = QTextEdit()
        summary.setReadOnly(True)
        summary.setMinimumHeight(260)
        summary.setPlainText(
            f"{self._t('Работают:', 'Working:')}\n"
            + ("\n".join(working) if working else self._t("Нет полностью работающих конфигураций.", "No fully working configurations."))
            + "\n\n"
            + (
                f"{self._t('Лучший результат:', 'Best result:')}\n{best_label} ({best_score}/{best_total})\n\n"
                if not working and best_label
                else ""
            )
            + f"{self._t('Не работают или дают ошибку:', 'Not working or failed:')}\n"
            + ("\n".join(failed) if failed else self._t("Ошибок не обнаружено.", "No failed configurations."))
        )
        dialog.body_layout.addWidget(summary)
        row = QHBoxLayout()
        row.addStretch(1)
        ok_btn = QPushButton(self._t("Ок", "OK"))
        ok_btn.setProperty("class", "primary")
        ok_btn.clicked.connect(dialog.accept)
        row.addWidget(ok_btn)
        dialog.body_layout.addLayout(row)
        dialog.prepare_and_center()
        dialog.exec()

    def _set_badge(self, key: str, text: str, icon_name: str) -> None:
        badge = self._status_badges.get(key)
        if not badge:
            return
        badge.value_label.setText(text)
        badge.icon_label.setPixmap(self._icon(icon_name).pixmap(18, 18))

    def _show_info(self, title: str, text: str) -> None:
        dialog = AppDialog(self, self.context, title)
        label = QLabel(text)
        label.setWordWrap(True)
        dialog.body_layout.addWidget(label)
        row = QHBoxLayout()
        row.addStretch(1)
        ok_btn = QPushButton(self._t("Ок", "OK"))
        ok_btn.setProperty("class", "primary")
        ok_btn.clicked.connect(dialog.accept)
        row.addWidget(ok_btn)
        dialog.body_layout.addLayout(row)
        dialog.prepare_and_center()
        dialog.exec()

    def _show_warning(self, title: str, text: str) -> None:
        self._show_info(title, text)

    def _show_error(self, title: str, text: str) -> None:
        self._show_info(title, text)

    def _ask_text_value(self, title: str, text: str, placeholder: str = "") -> str:
        dialog = AppDialog(self, self.context, title)
        label = QLabel(text)
        label.setWordWrap(True)
        dialog.body_layout.addWidget(label)
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        dialog.body_layout.addWidget(field)
        row = QHBoxLayout()
        row.addStretch(1)
        cancel_btn = QPushButton(self._t("Отмена", "Cancel"))
        ok_btn = QPushButton(self._t("Загрузить", "Load"))
        ok_btn.setProperty("class", "primary")
        cancel_btn.clicked.connect(dialog.reject)
        ok_btn.clicked.connect(dialog.accept)
        row.addWidget(cancel_btn)
        row.addWidget(ok_btn)
        dialog.body_layout.addLayout(row)
        dialog.prepare_and_center()
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return ""
        return field.text().strip()

    def _ask_yes_no(self, title: str, text: str) -> bool:
        dialog = AppDialog(self, self.context, title)
        label = QLabel(text)
        label.setWordWrap(True)
        dialog.body_layout.addWidget(label)
        row = QHBoxLayout()
        row.addStretch(1)
        no_btn = QPushButton(self._t("Нет", "No"))
        yes_btn = QPushButton(self._t("Да", "Yes"))
        yes_btn.setProperty("class", "primary")
        no_btn.clicked.connect(dialog.reject)
        yes_btn.clicked.connect(dialog.accept)
        row.addWidget(no_btn)
        row.addWidget(yes_btn)
        dialog.body_layout.addLayout(row)
        dialog.prepare_and_center()
        return dialog.exec() == QDialog.DialogCode.Accepted

    def refresh_components(self) -> None:
        components = self.context.processes.list_components()
        states = {item.component_id: item for item in self.context.processes.list_states()}
        self.components_list.clear()
        for component in components:
            state = states.get(component.id)
            status_text = state.status if state else "stopped"
            subtitle = f"{self._t('Версия', 'Version')}: {component.version} | {self._t('Включен', 'Enabled')}: {self._t('да', 'yes') if component.enabled else self._t('нет', 'no')} | {self._t('Автозапуск', 'Autostart')}: {self._t('да', 'yes') if component.autostart else self._t('нет', 'no')} | {self._t('Статус', 'Status')}: {status_text}"
            source = f"{self._t('Источник', 'Source')}: {component.source}"
            display_name = {"zapret": "Zapret", "tg-ws-proxy": "Tg-Ws-Proxy"}.get(component.id, component.name)
            item = QListWidgetItem(f"{display_name}\n{subtitle}\n{source}")
            item.setData(Qt.ItemDataRole.UserRole, component.id)
            item.setSizeHint(QSize(200, 70))
            self.components_list.addItem(item)
        if self._components_cards_layout is None:
            return

        while self._components_cards_layout.count():
            layout_item = self._components_cards_layout.takeAt(0)
            widget = layout_item.widget()
            if widget is not None:
                widget.deleteLater()

        descriptions = {
            "zapret": self._t(
                "Классический способ обхода блокировок через DPI.",
                "A classic DPI-based bypass method for blocked services.",
            ),
            "tg-ws-proxy": self._t(
                "Локальный Telegram Proxy. Позволяет подключаться к Telegram в обход блокировок, маскируясь под обычный https-трафик.",
                "Local Telegram Proxy. Lets Telegram connect through restrictions by blending in with regular HTTPS traffic.",
            ),
        }
        icons = {"zapret": "component_zapret.svg", "tg-ws-proxy": "component_tg.svg"}

        for component in components:
            state = states.get(component.id)
            status_text, _status_icon = self._component_badge_state(component, state, any_running=False)
            display_name = {"zapret": "Zapret", "tg-ws-proxy": "Tg-Ws-Proxy"}.get(component.id, component.name)
            card, card_layout = self._card()
            card.setMinimumHeight(300)
            icon = QLabel()
            icon_size = 38 if component.id == "tg-ws-proxy" else 36
            icon.setPixmap(self._icon(icons.get(component.id, "components.svg")).pixmap(icon_size, icon_size))
            icon_row = QHBoxLayout()
            icon_row.setContentsMargins(0, 12, 0, 0)
            icon_row.setSpacing(0)
            icon_row.addWidget(icon, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            icon_row.addStretch(1)
            card_layout.addLayout(icon_row)

            title = QLabel(display_name)
            title.setProperty("class", "title")
            title.setWordWrap(True)
            card_layout.addWidget(title)

            desc = QLabel(descriptions.get(component.id, component.description))
            desc.setProperty("class", "muted")
            desc.setWordWrap(True)
            card_layout.addWidget(desc)

            details = QLabel(
                f"Author: Flowseal\n"
                f"{self._t('Status', 'Status')}: {status_text}\n"
                f"{self._t('Version', 'Version')}: {component.version}"
            )
            details.setProperty("class", "muted")
            details.setWordWrap(True)
            card_layout.addWidget(details)
            card_layout.addStretch(1)

            enabled_text = self._t("включен", "enabled") if component.enabled else self._t("выключен", "disabled")
            participation = QLabel(f"{self._t('Участие в ON/OFF', 'ON/OFF participation')}: {enabled_text}")
            participation.setWordWrap(True)
            card_layout.addWidget(participation)
            if component.id == "zapret":
                config_label = QLabel(self._t("Конфигурация Zapret", "Zapret Configuration"))
                config_label.setProperty("class", "muted")
                card_layout.addWidget(config_label)
                config_combo = QComboBox()
                config_status = QLabel("")
                config_status.setProperty("class", "muted")
                config_status.hide()
                options = self.context.processes.list_zapret_generals()
                selected = self.context.settings.get().selected_zapret_general
                for option in options:
                    config_combo.addItem(self._format_general_option_label(option), option["id"])
                if config_combo.count() > 0:
                    picked_index = 0
                    for i in range(config_combo.count()):
                        if config_combo.itemData(i) == selected:
                            picked_index = i
                            break
                    config_combo.setCurrentIndex(picked_index)
                config_combo.currentIndexChanged.connect(
                    lambda _=0, combo=config_combo, status_label=config_status: self._on_general_selected_from_components(
                        str(combo.currentData() or ""),
                        combo,
                        status_label,
                    )
                )
                card_layout.addWidget(config_combo)
                card_layout.addWidget(config_status)

            if component.id == "tg-ws-proxy":
                connect_btn = QPushButton(self._t("Подключить к Telegram", "Connect to Telegram"))
                connect_btn.clicked.connect(self._prompt_tg_proxy_connect)
                card_layout.addWidget(connect_btn)

            toggle_btn = QPushButton(
                self._t("Выключить компонент", "Disable component")
                if component.enabled
                else self._t("Включить компонент", "Enable component")
            )
            toggle_btn.setProperty("class", "danger" if component.enabled else "primary")
            toggle_btn.clicked.connect(lambda _=False, cid=component.id, btn=toggle_btn: self._toggle_component_card(cid, btn))
            card_layout.addWidget(toggle_btn)
            self._components_cards_layout.addWidget(card, 1)

    def _prompt_tg_proxy_connect(self) -> None:
        try:
            self.context.processes.prompt_telegram_proxy_link()
        except Exception as error:
            self._show_error(
                self._t("TG Proxy", "TG Proxy"),
                f"{self._t('Не удалось открыть запрос на подключение в Telegram.', 'Failed to open Telegram connection prompt.')}\n{error}",
            )

    def _refresh_mods_legacy(self) -> None:
        index = self.context.mods.fetch_index()
        installed = {item.id: item for item in self.context.mods.list_installed()}
        combined: list[tuple[str, str, str, str, str, str]] = []
        seen: set[str] = set()
        for item in index:
            seen.add(item.id)
            state = "not installed"
            if item.id in installed:
                state = "enabled" if installed[item.id].enabled else "installed"
            combined.append(
                (
                    item.id,
                    item.name,
                    item.description,
                    f"{self._t('Автор', 'Author')}: {item.author} | {self._t('Версия', 'Version')}: {item.version} | {self._t('Статус', 'Status')}: {state}",
                    f"{self._t('Категория', 'Category')}: {item.category}",
                    state,
                )
            )

        for mod_id, item in installed.items():
            if mod_id in seen:
                continue
            state = "enabled" if item.enabled else "installed"
            source_type = "zapret bundle" if item.source_type == "zapret_bundle" else item.source_type
            combined.append(
                (
                    mod_id,
                    mod_id,
                    self._t("Локальная модификация без пользовательского описания.", "Local modification without user description."),
                    f"{self._t('Локальный импорт', 'Local import')} | {self._t('Версия', 'Version')}: {item.version} | {self._t('Статус', 'Status')}: {state}",
                    f"{self._t('Тип', 'Type')}: {source_type}",
                    state,
                )
            )

        selected = self._selected_mod_id()
        self.mods_list.clear()
        for mod_id, name, description, subtitle, tags, _state in combined:
            row_item = QListWidgetItem(f"{name}\n{description}\n{subtitle}\n{tags}")
            row_item.setData(Qt.ItemDataRole.UserRole, mod_id)
            row_item.setSizeHint(QSize(200, 88))
            self.mods_list.addItem(row_item)
        if selected:
            for i in range(self.mods_list.count()):
                it = self.mods_list.item(i)
                if it.data(Qt.ItemDataRole.UserRole) == selected:
                    self.mods_list.setCurrentItem(it)
                    break

    def _toggle_mod_by_id(self, mod_id: str) -> None:
        installed = {item.id: item for item in self.context.mods.list_installed()}
        if mod_id not in installed:
            self.context.mods.install(mod_id)
            installed = {item.id: item for item in self.context.mods.list_installed()}
        if mod_id in installed:
            self.context.mods.set_enabled(mod_id, not installed[mod_id].enabled)
        self.refresh_all()

    def refresh_mods(self) -> None:
        index = self.context.mods.fetch_index()
        installed = {item.id: item for item in self.context.mods.list_installed()}
        combined: list[dict[str, str | bool]] = []
        seen: set[str] = set()
        for item in index:
            seen.add(item.id)
            enabled = item.id in installed and installed[item.id].enabled
            state = "enabled" if enabled else ("installed" if item.id in installed else "not installed")
            combined.append(
                {
                    "id": item.id,
                    "name": item.name,
                    "description": item.description or self._t("Описание не указано.", "No description."),
                    "subtitle": f"{self._t('Автор', 'Author')}: {item.author} | {self._t('Версия', 'Version')}: {item.version}",
                    "state": state,
                    "enabled": enabled,
                    "changelog": item.changelog or "",
                }
            )

        for mod_id, item in installed.items():
            if mod_id in seen:
                continue
            combined.append(
                {
                    "id": mod_id,
                    "name": item.name or mod_id,
                    "description": item.description or self._t("Локальная модификация без описания.", "Local mod without description."),
                    "subtitle": f"{self._t('Автор', 'Author')}: {item.author or 'goshkow'} | {self._t('Версия', 'Version')}: {item.version}",
                    "state": "enabled" if item.enabled else "installed",
                    "enabled": item.enabled,
                    "changelog": "",
                }
            )

        if not hasattr(self, "mods_cards_layout"):
            return

        enabled_count = sum(1 for mod in combined if bool(mod["enabled"]))
        if hasattr(self, "mods_summary_chip"):
            self.mods_summary_chip.setText(
                self._t(
                    f"Всего пакетов: {len(combined)}",
                    f"Total packs: {len(combined)}",
                )
            )
        if hasattr(self, "mods_enabled_chip"):
            self.mods_enabled_chip.setText(
                self._t(
                    f"Активно сейчас: {enabled_count}",
                    f"Active now: {enabled_count}",
                )
            )

        while self.mods_cards_layout.count():
            child = self.mods_cards_layout.takeAt(0)
            widget = child.widget()
            if widget is not None:
                widget.deleteLater()

        if not combined:
            empty, empty_layout = self._card()
            empty.setProperty("class", "modCard")
            title = QLabel(self._t("Пока пусто", "Nothing here yet"))
            title.setProperty("class", "title")
            text = QLabel(
                self._t(
                    "Добавьте архив, конфиг или папку с файлами, чтобы здесь появились модификации.",
                    "Add an archive, config, or folder with files and your modifications will appear here.",
                )
            )
            text.setProperty("class", "muted")
            text.setWordWrap(True)
            empty_layout.addWidget(title)
            empty_layout.addWidget(text)
            self.mods_cards_layout.addWidget(empty)
            self.mods_cards_layout.addStretch(1)
            return

        for mod in combined:
            mod_id = str(mod["id"])
            enabled = bool(mod["enabled"])
            state = str(mod["state"])
            if mod_id == "unified-by-goshkow":
                mod["description"] = self._t(
                    "Позволяет обойти блокировки самых популярных сервисов, включая игровые сервисы, социальные сети и другие платформы.",
                    "Helps bypass restrictions for the most popular services, including gaming platforms, social networks, and other services.",
                )

            card = QFrame()
            card.setProperty("class", "modCard")
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(16, 16, 16, 16)
            card_layout.setSpacing(16)

            icon_wrap = QFrame()
            icon_wrap.setProperty("class", "modIconWrap")
            icon_wrap.setFixedSize(54, 54)
            icon_row = QVBoxLayout(icon_wrap)
            icon_row.setContentsMargins(0, 0, 0, 0)
            icon_row.setSpacing(0)
            icon_label = QLabel()
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setPixmap(self._icon("mods.svg").pixmap(24, 24))
            icon_row.addWidget(icon_label)
            card_layout.addWidget(icon_wrap, 0, Qt.AlignmentFlag.AlignTop)

            body = QVBoxLayout()
            body.setContentsMargins(0, 0, 0, 0)
            body.setSpacing(10)

            head = QHBoxLayout()
            head.setContentsMargins(0, 0, 0, 0)
            head.setSpacing(10)

            text_col = QVBoxLayout()
            text_col.setContentsMargins(0, 0, 0, 0)
            text_col.setSpacing(5)
            title = QLabel(str(mod["name"]))
            title.setProperty("class", "title")
            text_col.addWidget(title)

            state_map = {
                "enabled": self._t("Включена", "Enabled"),
                "installed": self._t("Выключена", "Disabled"),
                "not installed": self._t("Еще не подключена", "Not added yet"),
            }
            badge = QLabel(state_map.get(state, state))
            badge.setProperty("class", "modState")
            badge.setProperty("state", state)
            badge.setObjectName("ModStateBadge")
            text_col.addWidget(badge, 0, Qt.AlignmentFlag.AlignLeft)
            head.addLayout(text_col, 1)

            actions = QHBoxLayout()
            actions.setContentsMargins(0, 0, 0, 0)
            actions.setSpacing(8)

            info_btn = QPushButton(self._t("Подробнее", "Details"))
            info_btn.setIcon(self._icon("files.svg"))
            info_btn.setIconSize(QSize(14, 14))
            info_btn.clicked.connect(lambda _=False, m=mod: self._show_info(str(m["name"]), f"{m['description']}\n\n{m['changelog']}"))
            self._attach_button_animations(info_btn)
            actions.addWidget(info_btn)

            toggle_btn = QPushButton(
                self._t("Выключить", "Disable")
                if enabled
                else self._t("Включить", "Enable")
            )
            toggle_btn.setProperty("class", "primary")
            toggle_btn.setIcon(self._icon("power.svg"))
            toggle_btn.setIconSize(QSize(14, 14))
            toggle_btn.clicked.connect(lambda _=False, mid=mod_id: self._toggle_mod_by_id(mid))
            self._attach_button_animations(toggle_btn)
            actions.addWidget(toggle_btn)

            remove_btn = QPushButton(self._t("Удалить", "Remove"))
            remove_btn.setProperty("class", "danger")
            remove_btn.setIcon(self._icon("window_close.svg"))
            remove_btn.setIconSize(QSize(14, 14))
            remove_btn.clicked.connect(lambda _=False, mid=mod_id: self.context.mods.remove(mid) or self.refresh_all())
            self._attach_button_animations(remove_btn)
            if mod_id != "unified-by-goshkow":
                actions.addWidget(remove_btn)
            head.addLayout(actions)
            body.addLayout(head)

            desc = QLabel(str(mod["description"]))
            desc.setWordWrap(True)
            desc.setProperty("class", "modBody")
            body.addWidget(desc)

            meta_row = QHBoxLayout()
            meta_row.setContentsMargins(0, 0, 0, 0)
            meta_row.setSpacing(8)
            for meta_text in str(mod["subtitle"]).split(" | "):
                meta = QLabel(meta_text)
                meta.setProperty("class", "modMeta")
                meta.setObjectName("ModMetaChip")
                meta_row.addWidget(meta)
            meta_row.addStretch(1)
            body.addLayout(meta_row)
            card_layout.addLayout(body, 1)
            self.mods_cards_layout.addWidget(card)

        self.mods_cards_layout.addStretch(1)

    def refresh_files(self) -> None:
        records = self.context.files.list_files()
        selected = self._selected_file_path()
        self.files_list.clear()
        for record in records:
            row_item = QListWidgetItem(f"{record.relative_path}\n{self._t('Размер', 'Size')}: {record.size} {self._t('байт', 'bytes')}")
            row_item.setData(Qt.ItemDataRole.UserRole, record.path)
            row_item.setSizeHint(QSize(200, 54))
            self.files_list.addItem(row_item)
        if selected:
            for i in range(self.files_list.count()):
                it = self.files_list.item(i)
                if it.data(Qt.ItemDataRole.UserRole) == selected:
                    self.files_list.setCurrentItem(it)
                    break

    def refresh_logs(self) -> None:
        entries = self.context.logging.read_entries()
        lines = [f"[{e.timestamp}] {e.level}: {e.message} {e.context}" for e in entries[-250:]]
        self.logs_text.setPlainText("\n".join(lines))



