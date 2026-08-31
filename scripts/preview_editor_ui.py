import os
import sys
import traceback
import subprocess

# 確保輸出編碼為 UTF-8
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# 全域異常捕捉
def global_exception_handler(exc_type, exc_value, exc_traceback):
    err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print(f"\n[CRITICAL ERROR] 發生未捕獲異常:\n{err_msg}", file=sys.stderr)
    try:
        with open("preview_error.log", "w", encoding="utf-8") as f:
            f.write(err_msg)
    except Exception:
        pass
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = global_exception_handler

# 自動檢查並安裝 PySide6 依賴
try:
    import PySide6
except ImportError:
    print("[INFO] 正在安裝 PySide6 依賴...")
    subprocess.run([sys.executable, "-m", "pip", "install", "PySide6"])

from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QFont, QTextCursor, QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLabel, QLineEdit,
    QPlainTextEdit, QPushButton, QFrame, QSplitter,
    QStatusBar, QMessageBox
)

PREVIEW_QSS = """
QMainWindow, QWidget {
    background-color: #141418;
    color: #e2e2e9;
    font-family: 'Segoe UI', 'Microsoft JhengHei', 'PingFang TC', sans-serif;
    font-size: 13px;
}

/* 頂部導覽列與面板外框 */
QFrame#headerFrame {
    background-color: #1c1c24;
    border-bottom: 1px solid #2b2b38;
    padding: 8px 16px;
}

QFrame#sidebarFrame {
    background-color: #1a1a22;
    border-right: 1px solid #282834;
}

QFrame#editorContainer {
    background-color: #16161c;
}

/* 搜尋框與輸入元件 */
QLineEdit#searchBox {
    background-color: #23232e;
    border: 1px solid #323242;
    border-radius: 6px;
    padding: 7px 12px;
    color: #f0f0f5;
    font-size: 13px;
    selection-background-color: #e5a93b;
    selection-color: #141418;
}
QLineEdit#searchBox:focus {
    border: 1px solid #e5a93b;
    background-color: #272733;
}

/* 左側檔案清單 */
QListWidget#fileList {
    background-color: transparent;
    border: none;
    padding: 6px;
    outline: none;
}
QListWidget#fileList::item {
    background-color: #20202a;
    border: 1px solid #2b2b38;
    border-radius: 6px;
    margin-bottom: 6px;
    padding: 10px 12px;
    color: #c5c5d2;
}
QListWidget#fileList::item:hover {
    background-color: #282836;
    border: 1px solid #3d3d50;
    color: #ffffff;
}
QListWidget#fileList::item:selected {
    background-color: #2f2a24;
    border: 1px solid #e5a93b;
    color: #f7d28b;
    font-weight: bold;
}

/* 分割條樣式 */
QSplitter::handle {
    background-color: #262633;
    width: 3px;
}
QSplitter::handle:hover {
    background-color: #e5a93b;
}

/* 核心純文字編輯框（高質感稿紙風格） */
QPlainTextEdit#editorArea {
    background-color: #17171d;
    border: none;
    border-radius: 8px;
    padding: 24px 32px;
    color: #e6e6ee;
    font-family: 'Segoe UI', 'Microsoft JhengHei', 'PingFang TC', sans-serif;
    font-size: 15px;
    line-height: 1.6;
    selection-background-color: #4a3a20;
    selection-color: #ffd980;
}
QPlainTextEdit#editorArea:focus {
    background-color: #191921;
}

/* 按鈕美學 */
QPushButton {
    background-color: #262634;
    border: 1px solid #36364a;
    border-radius: 6px;
    padding: 6px 14px;
    color: #dedee8;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #333346;
    border: 1px solid #4a4a66;
    color: #ffffff;
}
QPushButton#primaryBtn {
    background-color: #e5a93b;
    border: 1px solid #f0b74d;
    color: #141418;
    font-weight: bold;
}
QPushButton#primaryBtn:hover {
    background-color: #f5b94c;
    border: 1px solid #ffd478;
}

/* 滾動條極簡微化 */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 6px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #333344;
    min-height: 30px;
    border-radius: 3px;
}
QScrollBar::handle:vertical:hover {
    background: #4a4a60;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* 狀態列 */
QStatusBar {
    background-color: #16161e;
    border-top: 1px solid #242430;
    color: #8c8c9e;
    font-size: 12px;
    padding: 4px 12px;
}
"""

SAMPLE_FILES = {
    "【人物誌】唐門少主設定.md": """# 唐門少主 - 人物設定誌

### 基礎設定
- **本名**：唐凌霄
- **身分**：蜀中唐門嫡系少主、玄機閣當代執筆人
- **性格特質**：沉著內斂、心思縝密，行事如落子弈棋，不輕易顯露鋒芒。

---

### 隨身器具
1. **千機流光扇**：以精鋼為骨，綴以玄鐵暗刺，合則如點穴玉筆，展則化護身圓盾。
2. **沉水墨玉佩**：傳承自昔年門主，溫潤如玉，隱含辨毒微光。

---

### 經典行事原則
> 「風起於青萍之末，刃隱於袖裡之息。凡入局者，當自知退路。」
""",
    "【世界觀】巴蜀地理與宗門局勢.md": """# 巴蜀地理與宗門勢力劃分

### 險川要隘
蜀道連綿千仞，懸崖疊嶂，自古有「一夫當關、萬夫莫開」之勢。

- **問劍峰**：終年雲霧繚繞，唯有一條石棧梯可登絕頂。
- **碧水潭**：暗流匯聚之淵，水寒徹骨，深不可測。

---

### 門派共存態勢
巴蜀各大宗門表面井水不犯河水，然暗流湧動：
1. **唐門**：鎮守西蜀重鎮，長於機關術與醫道暗技。
2. **青城派**：道門玄宗，劍勢講求行雲流水。
""",
    "【章節草稿】第一回：霧鎖翠微亭.md": """# 第一回：霧鎖翠微亭

暮色四合，微雨初歇。

翠微亭外的石階上落滿了濕漉漉的竹葉。風穿過空蕩的竹林，唯聞遠處一聲低沉的清越鐘鳴。

青年立於亭簷之下，身著一襲深玄色暗紋錦袍，袖口處微露半截寒芒。他緩緩抬手，指尖微動，一片沾著殘雨的青葉便在掌心悄然翻轉。

「既然來了，何必隱於林後？」

話音未落，三丈開外的竹梢微微一晃，數道黑影已然悄無聲息地落於四周泥石之上。
"""
}

class PreviewEditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("【預覽模式】唐門山莊 - 高質感並排純文字編輯器")
        self.resize(1180, 760)
        self.setStyleSheet(PREVIEW_QSS)
        
        self.current_filename = None
        self.init_ui()
        self.load_sample_data()
        
    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 頂部狀態標題列 (緊湊極簡，高度固定 42px)
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_frame.setFixedHeight(42)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 0, 16, 0)
        
        app_title = QLabel("❖ 唐門文字工坊")
        app_title.setFont(QFont("Microsoft JhengHei", 11, QFont.Bold))
        app_title.setStyleSheet("color: #e5a93b;")
        header_layout.addWidget(app_title)
        
        header_layout.addStretch()
        
        self.btn_toggle_sidebar = QPushButton("📁 收合側欄 (Ctrl+B)")
        self.btn_toggle_sidebar.clicked.connect(self.toggle_sidebar)
        header_layout.addWidget(self.btn_toggle_sidebar)
        
        main_layout.addWidget(header_frame)
        
        # 中央 QSplitter 並排佈局 (佔據所有垂直剩餘空間)
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        
        # 左側檔案樹導覽欄
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("sidebarFrame")
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(12, 12, 12, 12)
        sidebar_layout.setSpacing(8)
        
        sidebar_title = QLabel("章節與設定檔案")
        sidebar_title.setStyleSheet("color: #9292a4; font-weight: bold; font-size: 11px; text-transform: uppercase;")
        sidebar_layout.addWidget(sidebar_title)
        
        self.search_box = QLineEdit()
        self.search_box.setObjectName("searchBox")
        self.search_box.setPlaceholderText("🔍 搜尋檔案...")
        self.search_box.textChanged.connect(self.filter_files)
        sidebar_layout.addWidget(self.search_box)
        
        self.file_list = QListWidget()
        self.file_list.setObjectName("fileList")
        self.file_list.currentItemChanged.connect(self.on_file_selected)
        sidebar_layout.addWidget(self.file_list)
        
        sidebar_frame.setMinimumWidth(180)
        sidebar_frame.setMaximumWidth(280)
        self.splitter.addWidget(sidebar_frame)
        self.sidebar_widget = sidebar_frame
        
        # 右側專注純文字編輯區 (核心視覺焦點)
        editor_frame = QFrame()
        editor_frame.setObjectName("editorContainer")
        editor_layout = QVBoxLayout(editor_frame)
        editor_layout.setContentsMargins(24, 16, 24, 16)
        editor_layout.setSpacing(10)
        
        # 編輯器頂部資訊列
        editor_top_bar = QHBoxLayout()
        self.lbl_current_file = QLabel("請由左側點選檔案以開啟編輯")
        self.lbl_current_file.setFont(QFont("Microsoft JhengHei", 12, QFont.Bold))
        self.lbl_current_file.setStyleSheet("color: #ffffff;")
        editor_top_bar.addWidget(self.lbl_current_file)
        
        editor_top_bar.addStretch()
        
        self.lbl_save_status = QLabel("● 唯讀預覽模式")
        self.lbl_save_status.setStyleSheet("color: #6edb8f; font-size: 12px; margin-right: 8px;")
        editor_top_bar.addWidget(self.lbl_save_status)
        
        self.btn_save = QPushButton("儲存變更 (Ctrl+S)")
        self.btn_save.setObjectName("primaryBtn")
        self.btn_save.clicked.connect(self.simulate_save)
        editor_top_bar.addWidget(self.btn_save)
        
        editor_layout.addLayout(editor_top_bar)
        
        # 純文字編輯區塊 (佔據最大高度與寬度)
        self.editor = QPlainTextEdit()
        self.editor.setObjectName("editorArea")
        self.editor.textChanged.connect(self.on_text_changed)
        self.editor.cursorPositionChanged.connect(self.update_cursor_status)
        editor_layout.addWidget(self.editor, 1)
        
        editor_frame.setMinimumWidth(500)
        self.splitter.addWidget(editor_frame)
        
        # 設定分割比例 (220px : 960px，預設聚焦於右側稿紙)
        self.splitter.setSizes([220, 960])
        main_layout.addWidget(self.splitter, 1)
        
        # 底部狀態列
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.lbl_char_count = QLabel("字數: 0 字")
        self.lbl_para_count = QLabel("段落: 0")
        self.lbl_cursor_pos = QLabel("行 1, 欄 1")
        self.lbl_encoding = QLabel("UTF-8 (繁體)")
        
        self.status_bar.addPermanentWidget(self.lbl_char_count)
        self.status_bar.addPermanentWidget(QLabel(" | "))
        self.status_bar.addPermanentWidget(self.lbl_para_count)
        self.status_bar.addPermanentWidget(QLabel(" | "))
        self.status_bar.addPermanentWidget(self.lbl_cursor_pos)
        self.status_bar.addPermanentWidget(QLabel(" | "))
        self.status_bar.addPermanentWidget(self.lbl_encoding)
        self.status_bar.showMessage("提示：點擊左側檔案立即在右側展開並排編輯。支援 Ctrl+S 儲存、Ctrl+B 收合側欄。")
        
        # 快捷鍵綁定
        QShortcut(QKeySequence("Ctrl+S"), self, self.simulate_save)
        QShortcut(QKeySequence("Ctrl+B"), self, self.toggle_sidebar)
        
        self.setCentralWidget(main_widget)
        
    def load_sample_data(self):
        self.file_list.clear()
        for filename in SAMPLE_FILES.keys():
            item = QListWidgetItem(f"📄  {filename}")
            item.setData(Qt.UserRole, filename)
            self.file_list.addItem(item)
            
        if self.file_list.count() > 0:
            self.file_list.setCurrentRow(0)
            
    def on_file_selected(self, current, previous):
        if not current:
            return
        filename = current.data(Qt.UserRole)
        self.current_filename = filename
        self.lbl_current_file.setText(f"📄  {filename}")
        
        content = SAMPLE_FILES.get(filename, "")
        self.editor.blockSignals(True)
        self.editor.setPlainText(content)
        self.editor.blockSignals(False)
        
        self.lbl_save_status.setText("● 已同步最新內容")
        self.lbl_save_status.setStyleSheet("color: #6edb8f; font-size: 12px; margin-right: 8px;")
        self.update_statistics()
        
    def on_text_changed(self):
        self.lbl_save_status.setText("● 編輯中 (未儲存)")
        self.lbl_save_status.setStyleSheet("color: #e5a93b; font-size: 12px; margin-right: 8px;")
        self.update_statistics()
        
    def update_statistics(self):
        text = self.editor.toPlainText()
        char_count = len(text.replace(" ", "").replace("\\n", "").replace("\\r", ""))
        lines = text.splitlines()
        para_count = len([line for line in lines if line.strip()])
        
        self.lbl_char_count.setText(f"字數: {char_count} 字")
        self.lbl_para_count.setText(f"段落: {para_count}")
        
    def update_cursor_status(self):
        cursor = self.editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        self.lbl_cursor_pos.setText(f"行 {line}, 欄 {col}")
        
    def simulate_save(self):
        if not self.current_filename:
            return
        # 沙盒模擬儲存至記憶體
        SAMPLE_FILES[self.current_filename] = self.editor.toPlainText()
        self.lbl_save_status.setText("✓ 已儲存 (沙盒預覽)")
        self.lbl_save_status.setStyleSheet("color: #6edb8f; font-size: 12px; margin-right: 8px;")
        self.status_bar.showMessage(f"【沙盒提示】檔案 [{self.current_filename}] 內容已成功儲存至預覽緩衝區！", 4000)
        
    def toggle_sidebar(self):
        if not self.sidebar_widget.isHidden():
            self.sidebar_widget.hide()
            self.btn_toggle_sidebar.setText("📁 展開側欄 (Ctrl+B)")
        else:
            self.sidebar_widget.show()
            self.btn_toggle_sidebar.setText("📁 收合側欄 (Ctrl+B)")
            
    def filter_files(self, text):
        keyword = text.strip().lower()
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            filename = item.data(Qt.UserRole).lower()
            item.setHidden(keyword not in filename)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PreviewEditorWindow()
    window.show()
    sys.exit(app.exec())
