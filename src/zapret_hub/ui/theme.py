from __future__ import annotations


def build_stylesheet(theme: str, chevron_icon: str = "", check_icon: str = "") -> str:
    dark = """
    QWidget {
        background: #0f1420;
        color: #d9e0f0;
        font-family: "Segoe UI";
        font-size: 10pt;
    }
    #WindowShell {
        background: transparent;
    }
    QStackedWidget, QStackedWidget > QWidget {
        background: transparent;
    }
    QWidget[class="pageRoot"], QWidget[class="pageCanvas"] {
        background: transparent;
    }
    QLabel {
        background: transparent;
    }
    #RootFrame {
        background: #101725;
        border: 1px solid #24304a;
        border-radius: 16px;
    }
    #TitleBar {
        background: #101726;
        border: none;
        border-top-left-radius: 16px;
        border-top-right-radius: 16px;
    }
    #Sidebar {
        background: #101726;
        border-bottom-left-radius: 16px;
    }
    #Content {
        background: transparent;
        border: none;
    }
    #ContentSurface {
        background: qlineargradient(x1:0, y1:1, x2:1, y2:0, stop:0 #0d1320, stop:0.62 #101827, stop:1 #172339);
        border-top: 1px solid #24304a;
        border-left: 1px solid #24304a;
        border-top-left-radius: 18px;
        border-top-right-radius: 0px;
        border-bottom-left-radius: 0px;
        border-bottom-right-radius: 16px;
    }
    QDialog#AppDialogWindow {
        background: transparent;
        border: none;
    }
    #DialogRoot {
        background: #151f33;
        border: 1px solid #243550;
        border-radius: 12px;
    }
    #DialogTitleBar {
        background: transparent;
        border: none;
        border-top-left-radius: 12px;
        border-top-right-radius: 12px;
    }
    #DialogBody {
        background: transparent;
    }
    #LoadingOverlay {
        background: rgba(9, 13, 22, 0.42);
    }
    #LoadingCard {
        background: #141f32;
        border: 1px solid #2d456d;
        border-radius: 16px;
    }
    QFrame[class="card"] {
        background: qlineargradient(x1:0, y1:1, x2:1, y2:0, stop:0 #131d30, stop:0.68 #162238, stop:1 #1a2842);
        border: 1px solid #243550;
        border-radius: 16px;
    }
    QFrame[class="modHero"] {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #17253d, stop:1 #131d30);
        border: 1px solid #2a436a;
        border-radius: 16px;
    }
    QFrame[class="modCard"] {
        background: #141f32;
        border: 1px solid #284061;
        border-radius: 16px;
    }
    QFrame[class="modIconWrap"] {
        background: #1b2b45;
        border: 1px solid #35527d;
        border-radius: 16px;
    }
    QLabel[class="title"] {
        font-size: 13pt;
        font-weight: 700;
        color: #f5f7fc;
    }
    #DashboardTitle {
        padding: 0px;
        margin: 0px;
    }
    #DashboardPowerBlock {
        background: transparent;
    }
    QLabel[class="muted"] {
        color: #90a1c2;
    }
    QLabel[class="modHint"] {
        color: #a9b8d8;
    }
    QLabel[class="modState"] {
        color: #f8fbff;
        background: #21324f;
        border: 1px solid #39547d;
        border-radius: 12px;
        padding: 6px 12px;
        font-weight: 600;
    }
    QLabel[class="modState"][state="enabled"] {
        background: rgba(44, 163, 93, 0.16);
        border: 1px solid #2f8f5d;
        color: #a8efc1;
    }
    QLabel[class="modState"][state="installed"] {
        background: rgba(104, 137, 186, 0.16);
        border: 1px solid #5070a4;
        color: #d6e4ff;
    }
    QLabel[class="modState"][state="not installed"] {
        background: rgba(150, 164, 192, 0.12);
        border: 1px solid #4b617f;
        color: #bcc9df;
    }
    QLabel[class="modMeta"] {
        color: #afbdd9;
        background: #18253d;
        border: 1px solid #2b446a;
        border-radius: 12px;
        padding: 6px 12px;
    }
    #ModsSummaryChip, #ModsEnabledChip {
        border-radius: 11px;
    }
    #ModStateBadge, #ModMetaChip {
        border-radius: 12px;
    }
    QLabel[class="modBody"] {
        color: #d7e1f2;
        line-height: 1.3em;
    }
    #ModsScroll, #ModsCanvas {
        background: transparent;
        border: none;
    }
    QToolButton[class="nav"] {
        min-width: 44px;
        min-height: 44px;
        max-width: 44px;
        max-height: 44px;
        border-radius: 12px;
        border: 1px solid transparent;
        background: transparent;
    }
    QToolButton[class="nav"]:hover {
        background: #1e2a43;
        border: 1px solid #35507a;
    }
    QToolButton[class="nav"]:checked {
        background: #2a3d61;
        border: 1px solid #4f73b3;
    }
    QToolButton[class="window"] {
        min-width: 26px;
        min-height: 26px;
        max-width: 26px;
        max-height: 26px;
        border-radius: 12px;
        border: none;
        background: transparent;
        padding: 0px;
        margin: 0px;
    }
    QToolButton[class="window"][role="min"],
    QToolButton[class="window"][role="close"] {
        padding: 0px 1px 2px 0px;
    }
    QToolButton[class="window"][role="close"] {
        padding: 0px 1px 1px 0px;
    }
    QToolButton[class="window"]:hover {
        background: rgba(83, 108, 148, 0.25);
    }
    QToolButton[class="window"][role="close"]:hover {
        background: rgba(170, 84, 97, 0.62);
    }
    QPushButton {
        background: #243552;
        border: 1px solid #35517f;
        border-radius: 10px;
        padding: 8px 12px;
    }
    QPushButton:hover {
        background: #2d4268;
    }
    QToolButton[class="action"] {
        min-width: 26px;
        min-height: 26px;
        max-width: 26px;
        max-height: 26px;
        border: none;
        border-radius: 12px;
        background: transparent;
        padding: 0;
        margin: 0;
    }
    QToolButton[class="action"]:hover {
        background: rgba(83, 108, 148, 0.25);
    }
    QToolButton[class="action"]::menu-indicator {
        image: none;
        width: 0px;
        height: 0px;
    }
    QFrame[class="fileModeCard"] {
        background: qlineargradient(x1:0, y1:1, x2:1, y2:0, stop:0 #141e31, stop:1 #1a2942);
        border: 1px solid #2e466d;
        border-radius: 14px;
    }
    QFrame[class="fileModeCard"][hovered="true"] {
        background: qlineargradient(x1:0, y1:1, x2:1, y2:0, stop:0 #1a2842, stop:1 #203252);
        border: 1px solid #4f73b3;
    }
    QPushButton[class="primary"] {
        background: #5865f2;
        border-color: #6773ff;
        color: #ffffff;
        font-weight: 700;
    }
    QPushButton[class="danger"] {
        background: #151f33;
        border-color: #fb5e5e;
        color: #ffd9dd;
        font-weight: 700;
    }
    QPushButton[class="danger"]:hover {
        background: rgba(239, 68, 68, 0.12);
    }
    QToolButton[class="power"] {
        min-width: 132px;
        min-height: 132px;
        max-width: 132px;
        max-height: 132px;
        border-radius: 66px;
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #7380ff, stop:0.48 #5f6cf7, stop:1 #4551cb);
        border: 2px solid #7b87ff;
        padding: 0px;
    }
    QToolButton[class="power"][state="off"] {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #324a73, stop:0.55 #283b5c, stop:1 #1d2b44);
        border: 2px solid #35517f;
    }
    QToolButton[class="power"]:hover {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8591ff, stop:0.48 #6d79ff, stop:1 #505ce0);
    }
    QToolButton[class="power"][state="off"]:hover {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3a5685, stop:0.55 #30486f, stop:1 #223451);
    }
    QLineEdit, QComboBox, QTextEdit, QTableWidget {
        background: #111a2b;
        border: 1px solid #2f4468;
        border-radius: 10px;
        padding: 6px;
        selection-background-color: #37568a;
    }
    QCheckBox {
        background: transparent;
        spacing: 8px;
        padding: 2px 0;
    }
    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        border-radius: 5px;
        border: 1px solid #4a628c;
        background: transparent;
    }
    QCheckBox::indicator:unchecked:hover {
        background: rgba(83, 108, 148, 0.18);
    }
    QCheckBox::indicator:checked {
        border: 1px solid #90a5ff;
        background: #5865f2;
        __CHECK_ICON__
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 22px;
        border: none;
        background: transparent;
    }
    QComboBox::down-arrow {
        width: 12px;
        height: 12px;
        __COMBO_ARROW__
    }
    QListWidget {
        background: #111a2b;
        border: 1px solid #2f4468;
        border-radius: 12px;
        padding: 8px;
        outline: none;
    }
    QListWidget::item {
        background: #17233a;
        border: 1px solid #2e4269;
        border-radius: 10px;
        padding: 10px;
        margin: 2px 0;
    }
    QListWidget::item:selected {
        background: #253c62;
        border: 1px solid #5f80bc;
    }
    QListWidget::item:hover {
        background: #203352;
    }
    QHeaderView::section {
        background: #1d2940;
        color: #dbe4f5;
        border: none;
        padding: 6px;
    }
    QScrollBar:vertical {
        background: transparent;
        border: none;
        width: 8px;
        margin: 4px 1px 4px 1px;
    }
    QScrollBar::groove:vertical {
        background: transparent;
        border: none;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background: rgba(91, 123, 178, 0.92);
        min-height: 34px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical:hover {
        background: rgba(116, 150, 212, 0.96);
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: transparent;
    }
    QScrollBar:horizontal {
        background: transparent;
        border: none;
        height: 8px;
        margin: 1px 4px 1px 4px;
    }
    QScrollBar::groove:horizontal {
        background: transparent;
        border: none;
        margin: 0px;
    }
    QScrollBar::handle:horizontal {
        background: rgba(91, 123, 178, 0.92);
        min-width: 34px;
        border-radius: 4px;
    }
    QScrollBar::handle:horizontal:hover {
        background: rgba(116, 150, 212, 0.96);
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0px;
    }
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
        background: transparent;
    }
    QListWidget#FilesList, QListWidget#FilesList::viewport {
        background: transparent;
        border: none;
    }
    QListWidget#FilesList {
        padding: 0px;
    }
    QListWidget#FilesList::item {
        margin: 0px 0px 8px 0px;
    }
    QListWidget#FilesList::item:selected {
        color: #d9e0f0;
    }
    QListWidget#FilesList QScrollBar:vertical,
    QTextEdit#FileEditor QScrollBar:vertical {
        background: transparent;
        border: none;
        width: 7px;
        margin: 6px 1px 6px 1px;
    }
    QListWidget#FilesList QScrollBar::handle:vertical,
    QTextEdit#FileEditor QScrollBar::handle:vertical {
        background: rgba(125, 154, 211, 0.96);
        min-height: 40px;
        border-radius: 4px;
    }
    QListWidget#FilesList QScrollBar:horizontal,
    QTextEdit#FileEditor QScrollBar:horizontal {
        background: transparent;
        border: none;
        height: 7px;
        margin: 1px 6px 1px 6px;
    }
    QListWidget#FilesList QScrollBar::handle:horizontal,
    QTextEdit#FileEditor QScrollBar::handle:horizontal {
        background: rgba(125, 154, 211, 0.96);
        min-width: 40px;
        border-radius: 4px;
    }
    QListWidget#FilesList QScrollBar::add-page:vertical,
    QListWidget#FilesList QScrollBar::sub-page:vertical,
    QTextEdit#FileEditor QScrollBar::add-page:vertical,
    QTextEdit#FileEditor QScrollBar::sub-page:vertical,
    QListWidget#FilesList QScrollBar::add-page:horizontal,
    QListWidget#FilesList QScrollBar::sub-page:horizontal,
    QTextEdit#FileEditor QScrollBar::add-page:horizontal,
    QTextEdit#FileEditor QScrollBar::sub-page:horizontal {
        background: transparent;
    }
    QListWidget#FilesList QScrollBar::groove:vertical,
    QListWidget#FilesList QScrollBar::groove:horizontal,
    QTextEdit#FileEditor QScrollBar::groove:vertical,
    QTextEdit#FileEditor QScrollBar::groove:horizontal,
    QAbstractScrollArea::corner {
        background: transparent;
        border: none;
    }
    QMenu {
        background: #141f32;
        border: 1px solid #304463;
        border-radius: 8px;
        padding: 6px;
    }
    QMenu::item {
        padding: 7px 10px;
        border-radius: 6px;
    }
    QMenu::item:selected {
        background: #2b3f63;
    }
    """

    light = """
    QWidget {
        background: #eef2f8;
        color: #1f2a3d;
        font-family: "Segoe UI";
        font-size: 10pt;
    }
    #WindowShell {
        background: transparent;
    }
    QStackedWidget, QStackedWidget > QWidget {
        background: transparent;
    }
    QWidget[class="pageRoot"], QWidget[class="pageCanvas"] {
        background: transparent;
    }
    QLabel {
        background: transparent;
    }
    #RootFrame {
        background: #f3f6fd;
        border: 1px solid #d2ddeb;
        border-radius: 16px;
    }
    #TitleBar {
        background: #f3f6fd;
        border: none;
        border-top-left-radius: 16px;
        border-top-right-radius: 16px;
    }
    #Sidebar {
        background: #f3f6fd;
        border-bottom-left-radius: 16px;
    }
    #Content {
        background: transparent;
        border: none;
    }
    #ContentSurface {
        background: qlineargradient(x1:0, y1:1, x2:1, y2:0, stop:0 #e8eef9, stop:0.66 #f2f6fd, stop:1 #f8fbff);
        border-top: 1px solid #d2ddeb;
        border-left: 1px solid #d2ddeb;
        border-top-left-radius: 18px;
        border-top-right-radius: 0px;
        border-bottom-left-radius: 0px;
        border-bottom-right-radius: 16px;
    }
    QDialog#AppDialogWindow {
        background: transparent;
        border: none;
    }
    #DialogRoot {
        background: #ffffff;
        border: 1px solid #d2ddeb;
        border-radius: 12px;
    }
    #DialogTitleBar {
        background: transparent;
        border: none;
        border-top-left-radius: 12px;
        border-top-right-radius: 12px;
    }
    #DialogBody {
        background: transparent;
    }
    #LoadingOverlay {
        background: rgba(228, 236, 248, 0.58);
    }
    #LoadingCard {
        background: #ffffff;
        border: 1px solid #d2ddeb;
        border-radius: 16px;
    }
    QFrame[class="card"] {
        background: qlineargradient(x1:0, y1:1, x2:1, y2:0, stop:0 #f3f7ff, stop:0.68 #fbfdff, stop:1 #ffffff);
        border: 1px solid #d2ddeb;
        border-radius: 16px;
    }
    QFrame[class="modHero"] {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ffffff, stop:1 #eef4ff);
        border: 1px solid #cad7ea;
        border-radius: 16px;
    }
    QFrame[class="modCard"] {
        background: #ffffff;
        border: 1px solid #d6e1f0;
        border-radius: 16px;
    }
    QFrame[class="modIconWrap"] {
        background: #edf3ff;
        border: 1px solid #c5d6ee;
        border-radius: 16px;
    }
    QLabel[class="title"] {
        font-size: 13pt;
        font-weight: 700;
        color: #111827;
    }
    #DashboardTitle {
        padding: 0px;
        margin: 0px;
    }
    #DashboardPowerBlock {
        background: transparent;
    }
    QLabel[class="muted"] {
        color: #64748b;
    }
    QLabel[class="modHint"] {
        color: #61708c;
    }
    QLabel[class="modState"] {
        color: #24324a;
        background: #edf3ff;
        border: 1px solid #cadaf2;
        border-radius: 12px;
        padding: 6px 12px;
        font-weight: 600;
    }
    QLabel[class="modState"][state="enabled"] {
        background: #e8f8ef;
        border: 1px solid #9ed1b3;
        color: #1f6b45;
    }
    QLabel[class="modState"][state="installed"] {
        background: #edf3ff;
        border: 1px solid #bfd2f0;
        color: #2d4b7b;
    }
    QLabel[class="modState"][state="not installed"] {
        background: #f6f8fc;
        border: 1px solid #d8e0eb;
        color: #66758d;
    }
    QLabel[class="modMeta"] {
        color: #5f708d;
        background: #f5f8ff;
        border: 1px solid #d4dff0;
        border-radius: 12px;
        padding: 6px 12px;
    }
    #ModsSummaryChip, #ModsEnabledChip {
        border-radius: 11px;
    }
    #ModStateBadge, #ModMetaChip {
        border-radius: 12px;
    }
    QLabel[class="modBody"] {
        color: #2a3648;
        line-height: 1.3em;
    }
    #ModsScroll, #ModsCanvas {
        background: transparent;
        border: none;
    }
    QToolButton[class="nav"] {
        min-width: 44px;
        min-height: 44px;
        max-width: 44px;
        max-height: 44px;
        border-radius: 12px;
        border: 1px solid transparent;
        background: transparent;
    }
    QToolButton[class="nav"]:hover {
        background: #e7efff;
        border: 1px solid #bfd2f0;
    }
    QToolButton[class="nav"]:checked {
        background: #dae7ff;
        border: 1px solid #9cb7ea;
    }
    QToolButton[class="window"] {
        min-width: 26px;
        min-height: 26px;
        max-width: 26px;
        max-height: 26px;
        border-radius: 12px;
        border: none;
        background: transparent;
        padding: 0px;
        margin: 0px;
    }
    QToolButton[class="window"][role="min"],
    QToolButton[class="window"][role="close"] {
        padding: 0px 1px 2px 0px;
    }
    QToolButton[class="window"][role="close"] {
        padding: 0px 1px 1px 0px;
    }
    QToolButton[class="window"]:hover {
        background: rgba(148, 170, 205, 0.35);
    }
    QToolButton[class="window"][role="close"]:hover {
        background: rgba(189, 99, 109, 0.62);
    }
    QPushButton {
        background: #edf3ff;
        border: 1px solid #bfd2f0;
        border-radius: 10px;
        padding: 8px 12px;
    }
    QPushButton:hover {
        background: #e1ebff;
    }
    QToolButton[class="action"] {
        min-width: 26px;
        min-height: 26px;
        max-width: 26px;
        max-height: 26px;
        border: none;
        border-radius: 12px;
        background: transparent;
        padding: 0;
        margin: 0;
    }
    QToolButton[class="action"]:hover {
        background: rgba(148, 170, 205, 0.35);
    }
    QToolButton[class="action"]::menu-indicator {
        image: none;
        width: 0px;
        height: 0px;
    }
    QFrame[class="fileModeCard"] {
        background: qlineargradient(x1:0, y1:1, x2:1, y2:0, stop:0 #f3f7ff, stop:1 #ffffff);
        border: 1px solid #cad8ee;
        border-radius: 14px;
    }
    QFrame[class="fileModeCard"][hovered="true"] {
        background: qlineargradient(x1:0, y1:1, x2:1, y2:0, stop:0 #e8f0ff, stop:1 #ffffff);
        border: 1px solid #8ea9df;
    }
    QPushButton[class="primary"] {
        background: #5865f2;
        border-color: #6773ff;
        color: #ffffff;
        font-weight: 700;
    }
    QPushButton[class="danger"] {
        background: #ffffff;
        border-color: #fb5e5e;
        color: #bc4357;
        font-weight: 700;
    }
    QPushButton[class="danger"]:hover {
        background: rgba(239, 68, 68, 0.08);
    }
    QToolButton[class="power"] {
        min-width: 132px;
        min-height: 132px;
        max-width: 132px;
        max-height: 132px;
        border-radius: 66px;
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #7b86ff, stop:0.48 #6471f8, stop:1 #4c58d8);
        border: 2px solid #7b87ff;
        padding: 0px;
    }
    QToolButton[class="power"][state="off"] {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f5f8ff, stop:0.55 #e8f0ff, stop:1 #dce6fb);
        border: 2px solid #bfd2f0;
    }
    QToolButton[class="power"]:hover {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8a95ff, stop:0.48 #717cff, stop:1 #5863ea);
    }
    QToolButton[class="power"][state="off"]:hover {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:0.55 #eef4ff, stop:1 #e2ebff);
    }
    QLineEdit, QComboBox, QTextEdit, QTableWidget {
        background: #ffffff;
        border: 1px solid #cedbea;
        border-radius: 10px;
        padding: 6px;
        selection-background-color: #bfd2f0;
    }
    QCheckBox {
        background: transparent;
        spacing: 8px;
        padding: 2px 0;
    }
    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        border-radius: 5px;
        border: 1px solid #9bb1d2;
        background: #ffffff;
    }
    QCheckBox::indicator:unchecked:hover {
        background: #eef4ff;
    }
    QCheckBox::indicator:checked {
        border: 1px solid #7f96db;
        background: #5865f2;
        __CHECK_ICON__
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 22px;
        border: none;
        background: transparent;
    }
    QComboBox::down-arrow {
        width: 12px;
        height: 12px;
        __COMBO_ARROW__
    }
    QListWidget {
        background: #ffffff;
        border: 1px solid #cedbea;
        border-radius: 12px;
        padding: 8px;
        outline: none;
    }
    QListWidget::item {
        background: #f8fbff;
        border: 1px solid #d3e0ef;
        border-radius: 10px;
        padding: 10px;
        margin: 2px 0;
    }
    QListWidget::item:selected {
        background: #deebff;
        border: 1px solid #9cb7ea;
    }
    QListWidget::item:hover {
        background: #edf4ff;
    }
    QHeaderView::section {
        background: #edf3ff;
        color: #1f2a3d;
        border: none;
        padding: 6px;
    }
    QScrollBar:vertical {
        background: transparent;
        border: none;
        width: 8px;
        margin: 4px 1px 4px 1px;
    }
    QScrollBar::groove:vertical {
        background: transparent;
        border: none;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background: rgba(122, 150, 196, 0.96);
        min-height: 34px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical:hover {
        background: rgba(104, 134, 184, 0.96);
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: transparent;
    }
    QScrollBar:horizontal {
        background: transparent;
        border: none;
        height: 8px;
        margin: 1px 4px 1px 4px;
    }
    QScrollBar::groove:horizontal {
        background: transparent;
        border: none;
        margin: 0px;
    }
    QScrollBar::handle:horizontal {
        background: rgba(122, 150, 196, 0.96);
        min-width: 34px;
        border-radius: 4px;
    }
    QScrollBar::handle:horizontal:hover {
        background: rgba(104, 134, 184, 0.96);
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0px;
    }
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
        background: transparent;
    }
    QListWidget#FilesList, QListWidget#FilesList::viewport {
        background: transparent;
        border: none;
    }
    QListWidget#FilesList {
        padding: 0px;
    }
    QListWidget#FilesList::item {
        margin: 0px 0px 8px 0px;
    }
    QListWidget#FilesList::item:selected {
        color: #1f2a3d;
    }
    QListWidget#FilesList QScrollBar:vertical,
    QTextEdit#FileEditor QScrollBar:vertical {
        background: transparent;
        border: none;
        width: 7px;
        margin: 6px 1px 6px 1px;
    }
    QListWidget#FilesList QScrollBar::handle:vertical,
    QTextEdit#FileEditor QScrollBar::handle:vertical {
        background: rgba(122, 150, 196, 0.96);
        min-height: 40px;
        border-radius: 4px;
    }
    QListWidget#FilesList QScrollBar:horizontal,
    QTextEdit#FileEditor QScrollBar:horizontal {
        background: transparent;
        border: none;
        height: 7px;
        margin: 1px 6px 1px 6px;
    }
    QListWidget#FilesList QScrollBar::handle:horizontal,
    QTextEdit#FileEditor QScrollBar::handle:horizontal {
        background: rgba(122, 150, 196, 0.96);
        min-width: 40px;
        border-radius: 4px;
    }
    QListWidget#FilesList QScrollBar::add-page:vertical,
    QListWidget#FilesList QScrollBar::sub-page:vertical,
    QTextEdit#FileEditor QScrollBar::add-page:vertical,
    QTextEdit#FileEditor QScrollBar::sub-page:vertical,
    QListWidget#FilesList QScrollBar::add-page:horizontal,
    QListWidget#FilesList QScrollBar::sub-page:horizontal,
    QTextEdit#FileEditor QScrollBar::add-page:horizontal,
    QTextEdit#FileEditor QScrollBar::sub-page:horizontal {
        background: transparent;
    }
    QListWidget#FilesList QScrollBar::groove:vertical,
    QListWidget#FilesList QScrollBar::groove:horizontal,
    QTextEdit#FileEditor QScrollBar::groove:vertical,
    QTextEdit#FileEditor QScrollBar::groove:horizontal,
    QAbstractScrollArea::corner {
        background: transparent;
        border: none;
    }
    QMenu {
        background: #ffffff;
        border: 1px solid #c9d7eb;
        border-radius: 8px;
        padding: 6px;
    }
    QMenu::item {
        padding: 7px 10px;
        border-radius: 6px;
    }
    QMenu::item:selected {
        background: #e7efff;
    }
    """

    arrow_rule = "image: none;"
    if chevron_icon:
        normalized_icon = chevron_icon.replace("\\", "/")
        arrow_rule = f'image: url("{normalized_icon}");'
    check_rule = "image: none;"
    if check_icon:
        normalized_check = check_icon.replace("\\", "/")
        check_rule = f'image: url("{normalized_check}");'
    style = dark if theme == "dark" else light
    style = style.replace("__COMBO_ARROW__", arrow_rule)
    return style.replace("__CHECK_ICON__", check_rule)
