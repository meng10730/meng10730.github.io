import os
import sys
import json
import html
import subprocess

# 自動在啟動時安裝 PySide6 依賴
try:
    import PySide6
except ImportError:
    print("[INFO] PySide6 not found. Installing via pip...")
    subprocess.run([sys.executable, "-m", "pip", "install", "PySide6"])

import datetime
from PySide6.QtCore import Qt, QProcess, QSize, QUrl
from PySide6.QtGui import QIcon, QDesktopServices, QFont, QTextCursor, QColor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLabel, QComboBox, QLineEdit,
    QPlainTextEdit, QPushButton, QScrollArea, QFileDialog, QMessageBox,
    QDateEdit, QDialog, QInputDialog, QFrame, QSplitter,
    QProgressBar, QSystemTrayIcon, QStyle
)

# 視窗精美深色樣式表
QSS_STYLE = """
QWidget {
    background-color: #1a1a20;
    color: #e2e2e9;
    font-family: 'Segoe UI', 'Microsoft JhengHei', sans-serif;
    font-size: 13px;
}

QScrollBar:vertical {
    border: none;
    background: #1a1a20;
    width: 6px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #3a3a46;
    min-height: 20px;
    border-radius: 3px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QListWidget {
    background-color: #22222b;
    border: 1px solid #2e2e3a;
    border-radius: 6px;
    padding: 5px;
}
QListWidget::item {
    padding: 10px;
    border-bottom: 1px solid #2d2d38;
}
QListWidget::item:hover {
    background-color: #2d2d3a;
    border-radius: 4px;
}
QListWidget::item:selected {
    background-color: #e5a93b;
    color: #1a1a20;
    font-weight: bold;
    border-radius: 4px;
}

QLineEdit, QTextEdit, QPlainTextEdit, QDateEdit, QComboBox {
    background-color: #22222b;
    border: 1px solid #2e2e3a;
    border-radius: 5px;
    padding: 6px;
    color: #e2e2e9;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QDateEdit:focus {
    border: 1px solid #e5a93b;
}

QPushButton {
    background-color: #2d2d3a;
    border: 1px solid #3a3a4c;
    border-radius: 5px;
    padding: 8px 16px;
    color: #e2e2e9;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #3a3a4c;
}
QPushButton:pressed {
    background-color: #1f1f2a;
}

QPushButton#primaryButton {
    background-color: #e5a93b;
    border: 1px solid #c9932d;
    color: #1a1a20;
}
QPushButton#primaryButton:hover {
    background-color: #f5b94b;
}
QPushButton#primaryButton:pressed {
    background-color: #c9932d;
}

QPushButton#dangerButton {
    background-color: #8c2a2a;
    border: 1px solid #732222;
    color: #ffffff;
}
QPushButton#dangerButton:hover {
    background-color: #a43333;
}
QPushButton#dangerButton:pressed {
    background-color: #732222;
}

QFrame#cardFrame {
    background-color: #22222b;
    border: 1px solid #2e2e3a;
    border-radius: 6px;
}
"""

class ArrayFieldWidget(QWidget):
    """用於 Array 欄位的動態增加/刪除項目介面"""
    def __init__(self, label, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)
        
        self.header_layout = QHBoxLayout()
        self.label_widget = QLabel(label)
        self.label_widget.setStyleSheet("color: #a2a2ab; font-weight: bold;")
        self.add_btn = QPushButton("+ 增加項目")
        self.add_btn.setFixedWidth(100)
        self.add_btn.setStyleSheet("font-size: 11px; padding: 4px;")
        self.add_btn.clicked.connect(self.add_item)
        
        self.header_layout.addWidget(self.label_widget)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.add_btn)
        self.layout.addLayout(self.header_layout)
        
        self.items_layout = QVBoxLayout()
        self.items_layout.setSpacing(5)
        self.layout.addLayout(self.items_layout)
        
        self.inputs = []

    def add_item(self, text=""):
        item_widget = QWidget()
        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(0, 0, 0, 0)
        item_layout.setSpacing(5)
        
        line_edit = QLineEdit(text)
        del_btn = QPushButton("✕")
        del_btn.setFixedWidth(30)
        del_btn.setStyleSheet("background-color: #4a2d2d; color: #ff9999; border: none; padding: 6px;")
        
        item_layout.addWidget(line_edit)
        item_layout.addWidget(del_btn)
        self.items_layout.addWidget(item_widget)
        
        self.inputs.append((item_widget, line_edit))
        
        del_btn.clicked.connect(lambda: self.remove_item(item_widget))

    def remove_item(self, widget):
        for idx, (w, edit) in enumerate(self.inputs):
            if w == widget:
                self.inputs.pop(idx)
                widget.deleteLater()
                break

    def get_values(self):
        vals = []
        for w, edit in self.inputs:
            text = edit.text().strip()
            if text:
                vals.append(text)
        return vals

    def clear(self):
        for w, edit in self.inputs:
            w.deleteLater()
        self.inputs.clear()

    def set_values(self, values):
        self.clear()
        if not values:
            return
        if isinstance(values, list):
            for v in values:
                self.add_item(str(v))
        elif isinstance(values, str):
            for v in values.split(","):
                if v.strip():
                    self.add_item(v.strip())


class PublishDialog(QDialog):
    """發布確認對話框：顯示即將變更的檔案清單與輸入 Commit Message"""
    def __init__(self, changed_files, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🚀 確認發布上線")
        self.setFixedSize(500, 400)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        title = QLabel("準備發布網站上線")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(title)
        
        # 變更檔案清單
        layout.addWidget(QLabel("即將提交的變更檔案清單:"))
        self.file_list = QPlainTextEdit()
        self.file_list.setReadOnly(True)
        self.file_list.setPlainText("\n".join(changed_files) if changed_files else "（無偵測到檔案變更）")
        self.file_list.setStyleSheet("background-color: #15151c; font-family: Consolas; color: #a2a2ab;")
        layout.addWidget(self.file_list)
        
        # Commit Message
        layout.addWidget(QLabel("填寫本次提交訊息 (Commit Message):"))
        self.msg_edit = QLineEdit()
        import datetime
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        self.msg_edit.setText(f"更新山莊網站條目 {today_str}")
        layout.addWidget(self.msg_edit)
        
        # 按鈕
        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        self.ok_btn = QPushButton("確認並開始發布")
        self.ok_btn.setObjectName("primaryButton")
        self.ok_btn.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.ok_btn)
        layout.addLayout(btn_layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("唐門山莊綜合管理控制台")
        self.setMinimumSize(1100, 750)
        
        self.project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.workspace_dir = "C:\\workspace\\長生劫_小說工作區"
        self.schema = {}
        self.astro_process = None
        self.npm_install_process = None
        self.active_processes = []
        self.current_astro_port = 4321
        self.browser_opened = False
        self.auto_open_keystatic_after_start = False
        self.is_busy = False
        
        # 初始化 Windows 系統桌面通知托盤
        self.tray_icon = QSystemTrayIcon(self)
        try:
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
            self.tray_icon.show()
        except Exception:
            pass

        self.load_config()
        self.load_schema()
        self.setup_ui()
        self.refresh_file_list()
        
        # 啟動時自動檢查並建立桌面捷徑
        self.create_desktop_shortcut()
        
        # 啟動時自動與遠端同步，拉取線上最新變更 (新增/刪除/修改)
        self.auto_sync_on_startup()

    def auto_sync_on_startup(self):
        self.log("⌛ [啟動同步] 正在檢查並拉取線上（遠端）的更新...")
        
        def on_sync_success():
            self.log("✓ [啟動同步] 成功與線上同步，已自動載入並更新文章清單！")
            self.refresh_file_list()
            
        def on_sync_error():
            self.log("⚠️ [啟動同步] 線上同步失敗或無網路，請檢查連線，或手動點選「同步線上編輯」按鈕。")
            
        self.run_git_process(
            ["pull", "--rebase"],
            on_success=on_sync_success,
            on_error=on_sync_error
        )

    def load_config(self):
        config_path = os.path.join(self.project_dir, "sync-config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    self.workspace_dir = cfg.get("workspacePath", self.workspace_dir)
            except Exception as e:
                self.log(f"⚠️ 載入設定檔失敗: {e}")

    def load_schema(self):
        schema_path = os.path.join(self.project_dir, "scripts", "schema.json")
        if os.path.exists(schema_path):
            try:
                with open(schema_path, "r", encoding="utf-8") as f:
                    self.schema = json.load(f)
            except Exception as e:
                self.log(f"⚠️ 載入 Schema 失敗: {e}")

    def setup_ui(self):
        # 設定主樣式表
        self.setStyleSheet(QSS_STYLE)
        
        # 主佈局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 1. 左側控制與導覽面板 (Sidebar)
        sidebar = QFrame()
        sidebar.setObjectName("cardFrame")
        sidebar.setFixedWidth(230)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(15, 20, 15, 20)
        sidebar_layout.setSpacing(15)
        
        shanzhuang_title = QLabel("唐門山莊")
        shanzhuang_title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        shanzhuang_title.setStyleSheet("color: #e5a93b;")
        shanzhuang_title.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(shanzhuang_title)
        
        sidebar_layout.addWidget(QLabel("── 測試與編輯 ──"))
        
        self.test_server_btn = QPushButton("🧪 啟動本地測試")
        self.test_server_btn.clicked.connect(self.toggle_test_server)
        sidebar_layout.addWidget(self.test_server_btn)
        
        self.open_cms_btn = QPushButton("📝 開啟後台編輯")
        self.open_cms_btn.clicked.connect(self.open_keystatic_cms)
        sidebar_layout.addWidget(self.open_cms_btn)
        
        self.open_mover_btn = QPushButton("🚚 開啟藏書移置閣")
        self.open_mover_btn.clicked.connect(self.open_articles_mover)
        sidebar_layout.addWidget(self.open_mover_btn)
        
        sidebar_layout.addWidget(QLabel("── 同步與發布 ──"))
        
        self.sync_btn = QPushButton("🔄 同步線上編輯")
        self.sync_btn.clicked.connect(self.sync_online_edit)
        sidebar_layout.addWidget(self.sync_btn)
        
        self.publish_btn = QPushButton("🚀 一鍵發布上線")
        self.publish_btn.setObjectName("primaryButton")
        self.publish_btn.clicked.connect(self.confirm_publish)
        sidebar_layout.addWidget(self.publish_btn)

        # 於主發布按鈕正下方建立進度條
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #3a3a4c;
                border-radius: 4px;
                background-color: #121216;
                text-align: center;
                color: #ffffff;
                font-weight: bold;
                font-size: 11px;
                height: 18px;
            }
            QProgressBar::chunk {
                background-color: #e5a93b;
                border-radius: 3px;
            }
        """)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        sidebar_layout.addWidget(self.progress_bar)
        
        sidebar_layout.addWidget(QLabel("── 進階網頁維護 ──"))
        
        self.fix_env_btn = QPushButton("⚙️ 還原開發環境")
        self.fix_env_btn.clicked.connect(self.fix_dev_env)
        sidebar_layout.addWidget(self.fix_env_btn)
        
        self.restore_backup_btn = QPushButton("📦 還原歷史備份")
        self.restore_backup_btn.clicked.connect(self.restore_backup)
        sidebar_layout.addWidget(self.restore_backup_btn)
        
        sidebar_layout.addStretch()
        
        # 顯示工作區路徑與切換按鈕
        self.path_info = QLabel(f"工作區:\n{self.workspace_dir}")
        self.path_info.setWordWrap(True)
        self.path_info.setStyleSheet("color: #72727c; font-size: 11px;")
        sidebar_layout.addWidget(self.path_info)
        
        self.change_workspace_btn = QPushButton("📂 切換工作區")
        self.change_workspace_btn.clicked.connect(self.change_workspace)
        sidebar_layout.addWidget(self.change_workspace_btn)
        
        main_layout.addWidget(sidebar)
        
        # 2. 右側主要內容區（採用 Splitter 分割「寫作匯入」與「控制台日誌」）
        right_splitter = QSplitter(Qt.Vertical)
        
        # 上半部：寫作匯入面板
        import_panel = QFrame()
        import_panel.setObjectName("cardFrame")
        import_layout = QHBoxLayout(import_panel)
        import_layout.setContentsMargins(10, 10, 10, 10)
        import_layout.setSpacing(10)
        
        # 2.1 待匯入檔案列表 (左側)
        list_container = QWidget()
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 0, 0)
        
        title_box = QHBoxLayout()
        title_box.addWidget(QLabel("待處理文字檔清單:"))
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedWidth(30)
        refresh_btn.clicked.connect(self.refresh_file_list)
        title_box.addWidget(refresh_btn)
        list_layout.addLayout(title_box)
        
        self.file_list_widget = QListWidget()
        self.file_list_widget.setFixedWidth(250)
        self.file_list_widget.itemSelectionChanged.connect(self.on_file_selected)
        list_layout.addWidget(self.file_list_widget)
        
        import_layout.addWidget(list_container)
        
        # 2.2 動態表單面板 (右側)
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(5, 0, 5, 0)
        
        form_layout.addWidget(QLabel("選擇歸類網站分區:"))
        self.collection_combo = QComboBox()
        for col_name, col_info in self.schema.items():
            self.collection_combo.addItem(col_info["label"], col_name)
        self.collection_combo.currentIndexChanged.connect(self.on_collection_changed)
        form_layout.addWidget(self.collection_combo)
        
        # 用於動態欄位的 ScrollArea
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: #22222b; border: none;")
        self.scroll_widget = QWidget()
        self.scroll_widget.setStyleSheet("background-color: #22222b;")
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setSpacing(12)
        self.scroll_layout.setContentsMargins(0, 5, 0, 5)
        self.scroll_area.setWidget(self.scroll_widget)
        form_layout.addWidget(self.scroll_area)
        
        # 匯入按鈕
        self.import_btn = QPushButton("📥 匯入選中檔案至個人網站")
        self.import_btn.setObjectName("primaryButton")
        self.import_btn.clicked.connect(self.import_selected_file)
        form_layout.addWidget(self.import_btn)
        
        import_layout.addWidget(form_container)
        right_splitter.addWidget(import_panel)
        
        # 下半部：日誌與控制台輸出面板
        console_panel = QFrame()
        console_panel.setObjectName("cardFrame")
        console_layout = QVBoxLayout(console_panel)
        console_layout.setContentsMargins(15, 10, 15, 10)
        
        console_title_layout = QHBoxLayout()
        console_title_layout.addWidget(QLabel("控制台即時日誌:"))
        clear_log_btn = QPushButton("清除日誌")
        clear_log_btn.setFixedWidth(80)
        clear_log_btn.setStyleSheet("font-size: 11px; padding: 4px;")
        clear_log_btn.clicked.connect(self.clear_logs)
        console_title_layout.addWidget(clear_log_btn)
        console_layout.addLayout(console_title_layout)
        
        self.console_log = QPlainTextEdit()
        self.console_log.setReadOnly(True)
        self.console_log.setStyleSheet("background-color: #121216; font-family: Consolas, monospace; font-size: 12px; color: #a2a2ab; border: 1px solid #1c1c24;")
        console_layout.addWidget(self.console_log)
        
        right_splitter.addWidget(console_panel)
        
        # 設定分割器初始權重大小
        right_splitter.setSizes([500, 200])
        main_layout.addWidget(right_splitter)
        
        # 保存動態生成的欄位控制件對照表
        self.dynamic_widgets = {}

    def log(self, text):
        try:
            if not hasattr(self, "console_log") or self.console_log is None:
                return
            escaped_text = html.escape(str(text))
            
            # 高對比螢光色彩風格分類
            if any(kw in text for kw in ["🎉", "✓", "✅", "成功"]):
                color = "#00ff88"  # 亮綠
            elif any(kw in text for kw in ["🚀", "🔄", "⌛", "正在", "進程"]):
                color = "#00d4ff"  # 天空亮藍
            elif any(kw in text for kw in ["⚠️", "ℹ️", "提示"]):
                color = "#ffcc00"  # 金黃
            elif any(kw in text for kw in ["❌", "ERROR", "衝突", "失敗"]):
                color = "#ff4d4d"  # 亮紅
            else:
                color = "#e2e2e9"  # 純白

            formatted_html = f'<span style="color: {color};">{escaped_text}</span>'
            self.console_log.appendHtml(formatted_html)
            
            # 移動游標至末端以自動捲動
            cursor = self.console_log.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.console_log.setTextCursor(cursor)
            
            # 控制台維持最大 1000 行
            if self.console_log.blockCount() > 1000:
                cursor.movePosition(QTextCursor.MoveOperation.Start)
                cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()
        except Exception:
            pass

    def clear_logs(self):
        self.console_log.clear()

    def get_existing_target_files_map(self):
        """建置山莊 content 資料夾內所有既有 .md 檔對照表"""
        content_dir = os.path.join(self.project_dir, "src", "content")
        target_map = {} # filename_lower -> { path, collection, mtime }
        if not os.path.exists(content_dir):
            return target_map
            
        for col in os.listdir(content_dir):
            col_path = os.path.join(content_dir, col)
            if os.path.isdir(col_path):
                for fname in os.listdir(col_path):
                    if fname.endswith(".md") and not fname.startswith("_"):
                        fpath = os.path.join(col_path, fname)
                        try:
                            mtime = os.path.getmtime(fpath)
                        except Exception:
                            mtime = 0
                        target_map[fname.lower()] = {
                            "filename": fname,
                            "path": fpath,
                            "collection": col,
                            "mtime": mtime
                        }
        return target_map

    def refresh_file_list(self):
        self.file_list_widget.clear()
        if not os.path.exists(self.workspace_dir):
            self.log(f"❌ [錯誤] 找不到工作區路徑: {self.workspace_dir}")
            return
        
        files = [f for f in os.listdir(self.workspace_dir) if f.endswith(".md") or f.endswith(".txt")]
        target_map = self.get_existing_target_files_map()
        
        imported_count = 0
        for f in files:
            item = QListWidgetItem(f)
            base_name = os.path.splitext(f)[0]
            possible_target = f"{base_name.lower()}.md"
            slugified_target = f"{self.slugify_text(base_name).lower()}.md"
            
            # 檢查是否已存在於山莊 content 中
            matched_info = None
            if f.lower() in target_map:
                matched_info = target_map[f.lower()]
            elif possible_target in target_map:
                matched_info = target_map[possible_target]
            elif slugified_target in target_map:
                matched_info = target_map[slugified_target]
                
            if matched_info:
                imported_count += 1
                mtime_str = datetime.datetime.fromtimestamp(matched_info["mtime"]).strftime("%Y-%m-%d %H:%M:%S")
                item.setForeground(QColor("#00ff88")) # 已匯入高亮呈現亮綠色
                item.setToolTip(f"✅ [已匯入山莊]\n目標分區: {matched_info['collection']}\n目標檔名: {matched_info['filename']}\n修改時間: {mtime_str}")
            else:
                item.setForeground(QColor("#e2e2e9")) # 未匯入呈現預設灰白色
                item.setToolTip("📄 尚未匯入山莊")
                
            self.file_list_widget.addItem(item)
            
        self.log(f"✓ 已刷新文字檔列表，共尋找到 {len(files)} 個檔案 ({imported_count} 個已有匯入紀錄) ({self.workspace_dir})。")

    def change_workspace(self):
        new_dir = QFileDialog.getExistingDirectory(
            self, "選取新工作區資料夾", self.workspace_dir
        )
        if not new_dir:
            return
        
        if not os.path.exists(new_dir):
            QMessageBox.warning(self, "路徑無效", "選取的資料夾不存在！")
            return
        
        self.workspace_dir = new_dir
        self.path_info.setText(f"工作區:\n{self.workspace_dir}")
        
        # 寫回 sync-config.json 持久化
        config_path = os.path.join(self.project_dir, "sync-config.json")
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump({"workspacePath": self.workspace_dir}, f, ensure_ascii=False, indent=2)
            self.log(f"✅ 工作區已成功切換並寫入設定檔: {self.workspace_dir}")
        except Exception as e:
            self.log(f"⚠️ 寫入 sync-config.json 失敗: {e}")
            
        # 觸發即時熱更新
        self.refresh_file_list()

    def on_file_selected(self):
        selected = self.file_list_widget.selectedItems()
        if not selected:
            return
        filename = selected[0].text()
        filepath = os.path.join(self.workspace_dir, filename)
        
        # 解析檔案的 Frontmatter 以利帶入預設值
        fm, body = self.parse_frontmatter(filepath)
        
        # 若 Frontmatter 中無標題或名稱，自動以檔名(去副檔名)作為預設值
        base_title = os.path.splitext(filename)[0]
        if "title" not in fm or not fm["title"]:
            fm["title"] = base_title
        if "name" not in fm or not fm["name"]:
            fm["name"] = base_title
        
        # 填入表單
        self.populate_form(fm)

    def parse_frontmatter(self, file_path):
        if not os.path.exists(file_path):
            return {}, ""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            self.log(f"⚠️ 解析檔案失敗: {e}")
            return {}, ""
        
        fm = {}
        body = content
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                fm_block = parts[1]
                body = parts[2].strip()
                for line in fm_block.split("\n"):
                    line = line.strip()
                    if not line or ":" not in line:
                        continue
                    colon_idx = line.find(":")
                    if colon_idx > 0:
                        k = line[:colon_idx].strip()
                        v = line[colon_idx+1:].strip()
                        
                        if v.startswith("[") and v.endswith("]"):
                            items = [x.strip().strip('"').strip("'") for x in v[1:-1].split(",") if x.strip()]
                            fm[k] = items
                        else:
                            fm[k] = v.strip('"').strip("'")
        return fm, body

    def on_collection_changed(self):
        selected = self.file_list_widget.selectedItems()
        fm = {}
        if selected:
            filename = selected[0].text()
            filepath = os.path.join(self.workspace_dir, filename)
            fm, _ = self.parse_frontmatter(filepath)
        self.populate_form(fm)

    def get_novels_list(self):
        novels = set(getattr(self, "custom_novels", []))
        novels_dir = os.path.join(self.project_dir, "src", "content", "novels")
        if os.path.exists(novels_dir):
            for file in os.listdir(novels_dir):
                if file.endswith(".md"):
                    filepath = os.path.join(novels_dir, file)
                    fm, _ = self.parse_frontmatter(filepath)
                    title = fm.get("title") or os.path.splitext(file)[0]
                    if title:
                        novels.add(title)
        return sorted(list(novels))

    def get_factions_list(self):
        factions = set(getattr(self, "custom_factions", []))
        factions_dir = os.path.join(self.project_dir, "src", "content", "factions")
        if os.path.exists(factions_dir):
            for file in os.listdir(factions_dir):
                if file.endswith(".md"):
                    filepath = os.path.join(factions_dir, file)
                    fm, _ = self.parse_frontmatter(filepath)
                    title = fm.get("title") or os.path.splitext(file)[0]
                    if title:
                        factions.add(title)
        return sorted(list(factions))

    def add_novel_dialog(self, combo):
        name, ok = QInputDialog.getText(self, "新增作品", "請輸入小說作品名稱:")
        if ok and name.strip():
            clean_name = name.strip()
            
            # 檢查是否與既有作品資料重複
            existing_novels = self.get_novels_list()
            combo_items = [combo.itemText(i) for i in range(combo.count())]
            all_existing = set(existing_novels + combo_items)
            
            if clean_name in all_existing:
                QMessageBox.warning(
                    self, "同名資料重複警告",
                    f"⚠️ 偵測到已有同名作品「{clean_name}」！\n已自動為您定位並選取該作品，請勿重複建立。"
                )
                idx = combo.findText(clean_name)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
                else:
                    combo.setCurrentText(clean_name)
                self.log(f"⚠️ [警告] 輸入的作品「{clean_name}」已存在於選單中，已自動定位選取。")
                return

            if not hasattr(self, "custom_novels"):
                self.custom_novels = []
            if clean_name not in self.custom_novels:
                self.custom_novels.append(clean_name)
            combo.addItem(clean_name, clean_name)
            combo.setCurrentText(clean_name)
            self.log(f"✅ 已成功新增作品至選單: {clean_name}")

    def add_faction_dialog(self, combo):
        name, ok = QInputDialog.getText(self, "新增門派/陣營", "請輸入門派或陣營名稱:")
        if ok and name.strip():
            clean_name = name.strip()
            
            # 檢查是否與既有門派/陣營資料重複
            existing_factions = self.get_factions_list()
            combo_items = [combo.itemText(i) for i in range(combo.count())]
            all_existing = set(existing_factions + combo_items)
            
            if clean_name in all_existing:
                QMessageBox.warning(
                    self, "同名資料重複警告",
                    f"⚠️ 偵測到已有同名門派/陣營「{clean_name}」！\n已自動為您定位並選取該門派，請勿重複建立。"
                )
                idx = combo.findText(clean_name)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
                else:
                    combo.setCurrentText(clean_name)
                self.log(f"⚠️ [警告] 輸入的門派/陣營「{clean_name}」已存在於選單中，已自動定位選取。")
                return

            if not hasattr(self, "custom_factions"):
                self.custom_factions = []
            if clean_name not in self.custom_factions:
                self.custom_factions.append(clean_name)
            combo.addItem(clean_name, clean_name)
            combo.setCurrentText(clean_name)
            self.log(f"✅ 已成功新增門派至選單: {clean_name}")

    def add_alias_dialog(self, array_widget):
        name, ok = QInputDialog.getText(self, "新增自訂稱號/別名", "請輸入江湖稱號或別名:")
        if ok and name.strip():
            clean_name = name.strip()
            array_widget.add_item(clean_name)
            self.log(f"✅ 已成功新增自訂稱號/別名: {clean_name}")

    def slugify_text(self, text):
        if not text or not text.strip():
            return ""
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            res = subprocess.run(
                ["node", os.path.join(self.project_dir, "scripts", "gui-helper.js"), "--slugify", text.strip()],
                capture_output=True, text=True, encoding="utf-8", creationflags=creationflags
            )
            return res.stdout.strip()
        except Exception:
            return text.strip().lower().replace(" ", "-")

    def on_title_editing_finished(self, edit_widget, edit_slug_widget, original_title):
        try:
            new_title = edit_widget.text().strip()
        except Exception:
            return
            
        if new_title and new_title != original_title:
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, lambda: self._safe_ask_sync_slug(edit_widget, edit_slug_widget, new_title))

    def _safe_ask_sync_slug(self, edit_widget, edit_slug_widget, new_title):
        try:
            current_title = edit_widget.text().strip()
            current_slug = edit_slug_widget.text().strip()
        except Exception:
            return
            
        if current_title != new_title:
            return
            
        new_slug = self.slugify_text(new_title)
        if new_slug and new_slug != current_slug:
            reply = QMessageBox.question(
                self, "同步更新網頁別名 (slug)",
                f"偵測到標題/名稱已修改為：「{new_title}」\n是否同步將網頁別名 (slug) 更新為拼音：「{new_slug}」？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                try:
                    edit_slug_widget.setText(new_slug)
                    self.log(f"✅ 已同步更新網頁別名 (slug) 為: {new_slug}")
                except Exception:
                    pass

    def populate_form(self, defaults={}):
        # 清除現有動態表單欄位
        for i in reversed(range(self.scroll_layout.count())):
            item = self.scroll_layout.itemAt(i)
            if item.widget() is not None:
                item.widget().deleteLater()
            elif item.layout() is not None:
                # 遞迴刪除子佈局
                for j in reversed(range(item.layout().count())):
                    w = item.layout().itemAt(j).widget()
                    if w is not None:
                        w.deleteLater()
        
        self.dynamic_widgets.clear()
        
        col_name = self.collection_combo.currentData()
        if not col_name or col_name not in self.schema:
            return
            
        fields = self.schema[col_name]["fields"]
        
        # 1. 顯式提供「網頁別名 (slug)」手動編輯欄位
        lbl_slug = QLabel("網頁別名 (slug, 選填手動自訂):")
        lbl_slug.setStyleSheet("color: #e5a93b; font-weight: bold;")
        edit_slug = QLineEdit(str(defaults.get("slug", "")))
        edit_slug.setPlaceholderText("留空則自動採用標題之拼音生成")
        self.scroll_layout.addWidget(lbl_slug)
        self.scroll_layout.addWidget(edit_slug)
        self.dynamic_widgets["slug"] = ("text_single", edit_slug)
        
        # 逐一生成動態欄位
        for field_name, field_info in fields.items():
            field_type = field_info["type"]
            field_label = field_info["label"]
            
            # 使用選中檔案已存在的 frontmatter 值，否則為空
            val = defaults.get(field_name, "")
            
            # 專屬邏輯：小說名稱欄位 (novel) 升級為動態資料庫下拉選單 + ➕ 新增按鈕
            if field_name == "novel":
                lbl = QLabel(f"{field_label} ({field_name}):")
                lbl.setStyleSheet("color: #a2a2ab; font-weight: bold;")
                
                combo_box_layout = QHBoxLayout()
                combo = QComboBox()
                combo.setEditable(True)
                novels_list = self.get_novels_list()
                
                combo.addItem("-- 請選擇或手動輸入 --", "")
                for nov in novels_list:
                    combo.addItem(nov, nov)
                if val:
                    combo.setCurrentText(str(val))
                    
                add_btn = QPushButton("➕ 新增作品")
                add_btn.setFixedWidth(90)
                add_btn.clicked.connect(lambda _, c=combo: self.add_novel_dialog(c))
                
                combo_box_layout.addWidget(combo)
                combo_box_layout.addWidget(add_btn)
                
                self.scroll_layout.addWidget(lbl)
                self.scroll_layout.addLayout(combo_box_layout)
                self.dynamic_widgets[field_name] = ("combo_custom", combo)
                
            # 專屬邏輯：所屬門派/陣營欄位 (affiliation) 升級為動態資料庫下拉選單 + ➕ 新增按鈕
            elif field_name == "affiliation":
                lbl = QLabel(f"{field_label} ({field_name}):")
                lbl.setStyleSheet("color: #a2a2ab; font-weight: bold;")
                
                combo_box_layout = QHBoxLayout()
                combo = QComboBox()
                combo.setEditable(True)
                factions_list = self.get_factions_list()
                
                combo.addItem("-- 請選擇或手動輸入 --", "")
                for fac in factions_list:
                    combo.addItem(fac, fac)
                if val:
                    combo.setCurrentText(str(val))
                    
                add_btn = QPushButton("➕ 新增門派")
                add_btn.setFixedWidth(90)
                add_btn.clicked.connect(lambda _, c=combo: self.add_faction_dialog(c))
                
                combo_box_layout.addWidget(combo)
                combo_box_layout.addWidget(add_btn)
                
                self.scroll_layout.addWidget(lbl)
                self.scroll_layout.addLayout(combo_box_layout)
                self.dynamic_widgets[field_name] = ("combo_custom", combo)
                
            elif field_type in ["text", "slug"]:
                if field_info.get("multiline", False):
                    # 多行文字
                    lbl = QLabel(f"{field_label} ({field_name}):")
                    lbl.setStyleSheet("color: #a2a2ab; font-weight: bold;")
                    edit = QPlainTextEdit()
                    edit.setPlainText(str(val))
                    edit.setMinimumHeight(80)
                    self.scroll_layout.addWidget(lbl)
                    self.scroll_layout.addWidget(edit)
                    self.dynamic_widgets[field_name] = ("text_multi", edit)
                else:
                    # 單行文字 / 標題與名稱自訂欄位
                    is_title_or_name = field_name in ["title", "name"] or field_type == "slug"
                    lbl_text = f"⭐ 自訂{field_label} ({field_name}):" if is_title_or_name else f"{field_label} ({field_name}):"
                    lbl = QLabel(lbl_text)
                    if is_title_or_name:
                        lbl.setStyleSheet("color: #00ff88; font-weight: bold; font-size: 13px;")
                    else:
                        lbl.setStyleSheet("color: #a2a2ab; font-weight: bold;")
                    
                    edit = QLineEdit(str(val))
                    if is_title_or_name:
                        edit.setPlaceholderText("請輸入自訂標題 / 人物名稱...")
                        edit.setStyleSheet("border: 1.5px solid #00ff88; padding: 5px; font-weight: bold; color: #ffffff; background: #1a1a24;")
                        orig_val = str(val)
                        edit.editingFinished.connect(lambda e=edit, s=edit_slug, o=orig_val: self.on_title_editing_finished(e, s, o))
                    self.scroll_layout.addWidget(lbl)
                    self.scroll_layout.addWidget(edit)
                    self.dynamic_widgets[field_name] = ("text_single", edit)
                    
            elif field_type == "date":
                # 日期
                lbl = QLabel(f"{field_label} ({field_name}):")
                lbl.setStyleSheet("color: #a2a2ab; font-weight: bold;")
                edit = QDateEdit()
                edit.setCalendarPopup(True)
                edit.setDisplayFormat("yyyy-MM-dd")
                
                # 若已有日期值，嘗試解析
                from PySide6.QtCore import QDate
                if val:
                    qdate = QDate.fromString(str(val), "yyyy-MM-dd")
                    if qdate.isValid():
                        edit.setDate(qdate)
                    else:
                        edit.setDate(QDate.currentDate())
                else:
                    edit.setDate(QDate.currentDate())
                    
                self.scroll_layout.addWidget(lbl)
                self.scroll_layout.addWidget(edit)
                self.dynamic_widgets[field_name] = ("date", edit)
                
            elif field_type == "select":
                # 下拉選單
                lbl = QLabel(f"{field_label} ({field_name}):")
                lbl.setStyleSheet("color: #a2a2ab; font-weight: bold;")
                combo = QComboBox()
                opts = field_info.get("options", [])
                
                for idx, opt in enumerate(opts):
                    combo.addItem(opt["label"], opt["value"])
                    if str(val) == opt["value"]:
                        combo.setCurrentIndex(idx)
                        
                self.scroll_layout.addWidget(lbl)
                self.scroll_layout.addWidget(combo)
                self.dynamic_widgets[field_name] = ("select", combo)
                
            elif field_type == "array":
                # 動態陣列欄位 (例: 別名/江湖稱號 alias, 標籤 tags)
                array_widget = ArrayFieldWidget(f"{field_label} ({field_name})")
                array_widget.set_values(val)
                
                # 專屬增強：若是別名/江湖稱號 (alias)，且目前無值，預設為其新增一個空白的自訂輸入框
                if field_name == "alias" and not val:
                    array_widget.add_item("")
                    
                # 專屬增強：如果是別名/江湖稱號 (alias)，在其標頭新增 [➕ 新增稱號] 按鈕
                if field_name == "alias":
                    add_alias_btn = QPushButton("➕ 新增稱號")
                    add_alias_btn.setFixedWidth(90)
                    add_alias_btn.setStyleSheet("font-size: 11px; padding: 4px; background-color: #2d5f5a; color: #ffffff;")
                    add_alias_btn.clicked.connect(lambda _, w=array_widget: self.add_alias_dialog(w))
                    array_widget.header_layout.addWidget(add_alias_btn)
                    
                self.scroll_layout.addWidget(array_widget)
                self.dynamic_widgets[field_name] = ("array", array_widget)
                
            elif field_type in ["url", "image"]:
                # URL / 圖片路徑
                lbl = QLabel(f"{field_label} ({field_name}):")
                lbl.setStyleSheet("color: #a2a2ab; font-weight: bold;")
                edit = QLineEdit(str(val))
                self.scroll_layout.addWidget(lbl)
                self.scroll_layout.addWidget(edit)
                self.dynamic_widgets[field_name] = (field_type, edit)

    def toggle_test_server(self):
        if self.astro_process and self.astro_process.state() == QProcess.Running:
            self.log("⏹️ 正在停止本地測試伺服器...")
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.astro_process.processId())], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.astro_process = None
            self.test_server_btn.setText("🧪 啟動本地測試")
            self.test_server_btn.setStyleSheet("")
            self.log("⏹️ 本地測試伺服器已成功關閉。")
        else:
            self.log("🧪 正在啟動本地測試伺服器 (npm run dev)...")
            self.astro_process = QProcess()
            self.astro_process.setWorkingDirectory(self.project_dir)
            self.astro_process.readyReadStandardOutput.connect(self.on_astro_stdout)
            self.astro_process.readyReadStandardError.connect(self.on_astro_stderr)
            
            self.current_astro_port = 4321
            self.browser_opened = False
            
            self.astro_process.start("cmd.exe", ["/c", "npm run dev"])
            self.test_server_btn.setText("⏹️ 停止測試伺服器")
            self.test_server_btn.setStyleSheet("background-color: #a93b3b; color: white;")

    def on_astro_stdout(self):
        data = self.astro_process.readAllStandardOutput().data().decode("utf-8", errors="ignore")
        self.log(data.strip())
        
        # 動態偵測並分析 Astro 啟動的本地連接埠 (例: Local    http://127.0.0.1:4324/)
        import re
        port_match = re.search(r"(?:Local|Local\s+)\s+https?://(?:127\.0\.0\.1|localhost|\[::1\]):(\d+)", data)
        if port_match:
            detected_port = int(port_match.group(1))
            self.current_astro_port = detected_port
            self.log(f"ℹ️ 成功探測到伺服器運行於連接埠: {detected_port}")
            if not getattr(self, "browser_opened", False):
                self.browser_opened = True
                
                # 如果是連鎖自動啟動，直接開啟相對應頁面
                flag = getattr(self, "auto_open_keystatic_after_start", False)
                if flag == "mover":
                    self.auto_open_keystatic_after_start = False
                    self.log(f"🚀 伺服器已就緒，連鎖打開移置閣 (http://localhost:{detected_port}/keystatic/move-articles)")
                    QDesktopServices.openUrl(QUrl(f"http://localhost:{detected_port}/keystatic/move-articles"))
                elif flag: # 也就是 True 或非空字串 (CMS 後台)
                    self.auto_open_keystatic_after_start = False
                    self.log(f"🚀 伺服器已就緒，連鎖打開後台 (http://localhost:{detected_port}/keystatic)")
                    QDesktopServices.openUrl(QUrl(f"http://localhost:{detected_port}/keystatic"))
                else:
                    self.log(f"🚀 自動打開首頁 (http://localhost:{detected_port})")
                    QDesktopServices.openUrl(QUrl(f"http://localhost:{detected_port}"))

    def on_astro_stderr(self):
        data = self.astro_process.readAllStandardError().data().decode("utf-8", errors="ignore")
        self.log(f"[Astro 錯誤] {data.strip()}")

    def open_keystatic_cms(self):
        self.log("📝 正在開啟 Keystatic 後台編輯器...")
        port = getattr(self, "current_astro_port", 4321)
        
        server_found = False
        # 如果測試伺服器未經由 GUI 運行，我們自動探測本地 4321~4330 埠口是否有別的行程正開啟著
        if not (self.astro_process and self.astro_process.state() == QProcess.Running):
            import socket
            for p in range(4321, 4331):
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.04)
                res = s.connect_ex(('127.0.0.1', p))
                s.close()
                if res == 0:
                    port = p
                    server_found = True
                    break
        else:
            server_found = True

        if not server_found:
            self.log("ℹ️ 偵測到本地測試伺服器未運行，正在為您自動連鎖啟動測試伺服器...")
            self.auto_open_keystatic_after_start = True # 標記啟動後要直接開啟 keystatic 后台
            self.toggle_test_server()
            return
        
        QProcess.startDetached("cmd.exe", ["/c", f"start http://localhost:{port}/keystatic"], self.project_dir)
        self.log(f"✓ 已直接在瀏覽器呼叫開啟 Keystatic 頁面 (動態連接埠: {port})。")

    def open_articles_mover(self):
        self.log("🚚 正在開啟藏書移置閣...")
        port = getattr(self, "current_astro_port", 4321)
        
        server_found = False
        # 如果測試伺服器未經由 GUI 運行，我們自動探測本地 4321~4330 埠口是否有別的行程正開啟著
        if not (self.astro_process and self.astro_process.state() == QProcess.Running):
            import socket
            for p in range(4321, 4331):
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.04)
                res = s.connect_ex(('127.0.0.1', p))
                s.close()
                if res == 0:
                    port = p
                    server_found = True
                    break
        else:
            server_found = True

        if not server_found:
            self.log("ℹ️ 偵測到本地測試伺服器未運行，正在為您自動連鎖啟動測試伺服器...")
            self.auto_open_keystatic_after_start = "mover" # 標記啟動後要開啟 mover 面板
            self.toggle_test_server()
            return
        
        QProcess.startDetached("cmd.exe", ["/c", f"start http://localhost:{port}/keystatic/move-articles"], self.project_dir)
        self.log(f"✓ 已直接在瀏覽器呼叫開啟藏書移置閣 (動態連接埠: {port})。")

    def sync_online_edit(self):
        self.log("🔄 正在執行線上編輯同步 (git pull --rebase)...")
        self.run_git_process(["pull", "--rebase"], "同步完成！", "同步時發生衝突！")

    def confirm_publish(self):
        self.log("⌛ 正在檢查 Git 變更檔案清單...")
        # 執行 git status --porcelain 取得本次變更檔案
        try:
            res = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding="utf-8",
                errors="ignore"
            )
            files = [line.strip() for line in res.stdout.split("\n") if line.strip()]
        except Exception as e:
            files = []
            self.log(f"⚠️ 無法取得 Git 狀態: {e}")
            
        dialog = PublishDialog(files, self)
        if dialog.exec() == QDialog.Accepted:
            commit_msg = dialog.msg_edit.text().strip()
            self.log(f"🚀 開始執行發布程序，提交訊息: \"{commit_msg}\"")
            self.run_publish_flow(commit_msg)

    def set_ui_busy(self, busy: bool):
        self.is_busy = busy
        buttons = [
            self.test_server_btn, self.open_cms_btn, self.open_mover_btn,
            self.sync_btn, self.publish_btn, self.fix_env_btn, self.restore_backup_btn,
            self.import_btn, self.change_workspace_btn
        ]
        for btn in buttons:
            btn.setEnabled(not busy)
            
        if busy:
            self.publish_btn.setText("🚀 發布上線中...")
            self.progress_bar.setValue(0)
            self.progress_bar.show()
        else:
            self.publish_btn.setText("🚀 一鍵發布上線")
            self.progress_bar.setValue(0)
            self.progress_bar.hide()

    def closeEvent(self, event):
        if getattr(self, "is_busy", False):
            reply = QMessageBox.question(
                self, "發布進行中",
                "網站發布程序仍在背景進行中，確定要關閉視窗嗎？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
        event.accept()

    def run_publish_flow(self, commit_message):
        # 執行一鍵發布上線流程: git add . -> git commit -> git pull --rebase -> git push
        self.set_ui_busy(True)
        self.progress_bar.setValue(10)

        def finish_publish(success=True):
            self.set_ui_busy(False)
            if success:
                self.refresh_file_list()
                if hasattr(self, "tray_icon") and self.tray_icon.isSystemTrayAvailable():
                    self.tray_icon.showMessage("網站發布完成", "網站發布完成", QSystemTrayIcon.Information, 3000)

        def step_push():
            self.log("🚀 正在將代碼推送到 GitHub 儲存庫...")
            self.progress_bar.setValue(75)
            self.run_git_process(
                ["push"],
                "🎉 網站發布成功！已順利上傳至線上個人網站。",
                "❌ 發布推送失敗！可能是遠端有更新，請先點擊「同步線上編輯」按鈕。",
                on_finish=lambda: finish_publish(True),
                on_error_finish=lambda: finish_publish(False)
            )

        def step_pull():
            self.log("🔄 正在進行安全拉取同步，防範衝突...")
            self.progress_bar.setValue(50)
            self.run_git_process(
                ["pull", "--rebase"],
                step_push,
                "❌ 同步拉取時發生衝突！已自動還原本地狀態。",
                next_on_error=True,
                on_error_finish=lambda: finish_publish(False)
            )

        def step_commit():
            self.log("📝 正在儲存本地變更...")
            self.progress_bar.setValue(25)
            self.run_git_process(
                ["commit", "-m", commit_message],
                step_pull,
                step_pull,
                next_on_error=True
            )

        self.log("📥 正在準備暫存所有變更...")
        self.run_git_process(
            ["add", "."],
            step_commit,
            "❌ Git 暫存失敗！",
            on_error_finish=lambda: finish_publish(False)
        )

    def run_git_process(self, args, on_success, on_error, next_on_error=False, on_finish=None, on_error_finish=None):
        proc = QProcess(self)
        proc.setWorkingDirectory(self.project_dir)
        
        def handle_finish(exit_code, exit_status):
            try:
                p = self.sender() or proc
            except Exception:
                p = proc
            try:
                stdout = p.readAllStandardOutput().data().decode("utf-8", errors="ignore").strip()
            except Exception:
                stdout = ""
            try:
                stderr = p.readAllStandardError().data().decode("utf-8", errors="ignore").strip()
            except Exception:
                stderr = ""
            if stdout: self.log(stdout)
            if stderr: self.log(stderr)
            
            if exit_code == 0:
                if callable(on_success):
                    on_success()
                else:
                    self.log(f"✓ {on_success}")
                if callable(on_finish):
                    try: on_finish()
                    except Exception as e: self.log(f"⚠️ 回調異常: {e}")
            else:
                # 自動安全還原防呆衝突處理
                if "conflict" in stdout.lower() or "conflict" in stderr.lower() or ("pull" in args and "--rebase" in args):
                    self.log("⚠️ 偵測到與線上內容衝突，自動執行安全性還原 (git rebase --abort)...")
                    try:
                        subprocess.run(["git", "rebase", "--abort"], cwd=self.project_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        self.log("✓ 已自動撤銷衝突同步，本地專案保持乾淨完好。請點擊「同步線上編輯」查看。")
                    except Exception as e:
                        self.log(f"⚠️ 撤銷失敗: {e}")

                if next_on_error and callable(on_error):
                    on_error()
                else:
                    self.log(f"❌ {on_error if isinstance(on_error, str) else 'Git 指令執行失敗'}")
                    if "conflict" in stdout.lower() or "conflict" in stderr.lower():
                        QMessageBox.critical(self, "Git 衝突警告", "偵測到與線上編輯內容衝突！已自動還原本地狀態。")

                if callable(on_error_finish):
                    try: on_error_finish()
                    except Exception as e: self.log(f"⚠️ 錯誤回調異常: {e}")
                elif callable(on_finish):
                    try: on_finish()
                    except Exception as e: self.log(f"⚠️ 回調異常: {e}")
        
        proc.finished.connect(handle_finish)
        proc.start("git", args)
        self.active_processes.append(proc)

    def fix_dev_env(self):
        self.log("⚙️ 正在修復並還原 Keystatic 開發設定環境...")
        cmd_path = os.path.join(self.project_dir, "scripts", "batches", "還原開發環境.bat")
        if os.path.exists(cmd_path):
            res = subprocess.run(["cmd.exe", "/c", cmd_path], cwd=self.project_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.log(res.stdout.decode("utf-8", errors="ignore"))
            self.log("✓ 開發環境設定已順利修復還原。")
        else:
            self.log("❌ 找不到 還原開發環境.bat 檔案！")

    def restore_backup(self):
        self.log("📦 正在啟動歷史備份還原工具...")
        cmd_path = os.path.join(self.project_dir, "scripts", "batches", "還原歷史備份.bat")
        if os.path.exists(cmd_path):
            # 以新視窗獨立啟動互動式還原工具
            QProcess.startDetached("cmd.exe", ["/c", "start", cmd_path], self.project_dir)
            self.log("✓ 備份還原工具已在獨立 CMD 視窗開啟。")
        else:
            self.log("❌ 找不到 還原歷史備份.bat 檔案！")

    def import_selected_file(self):
        selected = self.file_list_widget.selectedItems()
        if not selected:
            QMessageBox.warning(self, "警告", "請先從左側清單選擇要匯入的文字檔！")
            return
            
        filename = selected[0].text()
        filepath = os.path.join(self.workspace_dir, filename)
        col_name = self.collection_combo.currentData()
        
        # 收集表單資料
        data = {}
        for field_name, (field_type, widget) in self.dynamic_widgets.items():
            if field_type == "text_single":
                data[field_name] = widget.text().strip()
            elif field_type == "text_multi":
                data[field_name] = widget.toPlainText().strip()
            elif field_type == "date":
                data[field_name] = widget.date().toString("yyyy-MM-dd")
            elif field_type == "select":
                data[field_name] = widget.currentData()
            elif field_type == "combo_custom":
                data[field_name] = widget.currentText().strip()
            elif field_type == "array":
                data[field_name] = widget.get_values()
            elif field_type in ["url", "image"]:
                data[field_name] = widget.text().strip()
                
        # 檢查目標分區或全站中是否已存在對應的目標 .md 檔案，若存在則提示修改時間並由使用者決定是否覆寫
        target_map = self.get_existing_target_files_map()
        title_or_name = data.get("title") or data.get("name") or os.path.splitext(filename)[0]
        custom_slug = data.get("slug", "").strip()
        predicted_slug = custom_slug if custom_slug else self.slugify_text(title_or_name)
        if not predicted_slug.endswith(".md"):
            target_md_filename = f"{predicted_slug}.md"
        else:
            target_md_filename = predicted_slug

        # 在目標分區路徑或是對照表中尋找匹配
        matched_target_info = None
        target_path_in_col = os.path.join(self.project_dir, "src", "content", col_name, target_md_filename)
        if os.path.exists(target_path_in_col):
            matched_target_info = {
                "filename": target_md_filename,
                "path": target_path_in_col,
                "collection": col_name,
                "mtime": os.path.getmtime(target_path_in_col)
            }
        elif target_md_filename.lower() in target_map:
            matched_target_info = target_map[target_md_filename.lower()]

        if matched_target_info:
            src_mtime = os.path.getmtime(filepath) if os.path.exists(filepath) else 0
            tgt_mtime = matched_target_info["mtime"]

            src_time_str = datetime.datetime.fromtimestamp(src_mtime).strftime("%Y-%m-%d %H:%M:%S") if src_mtime else "未知"
            tgt_time_str = datetime.datetime.fromtimestamp(tgt_mtime).strftime("%Y-%m-%d %H:%M:%S") if tgt_mtime else "未知"

            if src_mtime > tgt_mtime:
                time_note = "📌 狀態提示：待匯入的來源檔案【較新】（適合覆寫更新）"
            elif src_mtime < tgt_mtime:
                time_note = "⚠️ 警告提示：山莊目標分區內的已有檔案【較新】！覆寫可能蓋掉後台近期的修改"
            else:
                time_note = "ℹ️ 狀態提示：來源檔案與目標檔案的修改時間相同"

            reply = QMessageBox.question(
                self, "⚠️ 重複目標檔案上傳警告",
                f"偵測到山莊目標分區 [{matched_target_info['collection']}] 中已存在同名檔案：\n「{matched_target_info['filename']}」\n\n"
                f"📁 檔案修改時間對比：\n"
                f"• 待匯入檔案 (本地來源): {src_time_str}\n"
                f"• 已存在檔案 (山莊目標): {tgt_time_str}\n\n"
                f"{time_note}\n\n"
                f"請問您確定要繼續匯入並覆寫該目標檔案嗎？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )

            if reply != QMessageBox.Yes:
                self.log(f"ℹ️ 使用者取消了重複檔案「{filename}」的匯入作業。")
                return

        # 呼叫 gui-helper.js 執行匯入
        import_proc = QProcess()
        import_proc.setWorkingDirectory(self.project_dir)
        
        def on_import_finish(exit_code, exit_status):
            stdout = import_proc.readAllStandardOutput().data().decode("utf-8", errors="ignore").strip()
            stderr = import_proc.readAllStandardError().data().decode("utf-8", errors="ignore").strip()
            
            if exit_code == 0:
                try:
                    # 尋找輸出中的結果 JSON
                    json_start = stdout.find('{"success":true')
                    if json_start >= 0:
                        res = json.loads(stdout[json_start:])
                        self.log(f"✓ 匯入成功！已轉譯寫入至: {res['path']}")
                        QMessageBox.information(self, "成功", f"文件已順利匯入至分區 {res['collection']}！")
                        self.refresh_file_list()
                    else:
                        self.log(stdout)
                        QMessageBox.warning(self, "提示", "匯入完成，但未能解析回傳的 JSON 結果。")
                except Exception as e:
                    self.log(f"解析匯入結果出錯: {e}\n{stdout}")
            else:
                self.log(f"❌ 匯入失敗！\n錯誤日誌: {stderr}\n輸出: {stdout}")
                QMessageBox.critical(self, "匯入失敗", f"匯入文字檔時出錯:\n{stderr or stdout}")
                
        import_proc.finished.connect(on_import_finish)
        
        # 執行 Node 側的匯入指令
        args = [
            "scripts/gui-helper.js",
            "--import",
            "--file", filepath,
            "--collection", col_name,
            "--data", json.dumps(data, ensure_ascii=False)
        ]
        
        self.log(f"⌛ 正在匯入 \"{filename}\" 至分區 \"{col_name}\"...")
        import_proc.start("node", args)

    def create_desktop_shortcut(self):
        desktop = os.path.expanduser("~/Desktop")
        shortcut_path = os.path.join(desktop, "唐門山莊網站管理控制台.lnk")
        if os.path.exists(shortcut_path):
            return
            
        bat_path = os.path.join(self.project_dir, "開啟控制台.bat")
        
        # 使用 PowerShell 建立捷徑的指令
        ps_script = f"""
        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
        $Shortcut.TargetPath = "{bat_path}"
        $Shortcut.WorkingDirectory = "{self.project_dir}"
        $Shortcut.Description = "唐門山莊網站管理圖形化控制台"
        $Shortcut.Save()
        """
        try:
            subprocess.run(
                ["powershell", "-Command", ps_script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            self.log("✓ 已自動在 Windows 桌面為您建立「唐門山莊網站管理控制台」啟動捷徑！")
        except Exception as e:
            self.log(f"⚠️ 無法自動建立桌面捷徑: {e}")

    def closeEvent(self, event):
        # 視窗關閉時，確實關閉所有的子進程，防止殭屍進程
        if self.astro_process and self.astro_process.state() == QProcess.Running:
            self.log("⏹️ 關閉主程式：正在關閉背景 Astro 測試伺服器...")
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.astro_process.processId())], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        for proc in self.active_processes:
            if proc.state() == QProcess.Running:
                proc.terminate()
                proc.waitForFinished(1000)
                
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
