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
from PySide6.QtCore import Qt, QProcess, QSize, QUrl, QTimer
from PySide6.QtGui import QIcon, QDesktopServices, QFont, QTextCursor, QColor, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLabel, QComboBox, QLineEdit,
    QPlainTextEdit, QPushButton, QScrollArea, QFileDialog, QMessageBox,
    QDateEdit, QDialog, QInputDialog, QFrame, QSplitter,
    QProgressBar, QSystemTrayIcon, QStyle, QTabWidget, QMenu, QTextBrowser
)

# 視窗精美深色樣式表
QSS_STYLE = """
QTabWidget::pane {
    border: 1px solid #2e2e3a;
    background-color: #1a1a20;
    border-radius: 6px;
}
QTabBar::tab {
    background-color: #22222b;
    border: 1px solid #2e2e3a;
    padding: 8px 18px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    color: #a2a2ab;
    font-weight: bold;
}
QTabBar::tab:selected {
    background-color: #e5a93b;
    color: #1a1a20;
    border: 1px solid #e5a93b;
}
QTabBar::tab:hover:!selected {
    background-color: #2d2d3a;
    color: #e2e2e9;
}

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

def to_chinese_num(n: int) -> str:
    """整數轉中文數字 (支援 1 ~ 99)"""
    digits = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
    if n <= 10:
        return digits[n]
    elif n < 20:
        return "十" + digits[n % 10]
    elif n < 100:
        ten = n // 10
        unit = n % 10
        return digits[ten] + "十" + (digits[unit] if unit > 0 else "")
    return str(n)


class DropMarkdownEdit(QPlainTextEdit):
    """專用小說 Markdown 拖曳文字編輯器，支援直接拖入 .md / .txt 檔案並自動剝離 YAML Frontmatter"""
    def __init__(self, parent=None, on_text_changed=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setPlaceholderText("💡 可直接將寫好的 .md 或 .txt 檔案拖曳至此處，或在下方點擊「📋 貼上剪貼簿內容」...\n\n（系統會自動幫您去除開頭的 YAML 標籤，保留純故事正文）")
        if on_text_changed:
            self.textChanged.connect(on_text_changed)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                if file_path and os.path.exists(file_path):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        clean_content = self.strip_frontmatter(content)
                        self.setPlainText(clean_content)
                        event.acceptProposedAction()
                        return
                    except Exception as e:
                        print(f"讀取拖曳檔案失敗: {e}")
        elif event.mimeData().hasText():
            text = event.mimeData().text()
            clean_content = self.strip_frontmatter(text)
            self.setPlainText(clean_content)
            event.acceptProposedAction()
            return
        super().dropEvent(event)

    def strip_frontmatter(self, text: str) -> str:
        import re
        pattern = r"^---\s*\n[\s\S]*?\n---\s*\n"
        return re.sub(pattern, "", text.strip())


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
        self.add_btn.clicked.connect(lambda: self.add_item(""))
        
        self.header_layout.addWidget(self.label_widget)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.add_btn)
        self.layout.addLayout(self.header_layout)
        
        self.items_layout = QVBoxLayout()
        self.items_layout.setSpacing(5)
        self.layout.addLayout(self.items_layout)
        
        self.inputs = []

    def add_item(self, text=""):
        if isinstance(text, bool) or text is None:
            text = ""
        text = str(text)
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


class NoScrollComboBox(QComboBox):
    """自訂 QComboBox：點開選單清單時啟用滾輪選取項目，未點開時鎖定滾輪避免頁面滑動時誤觸"""
    def wheelEvent(self, event):
        if self.view() and self.view().isVisible():
            super().wheelEvent(event)
        else:
            event.ignore()


class EnhancedPlainTextEdit(QPlainTextEdit):
    """強化的文字編輯器：修復 Windows 剪貼簿 U+2029 複製空白 Bug，並提供深色中文右鍵選單"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_custom_context_menu)

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Copy):
            self.copy_selected_text()
            event.accept()
        elif event.matches(QKeySequence.Cut):
            self.cut_selected_text()
            event.accept()
        else:
            super().keyPressEvent(event)

    def copy_selected_text(self):
        cursor = self.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            # 關鍵修復：將 Qt 特有段落分隔符 \u2029 轉譯為標準 Windows 換行符 \r\n
            clean_text = selected_text.replace('\u2029', '\r\n').replace('\u2028', '\n')
            QApplication.clipboard().setText(clean_text)

    def cut_selected_text(self):
        cursor = self.textCursor()
        if cursor.hasSelection():
            self.copy_selected_text()
            if not self.isReadOnly():
                cursor.removeSelectedText()

    def copy_full_text(self):
        full_text = self.toPlainText()
        if full_text:
            clean_text = full_text.replace('\u2029', '\r\n').replace('\u2028', '\n')
            QApplication.clipboard().setText(clean_text)

    def show_custom_context_menu(self, position):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #22222b;
                color: #e2e2e9;
                border: 1px solid #3a3a4c;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #e5a93b;
                color: #1a1a20;
                font-weight: bold;
            }
            QMenu::item:disabled {
                color: #555566;
            }
            QMenu::separator {
                height: 1px;
                background: #2e2e3a;
                margin: 4px 0px;
            }
        """)

        cursor = self.textCursor()
        has_selection = cursor.hasSelection()
        is_read_only = self.isReadOnly()

        copy_action = menu.addAction("📋 複製 (Ctrl+C)")
        copy_action.setEnabled(has_selection)
        copy_action.triggered.connect(self.copy_selected_text)

        cut_action = menu.addAction("✂️ 剪下 (Ctrl+X)")
        cut_action.setEnabled(has_selection and not is_read_only)
        cut_action.triggered.connect(self.cut_selected_text)

        paste_action = menu.addAction("📥 貼上 (Ctrl+V)")
        clipboard_text = QApplication.clipboard().text()
        paste_action.setEnabled(bool(clipboard_text) and not is_read_only)
        paste_action.triggered.connect(self.paste)

        menu.addSeparator()

        select_all_action = menu.addAction("全選 (Ctrl+A)")
        select_all_action.triggered.connect(self.selectAll)

        copy_all_action = menu.addAction("📄 複製全文")
        copy_all_action.triggered.connect(self.copy_full_text)

        menu.exec(self.mapToGlobal(position))


class FindReplaceDialog(QDialog):
    """尋找與取代對話框"""
    def __init__(self, editor: QPlainTextEdit, parent=None):
        super().__init__(parent)
        self.editor = editor
        self.setWindowTitle("🔍 尋找與取代")
        self.setFixedSize(380, 170)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        find_layout = QHBoxLayout()
        find_layout.addWidget(QLabel("尋找目標:"))
        self.find_input = QLineEdit()
        find_layout.addWidget(self.find_input)
        layout.addLayout(find_layout)

        replace_layout = QHBoxLayout()
        replace_layout.addWidget(QLabel("取代為:"))
        self.replace_input = QLineEdit()
        replace_layout.addWidget(self.replace_input)
        layout.addLayout(replace_layout)

        btn_layout = QHBoxLayout()
        self.find_btn = QPushButton("尋找下一個")
        self.find_btn.clicked.connect(self.find_next)
        self.replace_btn = QPushButton("取代")
        self.replace_btn.clicked.connect(self.replace_one)
        self.replace_all_btn = QPushButton("全部取代")
        self.replace_all_btn.clicked.connect(self.replace_all)

        btn_layout.addWidget(self.find_btn)
        btn_layout.addWidget(self.replace_btn)
        btn_layout.addWidget(self.replace_all_btn)
        layout.addLayout(btn_layout)

    def find_next(self):
        text = self.find_input.text()
        if not text: return
        found = self.editor.find(text)
        if not found:
            cursor = self.editor.textCursor()
            cursor.movePosition(QTextCursor.Start)
            self.editor.setTextCursor(cursor)
            if not self.editor.find(text):
                QMessageBox.information(self, "尋找結束", f"找不到「{text}」")

    def replace_one(self):
        text = self.find_input.text()
        replace_text = self.replace_input.text()
        if not text: return
        cursor = self.editor.textCursor()
        if cursor.hasSelection() and cursor.selectedText() == text:
            cursor.insertText(replace_text)
        self.find_next()

    def replace_all(self):
        text = self.find_input.text()
        replace_text = self.replace_input.text()
        if not text: return
        content = self.editor.toPlainText()
        count = content.count(text)
        if count > 0:
            new_content = content.replace(text, replace_text)
            self.editor.setPlainText(new_content)
            QMessageBox.information(self, "取代完成", f"已成功取代 {count} 處「{text}」")
        else:
            QMessageBox.information(self, "尋找結束", f"找不到「{text}」")


class StandaloneTextEditorWindow(QMainWindow):
    """獨立大視窗文字編輯器：支援雙欄 Markdown 預覽、搜尋取代、即時字數統計與備份"""
    def __init__(self, title_info="獨立文字編輯器", initial_text="", on_save_callback=None, parent=None):
        super().__init__(parent)
        self.on_save_callback = on_save_callback
        self.is_syncing = False
        self.is_modified = False
        self.setWindowTitle(f"📄 [{title_info}] - 唐門山莊獨立寫作大視窗")
        self.resize(1000, 700)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # 頂部工具列
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(8)

        self.save_btn = QPushButton("💾 儲存變更 (Ctrl+S)")
        self.save_btn.setObjectName("primaryButton")
        self.save_btn.clicked.connect(self.save_content)

        self.copy_all_btn = QPushButton("📋 複製全文")
        self.copy_all_btn.clicked.connect(self.copy_full_text)

        self.find_btn = QPushButton("🔍 尋找與取代 (Ctrl+F)")
        self.find_btn.clicked.connect(self.open_find_dialog)

        self.preview_toggle_btn = QPushButton("👁️ 切換 Markdown 雙欄預覽")
        self.preview_toggle_btn.setCheckable(True)
        self.preview_toggle_btn.toggled.connect(self.toggle_preview)

        toolbar_layout.addWidget(self.save_btn)
        toolbar_layout.addWidget(self.copy_all_btn)
        toolbar_layout.addWidget(self.find_btn)
        toolbar_layout.addWidget(self.preview_toggle_btn)
        toolbar_layout.addStretch()

        main_layout.addLayout(toolbar_layout)

        # 雙欄 Splitter
        self.splitter = QSplitter(Qt.Horizontal)

        # 編輯區
        self.editor = EnhancedPlainTextEdit()
        self.editor.setPlainText(initial_text)
        self.editor.setStyleSheet("background-color: #15151c; font-family: Consolas, monospace; font-size: 14px; color: #ffffff; padding: 10px;")
        self.editor.textChanged.connect(self.on_text_changed)

        self.splitter.addWidget(self.editor)

        # 預覽區 (預設隱藏)
        self.preview_browser = QTextBrowser()
        self.preview_browser.setStyleSheet("background-color: #1a1a24; color: #e2e2e9; font-family: sans-serif; font-size: 14px; padding: 12px;")
        self.preview_browser.hide()
        self.splitter.addWidget(self.preview_browser)

        main_layout.addWidget(self.splitter)

        # 底部狀態列 (即時字數/行數統計)
        self.status_bar_label = QLabel("📊 統計: 0 字 | 1 行")
        self.status_bar_label.setStyleSheet("color: #00ff88; font-weight: bold; font-size: 12px; padding: 4px;")
        main_layout.addWidget(self.status_bar_label)

        # 定時器以實現字數統計防抖
        self.stats_timer = QTimer(self)
        self.stats_timer.setSingleShot(True)
        self.stats_timer.timeout.connect(self.update_stats)

        # 快捷鍵
        save_shortcut = QKeySequence("Ctrl+S")
        self.save_btn.setShortcut(save_shortcut)
        find_shortcut = QKeySequence("Ctrl+F")
        self.find_btn.setShortcut(find_shortcut)

        self.update_stats()

    def toggle_preview(self, checked):
        if checked:
            self.preview_browser.show()
            self.splitter.setSizes([500, 500])
            self.update_preview()
        else:
            self.preview_browser.hide()

    def update_preview(self):
        if not self.preview_toggle_btn.isChecked():
            return
        raw_text = self.editor.toPlainText()
        body_text = raw_text
        if raw_text.startswith("---") and "---" in raw_text[3:]:
            parts = raw_text.split("---", 2)
            if len(parts) >= 3:
                body_text = parts[2]

        formatted_html = html.escape(body_text)
        formatted_html = formatted_html.replace("\n", "<br>")
        formatted_html = f"<div style='color: #e2e2e9; line-height: 1.6;'>{formatted_html}</div>"
        self.preview_browser.setHtml(formatted_html)

    def on_text_changed(self):
        self.stats_timer.start(300)
        self.is_modified = True
        if self.preview_toggle_btn.isChecked():
            self.update_preview()

    def update_stats(self):
        text = self.editor.toPlainText()
        lines = text.count("\n") + 1 if text else 0
        import re
        cjk_count = len(re.findall(r'[\u4e00-\u9fff]', text))
        non_cjk_words = len(re.findall(r'[a-zA-Z0-9_]+', text))
        total_words = cjk_count + non_cjk_words
        self.status_bar_label.setText(f"📊 統計: 約 {total_words} 字 ({cjk_count} 中文字, {non_cjk_words} 單詞) | {lines} 行")

    def copy_full_text(self):
        self.editor.copy_full_text()
        QMessageBox.information(self, "複製成功", "已成功將全文複製至剪貼簿！")

    def open_find_dialog(self):
        dialog = FindReplaceDialog(self.editor, self)
        dialog.exec()

    def save_content(self):
        if callable(self.on_save_callback):
            self.on_save_callback(self.editor.toPlainText(), save_to_disk=True)
            self.is_modified = False
            now_str = datetime.datetime.now().strftime("%H:%M:%S")
            self.status_bar_label.setText(f"📊 統計中... | ✅ 已於 {now_str} 成功儲存並同步至控制台！")
            self.update_stats()

    def closeEvent(self, event):
        if getattr(self, "is_modified", False):
            reply = QMessageBox.question(
                self,
                "未儲存的變更",
                "獨立寫作視窗內尚有未儲存的修改，請問是否在關閉前儲存？\n\n【是】儲存並同步至主頁面\n【否】放棄未儲存的修改直接關閉\n【取消】返回繼續寫作",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self.save_content()
                event.accept()
            elif reply == QMessageBox.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


class PublishDialog(QDialog):
    """發布確認對話框：顯示即將變更的檔案清單與選擇/填寫 Commit Message"""
    def __init__(self, changed_files, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🚀 確認發布上線")
        self.setFixedSize(520, 430)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        title = QLabel("準備發布網站上線")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(title)
        
        # 變更檔案清單
        layout.addWidget(QLabel("即將提交的變更檔案清單:"))
        self.file_list = EnhancedPlainTextEdit()
        self.file_list.setReadOnly(True)
        self.file_list.setPlainText("\n".join(changed_files) if changed_files else "（無偵測到檔案變更）")
        self.file_list.setStyleSheet("background-color: #15151c; font-family: Consolas; color: #a2a2ab;")
        layout.addWidget(self.file_list)
        
        # Commit Message (下拉選單選取 + 可自由打字微調)
        layout.addWidget(QLabel("選擇或填寫本次提交訊息 (Commit Message):"))
        self.msg_edit = NoScrollComboBox()
        self.msg_edit.setEditable(True)
        
        import datetime
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        
        commit_templates = [
            f"chore: 網站例行小更新 ({today_str})",
            f"feat: 新增小說內容與章節 ({today_str})",
            f"fix: 修正文字錯字與人物設定 ({today_str})",
            f"style: 調整排版與介面樣式 ({today_str})",
            f"docs: 更新藏書閣/門派檔案 ({today_str})",
            f"refactor: 程式碼與架構重構 ({today_str})"
        ]
        
        self.msg_edit.addItems(commit_templates)
        self.msg_edit.setStyleSheet("""
            QComboBox {
                background-color: #22222b;
                color: #00ff88;
                border: 1px solid #3a3a4c;
                border-radius: 6px;
                padding: 6px 10px;
                font-weight: bold;
            }
            QComboBox QAbstractItemView {
                background-color: #22222b;
                color: #e2e2e9;
                selection-background-color: #005533;
                selection-color: #00ff88;
            }
        """)
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

    def get_commit_message(self) -> str:
        """取得最終輸入的 commit 訊息"""
        return self.msg_edit.currentText().strip()



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("github個人網站綜合管理控制台")
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
                    self.custom_novels = cfg.get("customNovels", [])
                    self.custom_factions = cfg.get("customFactions", [])
                    self.layout_orientation = cfg.get("layoutOrientation", "horizontal")
                    self.layout_sizes = cfg.get("layoutSizes", [650, 450])
            except Exception as e:
                self.log(f"⚠️ 載入設定檔失敗: {e}")

    def save_config(self):
        config_path = os.path.join(self.project_dir, "sync-config.json")
        try:
            cfg = {}
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
            cfg["workspacePath"] = self.workspace_dir
            cfg["customNovels"] = getattr(self, "custom_novels", [])
            cfg["customFactions"] = getattr(self, "custom_factions", [])
            cfg["layoutOrientation"] = getattr(self, "layout_orientation", "horizontal")
            cfg["layoutSizes"] = getattr(self, "layout_sizes", [650, 450])
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f"⚠️ 寫入 sync-config.json 失敗: {e}")

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
        
        shanzhuang_title = QLabel("晚餐晚餐")
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
        
        # 2. 右側主要內容區（採用 Splitter 分割「多功能分頁」與「控制台日誌」）
        orientation = Qt.Horizontal if getattr(self, "layout_orientation", "horizontal") == "horizontal" else Qt.Vertical
        self.right_splitter = QSplitter(orientation)
        
        # 建立多功能頁籤分頁
        self.main_tab_widget = QTabWidget()
        
        tab1_panel = self.setup_tab1_panel()
        self.main_tab_widget.addTab(tab1_panel, "📥 待處理檔案匯入")
        
        tab2_panel = self.setup_tab2_panel()
        self.main_tab_widget.addTab(tab2_panel, "📚 網站既有文章管理")
        
        tab3_panel = self.setup_novel_publisher_panel()
        self.main_tab_widget.addTab(tab3_panel, "📖 小說極速連載工作台")
        
        self.right_splitter.addWidget(self.main_tab_widget)
        
        # 下半部（現為右側）：日誌與控制台輸出面板 (支援一鍵折疊)
        self.console_panel = QFrame()
        self.console_panel.setObjectName("cardFrame")
        console_layout = QVBoxLayout(self.console_panel)
        console_layout.setContentsMargins(12, 8, 12, 8)
        console_layout.setSpacing(6)
        
        console_title_layout = QHBoxLayout()
        lbl_console = QLabel("📋 控制台即時日誌:")
        lbl_console.setStyleSheet("color: #e5a93b; font-weight: bold; font-size: 12px;")
        console_title_layout.addWidget(lbl_console)
        
        console_title_layout.addStretch()
        
        self.toggle_layout_btn = QPushButton("↔️ 左右並排")
        self.toggle_layout_btn.setFixedWidth(90)
        self.toggle_layout_btn.setStyleSheet("font-size: 11px; padding: 3px;")
        self.toggle_layout_btn.clicked.connect(self.toggle_console_layout)
        console_title_layout.addWidget(self.toggle_layout_btn)

        self.btn_collapse_console = QPushButton("🔽 收折日誌")
        self.btn_collapse_console.setFixedWidth(80)
        self.btn_collapse_console.setStyleSheet("font-size: 11px; padding: 3px; background-color: #2b2b38;")
        self.btn_collapse_console.clicked.connect(self.toggle_console_panel)
        console_title_layout.addWidget(self.btn_collapse_console)

        clear_log_btn = QPushButton("清除")
        clear_log_btn.setFixedWidth(50)
        clear_log_btn.setStyleSheet("font-size: 11px; padding: 3px;")
        clear_log_btn.clicked.connect(self.clear_logs)
        console_title_layout.addWidget(clear_log_btn)
        console_layout.addLayout(console_title_layout)
        
        self.console_log = EnhancedPlainTextEdit()
        self.console_log.setReadOnly(True)
        self.console_log.setStyleSheet("background-color: #121216; font-family: Consolas, monospace; font-size: 12px; color: #a2a2ab; border: 1px solid #1c1c24;")
        console_layout.addWidget(self.console_log)
        
        self.right_splitter.addWidget(self.console_panel)
        
        # 設定分割器初始權重大小與持久化配置
        initial_sizes = getattr(self, "layout_sizes", [650, 450])
        self.right_splitter.setSizes(initial_sizes)
        self.toggle_layout_btn.setText("↔️ 左右並排" if orientation == Qt.Horizontal else "↕️ 上下分割")
        main_layout.addWidget(self.right_splitter)
        
        # 保存動態生成的欄位控制件對照表
        self.dynamic_widgets = {}
        self.tab2_dynamic_widgets = {}

    def toggle_console_panel(self):
        if not self.console_panel.isHidden():
            self.console_panel.hide()
            self.btn_collapse_console.setText("📋 展開日誌")
        else:
            self.console_panel.show()
            self.btn_collapse_console.setText("🔽 收折日誌")
            self.right_splitter.setSizes(getattr(self, "layout_sizes", [650, 450]))

    def toggle_console_layout(self):
        if self.right_splitter.orientation() == Qt.Horizontal:
            self.right_splitter.setOrientation(Qt.Vertical)
            self.right_splitter.setSizes([500, 250])
            self.toggle_layout_btn.setText("↕️ 上下分割")
            self.layout_orientation = "vertical"
        else:
            self.right_splitter.setOrientation(Qt.Horizontal)
            self.right_splitter.setSizes([650, 450])
            self.toggle_layout_btn.setText("↔️ 左右並排")
            self.layout_orientation = "horizontal"
        self.layout_sizes = self.right_splitter.sizes()
        self.save_config()

    def closeEvent(self, event):
        try:
            self.layout_orientation = "horizontal" if self.right_splitter.orientation() == Qt.Horizontal else "vertical"
            self.layout_sizes = self.right_splitter.sizes()
            self.save_config()
        except Exception:
            pass
        super().closeEvent(event)
        
        # 保存動態生成的欄位控制件對照表
        self.dynamic_widgets = {}
        self.tab2_dynamic_widgets = {}

    def setup_tab1_panel(self):
        tab1_panel = QFrame()
        tab1_panel.setObjectName("cardFrame")
        tab1_layout = QVBoxLayout(tab1_panel)
        tab1_layout.setContentsMargins(0, 0, 0, 0)
        tab1_layout.setSpacing(0)
        
        # 狀態控制變數
        self.is_tab1_loading = False
        self.is_tab1_dirty = False
        self.tab1_current_filepath = None
        self.tab1_current_font_size = 15
        
        # 60 秒無感自動儲存計時器 (草稿)
        self.tab1_autosave_timer = QTimer(self)
        self.tab1_autosave_timer.setSingleShot(True)
        self.tab1_autosave_timer.timeout.connect(self.auto_save_tab1_file)
        
        # 三欄式主分割器 (QSplitter)
        self.tab1_splitter = QSplitter(Qt.Horizontal)
        self.tab1_splitter.setChildrenCollapsible(False)
        
        # ----------------------------------------------------
        # 欄 1：左側待處理文字檔清單 (220px)
        # ----------------------------------------------------
        list_container = QWidget()
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(8, 8, 8, 8)
        list_layout.setSpacing(6)
        
        title_box = QHBoxLayout()
        title_box.addWidget(QLabel("待處理文字檔:"))
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedWidth(28)
        refresh_btn.clicked.connect(self.refresh_file_list)
        title_box.addWidget(refresh_btn)
        list_layout.addLayout(title_box)
        
        self.tab1_search_input = QLineEdit()
        self.tab1_search_input.setPlaceholderText("🔍 搜尋待處理檔案...")
        self.tab1_search_input.textChanged.connect(self.filter_tab1_files)
        list_layout.addWidget(self.tab1_search_input)
        
        self.file_list_widget = QListWidget()
        self.file_list_widget.currentItemChanged.connect(self.on_tab1_file_item_changed)
        list_layout.addWidget(self.file_list_widget)
        
        list_container.setMinimumWidth(180)
        list_container.setMaximumWidth(280)
        self.tab1_splitter.addWidget(list_container)
        
        # ----------------------------------------------------
        # 欄 2：中欄匯入屬性面板 (可一鍵收折，280px)
        # ----------------------------------------------------
        self.tab1_prop_panel = QFrame()
        self.tab1_prop_panel.setObjectName("cardFrame")
        self.tab1_prop_panel.setStyleSheet("background-color: #1e1e26; border-right: 1px solid #2b2b38;")
        prop_main_layout = QVBoxLayout(self.tab1_prop_panel)
        prop_main_layout.setContentsMargins(8, 8, 8, 8)
        prop_main_layout.setSpacing(6)
        
        prop_header = QHBoxLayout()
        lbl_prop_title = QLabel("⚙️ 匯入屬性設定")
        lbl_prop_title.setStyleSheet("color: #e5a93b; font-weight: bold; font-size: 12px;")
        prop_header.addWidget(lbl_prop_title)
        prop_header.addStretch()
        
        btn_collapse_prop = QPushButton("◀ 收折屬性")
        btn_collapse_prop.setFixedHeight(24)
        btn_collapse_prop.setStyleSheet("font-size: 11px; padding: 2px 6px; background-color: #2b2b38;")
        btn_collapse_prop.clicked.connect(self.toggle_tab1_prop_panel)
        prop_header.addWidget(btn_collapse_prop)
        prop_main_layout.addLayout(prop_header)
        
        # 分區選擇
        col_select_box = QHBoxLayout()
        col_select_box.addWidget(QLabel("分區:"))
        self.collection_combo = NoScrollComboBox()
        for col_name, col_info in self.schema.items():
            self.collection_combo.addItem(col_info["label"], col_name)
        self.collection_combo.currentIndexChanged.connect(self.on_collection_changed)
        col_select_box.addWidget(self.collection_combo)
        prop_main_layout.addLayout(col_select_box)
        
        # 動態屬性欄位 ScrollArea
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: transparent; border: none;")
        self.scroll_widget = QWidget()
        self.scroll_widget.setStyleSheet("background-color: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setSpacing(10)
        self.scroll_layout.setContentsMargins(2, 4, 2, 4)
        self.scroll_area.setWidget(self.scroll_widget)
        prop_main_layout.addWidget(self.scroll_area)
        
        self.tab1_prop_panel.setMinimumWidth(220)
        self.tab1_prop_panel.setMaximumWidth(360)
        self.tab1_splitter.addWidget(self.tab1_prop_panel)
        
        # ----------------------------------------------------
        # 欄 3：右側待處理純文字大稿紙編輯區 (佔滿剩餘所有空間)
        # ----------------------------------------------------
        self.tab1_editor_panel = QFrame()
        self.tab1_editor_panel.setStyleSheet("background-color: #14141a;")
        editor_panel_layout = QVBoxLayout(self.tab1_editor_panel)
        editor_panel_layout.setContentsMargins(12, 8, 12, 8)
        editor_panel_layout.setSpacing(8)
        
        # 編輯器頂部工具列
        editor_top_bar = QHBoxLayout()
        
        self.tab1_btn_expand_prop = QPushButton("▶ 展開屬性")
        self.tab1_btn_expand_prop.setFixedHeight(26)
        self.tab1_btn_expand_prop.setStyleSheet("font-size: 11px; padding: 2px 8px; background-color: #282836;")
        self.tab1_btn_expand_prop.clicked.connect(self.toggle_tab1_prop_panel)
        self.tab1_btn_expand_prop.hide()
        editor_top_bar.addWidget(self.tab1_btn_expand_prop)
        
        self.tab1_file_lbl = QLabel("請選擇左側待處理文字檔以開啟編輯")
        self.tab1_file_lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.tab1_file_lbl.setStyleSheet("color: #f0f0f5;")
        editor_top_bar.addWidget(self.tab1_file_lbl)
        
        editor_top_bar.addStretch()
        
        # 字級縮放按鈕組
        btn_font_minus = QPushButton("A-")
        btn_font_minus.setFixedSize(28, 26)
        btn_font_minus.setToolTip("縮小字級")
        btn_font_minus.clicked.connect(lambda: self.change_tab1_font_size(-1))
        editor_top_bar.addWidget(btn_font_minus)
        
        self.tab1_lbl_font_size = QLabel(f"{self.tab1_current_font_size}px")
        self.tab1_lbl_font_size.setStyleSheet("color: #a2a2ab; font-size: 11px; margin: 0 4px;")
        editor_top_bar.addWidget(self.tab1_lbl_font_size)
        
        btn_font_plus = QPushButton("A+")
        btn_font_plus.setFixedSize(28, 26)
        btn_font_plus.setToolTip("放大字級")
        btn_font_plus.clicked.connect(lambda: self.change_tab1_font_size(1))
        editor_top_bar.addWidget(btn_font_plus)
        
        btn_font_reset = QPushButton("↺")
        btn_font_reset.setFixedSize(28, 26)
        btn_font_reset.setToolTip("重置為預設 15px")
        btn_font_reset.clicked.connect(self.reset_tab1_font_size)
        editor_top_bar.addWidget(btn_font_reset)
        
        # 儲存狀態指示燈
        self.tab1_save_status_lbl = QLabel("● 尚未選擇檔案")
        self.tab1_save_status_lbl.setStyleSheet("color: #6edb8f; font-size: 11px; margin-left: 8px; margin-right: 6px;")
        editor_top_bar.addWidget(self.tab1_save_status_lbl)
        
        # 儲存草稿按鈕
        self.tab1_save_draft_btn = QPushButton("💾 儲存草稿 (Ctrl+S)")
        self.tab1_save_draft_btn.setFixedHeight(28)
        self.tab1_save_draft_btn.setStyleSheet("background-color: #2b3b48; color: #e2e2ee; font-size: 11px; padding: 4px 10px;")
        self.tab1_save_draft_btn.clicked.connect(lambda: self.save_pending_file(silent=False))
        editor_top_bar.addWidget(self.tab1_save_draft_btn)
        
        # 匯入按鈕
        self.import_btn = QPushButton("📥 匯入個人網站")
        self.import_btn.setObjectName("primaryButton")
        self.import_btn.setFixedHeight(28)
        self.import_btn.clicked.connect(self.import_selected_file)
        editor_top_bar.addWidget(self.import_btn)
        
        editor_panel_layout.addLayout(editor_top_bar)
        
        # 正文編輯框 (文字靠左佔滿右邊區塊)
        self.tab1_body_edit = EnhancedPlainTextEdit()
        self.tab1_body_edit.textChanged.connect(self.on_tab1_text_changed)
        self.tab1_body_edit.cursorPositionChanged.connect(self.update_tab1_cursor_pos)
        self.apply_tab1_editor_style()
        editor_panel_layout.addWidget(self.tab1_body_edit, 1)
        
        # 編輯器底部微型狀態列
        tab1_bottom_bar = QHBoxLayout()
        tab1_bottom_bar.setContentsMargins(4, 2, 4, 2)
        
        self.tab1_lbl_char_count = QLabel("字數: 0 字")
        self.tab1_lbl_char_count.setStyleSheet("color: #8c8c9e; font-size: 11px;")
        self.tab1_lbl_para_count = QLabel("段落: 0")
        self.tab1_lbl_para_count.setStyleSheet("color: #8c8c9e; font-size: 11px;")
        self.tab1_lbl_cursor_pos = QLabel("行 1, 欄 1")
        self.tab1_lbl_cursor_pos.setStyleSheet("color: #8c8c9e; font-size: 11px;")
        self.tab1_lbl_autosave_hint = QLabel("⏱️ 停頓 60 秒自動存檔")
        self.tab1_lbl_autosave_hint.setStyleSheet("color: #6a6a7c; font-size: 11px;")
        
        tab1_bottom_bar.addWidget(self.tab1_lbl_char_count)
        tab1_bottom_bar.addWidget(QLabel("<span style='color:#3a3a48;'> | </span>"))
        tab1_bottom_bar.addWidget(self.tab1_lbl_para_count)
        tab1_bottom_bar.addWidget(QLabel("<span style='color:#3a3a48;'> | </span>"))
        tab1_bottom_bar.addWidget(self.tab1_lbl_cursor_pos)
        tab1_bottom_bar.addStretch()
        tab1_bottom_bar.addWidget(self.tab1_lbl_autosave_hint)
        
        editor_panel_layout.addLayout(tab1_bottom_bar)
        
        self.tab1_editor_panel.setMinimumWidth(380)
        self.tab1_splitter.addWidget(self.tab1_editor_panel)
        
        # 預設三欄分割權重 (200px : 260px : 740px)
        self.tab1_splitter.setSizes([200, 260, 740])
        tab1_layout.addWidget(self.tab1_splitter)
        
        return tab1_panel

    def toggle_tab1_prop_panel(self):
        if not self.tab1_prop_panel.isHidden():
            self.tab1_prop_panel.hide()
            self.tab1_btn_expand_prop.show()
        else:
            self.tab1_prop_panel.show()
            self.tab1_btn_expand_prop.hide()

    def change_tab1_font_size(self, delta):
        new_size = max(12, min(28, self.tab1_current_font_size + delta))
        if new_size != self.tab1_current_font_size:
            self.tab1_current_font_size = new_size
            self.tab1_lbl_font_size.setText(f"{new_size}px")
            self.apply_tab1_editor_style()

    def reset_tab1_font_size(self):
        self.tab1_current_font_size = 15
        self.tab1_lbl_font_size.setText("15px")
        self.apply_tab1_editor_style()

    def apply_tab1_editor_style(self):
        style = f"""
        QPlainTextEdit {{
            background-color: #16161e;
            border: 1px solid #242430;
            border-radius: 6px;
            padding: 16px 20px;
            color: #f0f0f8;
            font-family: 'Segoe UI', 'Microsoft JhengHei', 'PingFang TC', sans-serif;
            font-size: {self.tab1_current_font_size}px;
            line-height: 1.6;
            selection-background-color: #4a3a20;
            selection-color: #ffd980;
        }}
        QPlainTextEdit:focus {{
            border: 1px solid #e5a93b;
            background-color: #181822;
        }}
        """
        self.tab1_body_edit.setStyleSheet(style)

    def filter_tab1_files(self, text):
        keyword = text.strip().lower()
        for i in range(self.file_list_widget.count()):
            item = self.file_list_widget.item(i)
            item.setHidden(keyword not in item.text().lower())

    def on_tab1_file_item_changed(self, current, previous):
        if previous and self.is_tab1_dirty:
            ret = QMessageBox.question(
                self,
                "未儲存草稿確認",
                "當前待處理檔案內容已修改但尚未儲存草稿，是否立即儲存？",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            if ret == QMessageBox.Save:
                self.save_pending_file(silent=True)
            elif ret == QMessageBox.Cancel:
                self.file_list_widget.blockSignals(True)
                self.file_list_widget.setCurrentItem(previous)
                self.file_list_widget.blockSignals(False)
                return
        
        if not current:
            return
        
        filename = current.text()
        filepath = os.path.join(self.workspace_dir, filename)
        self.load_tab1_file(filepath)

    def load_tab1_file(self, filepath):
        if not filepath or not os.path.exists(filepath):
            return
        
        self.is_tab1_loading = True
        self.tab1_autosave_timer.stop()
        self.tab1_current_filepath = filepath
        
        filename = os.path.basename(filepath)
        self.tab1_file_lbl.setText(f"📄  {filename}")
        
        fm, body = self.parse_frontmatter(filepath)
        base_title = os.path.splitext(filename)[0]
        if "title" not in fm or not fm["title"]:
            fm["title"] = base_title
        if "name" not in fm or not fm["name"]:
            fm["name"] = base_title
            
        self.populate_form(fm, body, filepath)
        self.tab1_body_edit.setPlainText(body)
        
        self.is_tab1_loading = False
        self.is_tab1_dirty = False
        
        self.tab1_save_status_lbl.setText("● 已同步最新內容")
        self.tab1_save_status_lbl.setStyleSheet("color: #6edb8f; font-size: 11px; margin-left: 8px; margin-right: 6px;")
        self.update_tab1_statistics()

    def mark_tab1_dirty(self):
        if self.is_tab1_loading:
            return
        self.is_tab1_dirty = True
        self.tab1_save_status_lbl.setText("● 編輯中 (未儲存草稿)")
        self.tab1_save_status_lbl.setStyleSheet("color: #e5a93b; font-size: 11px; margin-left: 8px; margin-right: 6px;")
        self.tab1_autosave_timer.start(60000)

    def on_tab1_text_changed(self):
        if self.is_tab1_loading:
            return
        self.mark_tab1_dirty()
        self.update_tab1_statistics()

    def update_tab1_statistics(self):
        text = self.tab1_body_edit.toPlainText()
        char_count = len(text.replace(" ", "").replace("\n", "").replace("\r", ""))
        lines = text.splitlines()
        para_count = len([line for line in lines if line.strip()])
        
        self.tab1_lbl_char_count.setText(f"字數: {char_count} 字")
        self.tab1_lbl_para_count.setText(f"段落: {para_count}")

    def update_tab1_cursor_pos(self):
        cursor = self.tab1_body_edit.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        self.tab1_lbl_cursor_pos.setText(f"行 {line}, 欄 {col}")

    def auto_save_tab1_file(self):
        if self.is_tab1_dirty and self.tab1_current_filepath:
            self.save_pending_file(silent=True)
            now_str = datetime.datetime.now().strftime("%H:%M:%S")
            self.tab1_save_status_lbl.setText(f"✓ 60秒自動存檔 ({now_str})")
            self.tab1_save_status_lbl.setStyleSheet("color: #6edb8f; font-size: 11px; margin-left: 8px; margin-right: 6px;")

    def setup_tab2_panel(self):
        tab2_panel = QFrame()
        tab2_panel.setObjectName("cardFrame")
        tab2_layout = QVBoxLayout(tab2_panel)
        tab2_layout.setContentsMargins(0, 0, 0, 0)
        tab2_layout.setSpacing(0)
        
        # 狀態控制變數
        self.is_tab2_loading = False
        self.is_tab2_dirty = False
        self.tab2_current_filepath = None
        self.tab2_current_font_size = 15
        
        # 60 秒無感自動儲存計時器
        self.tab2_autosave_timer = QTimer(self)
        self.tab2_autosave_timer.setSingleShot(True)
        self.tab2_autosave_timer.timeout.connect(self.auto_save_tab2_article)
        
        # 三欄式主分割器 (QSplitter)
        self.tab2_splitter = QSplitter(Qt.Horizontal)
        self.tab2_splitter.setChildrenCollapsible(False)
        
        # ----------------------------------------------------
        # 欄 1：左側分區與檔案清單 (220px)
        # ----------------------------------------------------
        list_container = QWidget()
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(8, 8, 8, 8)
        list_layout.setSpacing(6)
        
        col_select_layout = QHBoxLayout()
        col_select_layout.addWidget(QLabel("分區:"))
        self.tab2_col_combo = NoScrollComboBox()
        for col_name, col_info in self.schema.items():
            self.tab2_col_combo.addItem(col_info["label"], col_name)
        self.tab2_col_combo.currentIndexChanged.connect(self.refresh_tab2_file_list)
        col_select_layout.addWidget(self.tab2_col_combo)
        
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedWidth(28)
        refresh_btn.clicked.connect(self.refresh_tab2_file_list)
        col_select_layout.addWidget(refresh_btn)
        list_layout.addLayout(col_select_layout)
        
        self.tab2_search_input = QLineEdit()
        self.tab2_search_input.setPlaceholderText("🔍 搜尋檔案...")
        self.tab2_search_input.textChanged.connect(self.filter_tab2_files)
        list_layout.addWidget(self.tab2_search_input)
        
        self.tab2_file_list_widget = QListWidget()
        self.tab2_file_list_widget.currentItemChanged.connect(self.on_tab2_file_item_changed)
        list_layout.addWidget(self.tab2_file_list_widget)
        
        list_container.setMinimumWidth(180)
        list_container.setMaximumWidth(280)
        self.tab2_splitter.addWidget(list_container)
        
        # ----------------------------------------------------
        # 欄 2：中欄屬性面板 (可一鍵收折，280px)
        # ----------------------------------------------------
        self.tab2_prop_panel = QFrame()
        self.tab2_prop_panel.setObjectName("cardFrame")
        self.tab2_prop_panel.setStyleSheet("background-color: #1e1e26; border-right: 1px solid #2b2b38;")
        prop_main_layout = QVBoxLayout(self.tab2_prop_panel)
        prop_main_layout.setContentsMargins(8, 8, 8, 8)
        prop_main_layout.setSpacing(6)
        
        prop_header = QHBoxLayout()
        lbl_prop_title = QLabel("⚙️ 屬性設定")
        lbl_prop_title.setStyleSheet("color: #e5a93b; font-weight: bold; font-size: 12px;")
        prop_header.addWidget(lbl_prop_title)
        prop_header.addStretch()
        
        btn_collapse_prop = QPushButton("◀ 收折屬性")
        btn_collapse_prop.setFixedHeight(24)
        btn_collapse_prop.setStyleSheet("font-size: 11px; padding: 2px 6px; background-color: #2b2b38;")
        btn_collapse_prop.clicked.connect(self.toggle_tab2_prop_panel)
        prop_header.addWidget(btn_collapse_prop)
        prop_main_layout.addLayout(prop_header)
        
        self.tab2_scroll_area = QScrollArea()
        self.tab2_scroll_area.setWidgetResizable(True)
        self.tab2_scroll_area.setStyleSheet("background-color: transparent; border: none;")
        self.tab2_scroll_widget = QWidget()
        self.tab2_scroll_widget.setStyleSheet("background-color: transparent;")
        self.tab2_scroll_layout = QVBoxLayout(self.tab2_scroll_widget)
        self.tab2_scroll_layout.setSpacing(10)
        self.tab2_scroll_layout.setContentsMargins(2, 4, 2, 4)
        self.tab2_scroll_area.setWidget(self.tab2_scroll_widget)
        prop_main_layout.addWidget(self.tab2_scroll_area)
        
        self.tab2_prop_panel.setMinimumWidth(220)
        self.tab2_prop_panel.setMaximumWidth(360)
        self.tab2_splitter.addWidget(self.tab2_prop_panel)
        
        # ----------------------------------------------------
        # 欄 3：右側沉浸式純文字大稿紙編輯區 (佔滿剩餘所有空間)
        # ----------------------------------------------------
        self.tab2_editor_panel = QFrame()
        self.tab2_editor_panel.setStyleSheet("background-color: #14141a;")
        editor_panel_layout = QVBoxLayout(self.tab2_editor_panel)
        editor_panel_layout.setContentsMargins(12, 8, 12, 8)
        editor_panel_layout.setSpacing(8)
        
        # 編輯器頂部工具列
        editor_top_bar = QHBoxLayout()
        
        self.tab2_btn_expand_prop = QPushButton("▶ 展開屬性")
        self.tab2_btn_expand_prop.setFixedHeight(26)
        self.tab2_btn_expand_prop.setStyleSheet("font-size: 11px; padding: 2px 8px; background-color: #282836;")
        self.tab2_btn_expand_prop.clicked.connect(self.toggle_tab2_prop_panel)
        self.tab2_btn_expand_prop.hide()
        editor_top_bar.addWidget(self.tab2_btn_expand_prop)
        
        self.tab2_file_lbl = QLabel("請選擇左側文章以開啟編輯")
        self.tab2_file_lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.tab2_file_lbl.setStyleSheet("color: #f0f0f5;")
        editor_top_bar.addWidget(self.tab2_file_lbl)
        
        editor_top_bar.addStretch()
        
        # 字級縮放按鈕組
        btn_font_minus = QPushButton("A-")
        btn_font_minus.setFixedSize(28, 26)
        btn_font_minus.setToolTip("縮小字級")
        btn_font_minus.clicked.connect(lambda: self.change_tab2_font_size(-1))
        editor_top_bar.addWidget(btn_font_minus)
        
        self.tab2_lbl_font_size = QLabel(f"{self.tab2_current_font_size}px")
        self.tab2_lbl_font_size.setStyleSheet("color: #a2a2ab; font-size: 11px; margin: 0 4px;")
        editor_top_bar.addWidget(self.tab2_lbl_font_size)
        
        btn_font_plus = QPushButton("A+")
        btn_font_plus.setFixedSize(28, 26)
        btn_font_plus.setToolTip("放大字級")
        btn_font_plus.clicked.connect(lambda: self.change_tab2_font_size(1))
        editor_top_bar.addWidget(btn_font_plus)
        
        btn_font_reset = QPushButton("↺")
        btn_font_reset.setFixedSize(28, 26)
        btn_font_reset.setToolTip("重置為預設 15px")
        btn_font_reset.clicked.connect(self.reset_tab2_font_size)
        editor_top_bar.addWidget(btn_font_reset)
        
        # 儲存狀態指示燈
        self.tab2_save_status_lbl = QLabel("● 尚未選擇檔案")
        self.tab2_save_status_lbl.setStyleSheet("color: #6edb8f; font-size: 11px; margin-left: 10px; margin-right: 8px;")
        editor_top_bar.addWidget(self.tab2_save_status_lbl)
        
        # 儲存按鈕
        self.tab2_save_btn = QPushButton("💾 儲存修訂 (Ctrl+S)")
        self.tab2_save_btn.setObjectName("primaryButton")
        self.tab2_save_btn.setFixedHeight(28)
        self.tab2_save_btn.clicked.connect(lambda: self.save_tab2_article(silent=False))
        editor_top_bar.addWidget(self.tab2_save_btn)
        
        editor_panel_layout.addLayout(editor_top_bar)
        
        # 正文編輯框 (文字靠左佔滿右邊區塊)
        self.tab2_body_edit = EnhancedPlainTextEdit()
        self.tab2_body_edit.textChanged.connect(self.on_tab2_text_changed)
        self.tab2_body_edit.cursorPositionChanged.connect(self.update_tab2_cursor_pos)
        self.apply_tab2_editor_style()
        editor_panel_layout.addWidget(self.tab2_body_edit, 1)
        
        # 編輯器底部微型狀態列
        tab2_bottom_bar = QHBoxLayout()
        tab2_bottom_bar.setContentsMargins(4, 2, 4, 2)
        
        self.tab2_lbl_char_count = QLabel("字數: 0 字")
        self.tab2_lbl_char_count.setStyleSheet("color: #8c8c9e; font-size: 11px;")
        self.tab2_lbl_para_count = QLabel("段落: 0")
        self.tab2_lbl_para_count.setStyleSheet("color: #8c8c9e; font-size: 11px;")
        self.tab2_lbl_cursor_pos = QLabel("行 1, 欄 1")
        self.tab2_lbl_cursor_pos.setStyleSheet("color: #8c8c9e; font-size: 11px;")
        self.tab2_lbl_autosave_hint = QLabel("⏱️ 停頓 60 秒自動存檔")
        self.tab2_lbl_autosave_hint.setStyleSheet("color: #6a6a7c; font-size: 11px;")
        
        tab2_bottom_bar.addWidget(self.tab2_lbl_char_count)
        tab2_bottom_bar.addWidget(QLabel("<span style='color:#3a3a48;'> | </span>"))
        tab2_bottom_bar.addWidget(self.tab2_lbl_para_count)
        tab2_bottom_bar.addWidget(QLabel("<span style='color:#3a3a48;'> | </span>"))
        tab2_bottom_bar.addWidget(self.tab2_lbl_cursor_pos)
        tab2_bottom_bar.addStretch()
        tab2_bottom_bar.addWidget(self.tab2_lbl_autosave_hint)
        
        editor_panel_layout.addLayout(tab2_bottom_bar)
        
        self.tab2_editor_panel.setMinimumWidth(380)
        self.tab2_splitter.addWidget(self.tab2_editor_panel)
        
        # 預設三欄分割權重 (200px : 260px : 740px)
        self.tab2_splitter.setSizes([200, 260, 740])
        tab2_layout.addWidget(self.tab2_splitter)
        
        # 初始化載入首個分區之檔案清單
        QTimer.singleShot(200, self.refresh_tab2_file_list)
        
        return tab2_panel

    def toggle_tab2_prop_panel(self):
        if not self.tab2_prop_panel.isHidden():
            self.tab2_prop_panel.hide()
            self.tab2_btn_expand_prop.show()
        else:
            self.tab2_prop_panel.show()
            self.tab2_btn_expand_prop.hide()

    def change_tab2_font_size(self, delta):
        new_size = max(12, min(28, self.tab2_current_font_size + delta))
        if new_size != self.tab2_current_font_size:
            self.tab2_current_font_size = new_size
            self.tab2_lbl_font_size.setText(f"{new_size}px")
            self.apply_tab2_editor_style()

    def reset_tab2_font_size(self):
        self.tab2_current_font_size = 15
        self.tab2_lbl_font_size.setText("15px")
        self.apply_tab2_editor_style()

    def apply_tab2_editor_style(self):
        style = f"""
        QPlainTextEdit {{
            background-color: #16161e;
            border: 1px solid #242430;
            border-radius: 6px;
            padding: 16px 20px;
            color: #f0f0f8;
            font-family: 'Segoe UI', 'Microsoft JhengHei', 'PingFang TC', sans-serif;
            font-size: {self.tab2_current_font_size}px;
            line-height: 1.6;
            selection-background-color: #4a3a20;
            selection-color: #ffd980;
        }}
        QPlainTextEdit:focus {{
            border: 1px solid #e5a93b;
            background-color: #181822;
        }}
        """
        self.tab2_body_edit.setStyleSheet(style)

    def filter_tab2_files(self, text):
        keyword = text.strip().lower()
        for i in range(self.tab2_file_list_widget.count()):
            item = self.tab2_file_list_widget.item(i)
            item.setHidden(keyword not in item.text().lower())

    def refresh_tab2_file_list(self):
        self.tab2_file_list_widget.clear()
        col_name = self.tab2_col_combo.currentData()
        if not col_name:
            return
        col_dir = os.path.join(self.project_dir, "src", "content", col_name)
        if not os.path.exists(col_dir):
            return
        
        files = [f for f in os.listdir(col_dir) if f.endswith(".md")]
        files.sort()
        
        for f in files:
            fpath = os.path.join(col_dir, f)
            fm, _ = self.parse_frontmatter(fpath)
            title = fm.get("title") or fm.get("name") or f
            item = QListWidgetItem(f"📄 {title} ({f})")
            item.setData(Qt.UserRole, fpath)
            item.setToolTip(f"完整路徑: {fpath}")
            self.tab2_file_list_widget.addItem(item)

    def on_tab2_file_item_changed(self, current, previous):
        if previous and self.is_tab2_dirty:
            # 未存檔防呆攔截
            ret = QMessageBox.question(
                self,
                "未儲存變更確認",
                "當前文章內容已修改但尚未儲存，是否立即儲存變更？",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            if ret == QMessageBox.Save:
                self.save_tab2_article(silent=True)
            elif ret == QMessageBox.Cancel:
                # 恢復先前的選取
                self.tab2_file_list_widget.blockSignals(True)
                self.tab2_file_list_widget.setCurrentItem(previous)
                self.tab2_file_list_widget.blockSignals(False)
                return
        
        if not current:
            return
        
        filepath = current.data(Qt.UserRole)
        self.load_tab2_file(filepath)

    def load_tab2_file(self, filepath):
        if not filepath or not os.path.exists(filepath):
            return
        
        self.is_tab2_loading = True
        self.tab2_autosave_timer.stop()
        self.tab2_current_filepath = filepath
        
        # 清空中欄屬性
        for i in reversed(range(self.tab2_scroll_layout.count())):
            item = self.tab2_scroll_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
        
        self.tab2_dynamic_widgets = {}
        fm, body = self.parse_frontmatter(filepath)
        col_name = self.tab2_col_combo.currentData()
        fields = self.schema.get(col_name, {}).get("fields", {})
        
        self.tab2_file_lbl.setText(f"📄  {os.path.basename(filepath)}")
        
        for field_name, field_info in fields.items():
            field_type = field_info["type"]
            field_label = field_info["label"]
            val = fm.get(field_name, "")
            
            if field_type in ["text", "slug"]:
                if field_info.get("multiline", False):
                    lbl = QLabel(f"{field_label} ({field_name}):")
                    lbl.setStyleSheet("color: #a2a2ab; font-weight: bold; font-size: 11px;")
                    edit = EnhancedPlainTextEdit()
                    edit.setPlainText(str(val))
                    edit.setMinimumHeight(60)
                    edit.textChanged.connect(self.mark_tab2_dirty)
                    self.tab2_scroll_layout.addWidget(lbl)
                    self.tab2_scroll_layout.addWidget(edit)
                    self.tab2_dynamic_widgets[field_name] = ("text_multi", edit)
                else:
                    lbl = QLabel(f"{field_label} ({field_name}):")
                    lbl.setStyleSheet("color: #00ff88; font-weight: bold; font-size: 11px;")
                    edit = QLineEdit(str(val))
                    edit.textChanged.connect(self.mark_tab2_dirty)
                    self.tab2_scroll_layout.addWidget(lbl)
                    self.tab2_scroll_layout.addWidget(edit)
                    self.tab2_dynamic_widgets[field_name] = ("text_single", edit)
            elif field_type == "array":
                array_widget = ArrayFieldWidget(f"{field_label} ({field_name})")
                array_widget.set_values(val if isinstance(val, list) else ([val] if val else []))
                self.tab2_scroll_layout.addWidget(array_widget)
                self.tab2_dynamic_widgets[field_name] = ("array", array_widget)
            elif field_type == "select":
                lbl = QLabel(f"{field_label} ({field_name}):")
                lbl.setStyleSheet("color: #a2a2ab; font-weight: bold; font-size: 11px;")
                combo = NoScrollComboBox()
                opts = field_info.get("options", [])
                for opt in opts:
                    combo.addItem(opt["label"], opt["value"])
                idx = combo.findData(val)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
                combo.currentIndexChanged.connect(self.mark_tab2_dirty)
                self.tab2_scroll_layout.addWidget(lbl)
                self.tab2_scroll_layout.addWidget(combo)
                self.tab2_dynamic_widgets[field_name] = ("select", combo)
            else:
                lbl = QLabel(f"{field_label} ({field_name}):")
                lbl.setStyleSheet("color: #a2a2ab; font-weight: bold; font-size: 11px;")
                edit = QLineEdit(str(val))
                edit.textChanged.connect(self.mark_tab2_dirty)
                self.tab2_scroll_layout.addWidget(lbl)
                self.tab2_scroll_layout.addWidget(edit)
                self.tab2_dynamic_widgets[field_name] = (field_type, edit)
        
        self.tab2_body_edit.setPlainText(body)
        self.is_tab2_loading = False
        self.is_tab2_dirty = False
        
        self.tab2_save_status_lbl.setText("● 已同步最新內容")
        self.tab2_save_status_lbl.setStyleSheet("color: #6edb8f; font-size: 11px; margin-left: 10px; margin-right: 8px;")
        self.update_tab2_statistics()

    def mark_tab2_dirty(self):
        if self.is_tab2_loading:
            return
        self.is_tab2_dirty = True
        self.tab2_save_status_lbl.setText("● 編輯中 (未儲存)")
        self.tab2_save_status_lbl.setStyleSheet("color: #e5a93b; font-size: 11px; margin-left: 10px; margin-right: 8px;")
        self.tab2_autosave_timer.start(60000)

    def on_tab2_text_changed(self):
        if self.is_tab2_loading:
            return
        self.mark_tab2_dirty()
        self.update_tab2_statistics()

    def update_tab2_statistics(self):
        text = self.tab2_body_edit.toPlainText()
        char_count = len(text.replace(" ", "").replace("\n", "").replace("\r", ""))
        lines = text.splitlines()
        para_count = len([line for line in lines if line.strip()])
        
        self.tab2_lbl_char_count.setText(f"字數: {char_count} 字")
        self.tab2_lbl_para_count.setText(f"段落: {para_count}")

    def update_tab2_cursor_pos(self):
        cursor = self.tab2_body_edit.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        self.tab2_lbl_cursor_pos.setText(f"行 {line}, 欄 {col}")

    def auto_save_tab2_article(self):
        if self.is_tab2_dirty and self.tab2_current_filepath:
            self.save_tab2_article(silent=True)
            now_str = datetime.datetime.now().strftime("%H:%M:%S")
            self.tab2_save_status_lbl.setText(f"✓ 60秒自動存檔 ({now_str})")
            self.tab2_save_status_lbl.setStyleSheet("color: #6edb8f; font-size: 11px; margin-left: 10px; margin-right: 8px;")

    def save_tab2_article(self, silent=False):
        filepath = self.tab2_current_filepath
        if not filepath:
            items = self.tab2_file_list_widget.selectedItems()
            if items:
                filepath = items[0].data(Qt.UserRole)
        
        if not filepath or not os.path.exists(filepath):
            if not silent:
                QMessageBox.warning(self, "請選擇文章", "請先從左側列表中選擇欲修訂的文章！")
            return
        
        fm_data = {}
        for fname, (ftype, widget) in getattr(self, "tab2_dynamic_widgets", {}).items():
            if ftype == "text_single":
                fm_data[fname] = widget.text().strip()
            elif ftype == "text_multi":
                fm_data[fname] = widget.toPlainText().strip()
            elif ftype == "array":
                fm_data[fname] = widget.get_values()
            elif ftype == "select":
                fm_data[fname] = widget.currentData()
            else:
                if hasattr(widget, "text"):
                    fm_data[fname] = widget.text().strip()
        
        body_text = getattr(self, "tab2_body_edit", None)
        body_content = body_text.toPlainText() if body_text else ""
        
        lines = ["---"]
        for k, v in fm_data.items():
            if isinstance(v, list):
                if v:
                    quoted_v = [f'"{x}"' for x in v if x]
                    lines.append(f"{k}: [{', '.join(quoted_v)}]")
            elif isinstance(v, str):
                if "\n" in v:
                    lines.append(f"{k}: |")
                    for subline in v.split("\n"):
                        lines.append(f"  {subline}")
                else:
                    lines.append(f'{k}: "{v}"')
            else:
                lines.append(f"{k}: {v}")
        lines.append("---")
        lines.append("")
        lines.append(body_content)
        
        full_markdown = "\n".join(lines)
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(full_markdown)
            now_time = datetime.datetime.now().strftime("%H:%M:%S")
            self.log(f"✓ [{now_time}] 成功儲存修訂文章至網站: {os.path.basename(filepath)}")
            
            self.is_tab2_dirty = False
            self.tab2_autosave_timer.stop()
            self.tab2_save_status_lbl.setText(f"✓ 已儲存 ({now_time})")
            self.tab2_save_status_lbl.setStyleSheet("color: #6edb8f; font-size: 11px; margin-left: 10px; margin-right: 8px;")
            
            if not silent:
                subprocess.run(["node", "scripts/gui-helper.js", "--extract"], cwd=self.project_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                QMessageBox.information(self, "儲存成功", f"文章【{os.path.basename(filepath)}】已成功更新！\n系統已完成自動格式維護與同步。")
        except Exception as e:
            self.log(f"❌ 儲存修訂文章失敗: {e}")
            if not silent:
                QMessageBox.critical(self, "儲存失敗", f"儲存修訂文章時發生錯誤:\n{e}")


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
            
            sb = self.console_log.verticalScrollBar()
            is_at_bottom = sb.value() >= sb.maximum() - 25
            
            self.console_log.appendHtml(formatted_html)
            
            if is_at_bottom:
                sb.setValue(sb.maximum())

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
        target_map = {} # filename_lower/title_lower -> { path, collection, mtime, filename }
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
                        info = {
                            "filename": fname,
                            "path": fpath,
                            "collection": col,
                            "mtime": mtime
                        }
                        target_map[fname.lower()] = info
                        target_map[os.path.splitext(fname)[0].lower()] = info
                        
                        # 解析 Frontmatter 標題與名稱以進行中文比對
                        fm, _ = self.parse_frontmatter(fpath)
                        for key in ["title", "name", "slug"]:
                            if key in fm and fm[key]:
                                val = str(fm[key]).strip().lower()
                                if val:
                                    target_map[val] = info
                                    target_map[f"{val}.md"] = info

        # 同時載入 sync-config.json 中的映射對照 (來源檔名 ➔ 拼音/Slug 檔名)
        config_path = os.path.join(self.project_dir, "sync-config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    novels_map = cfg.get("novels", {})
                    for src_fname, meta in novels_map.items():
                        slug = meta.get("slug")
                        cat = meta.get("category", "")
                        if slug:
                            target_fname = f"{slug}.md" if not slug.endswith(".md") else slug
                            target_path = os.path.join(content_dir, cat, target_fname)
                            if os.path.exists(target_path):
                                info = {
                                    "filename": target_fname,
                                    "path": target_path,
                                    "collection": cat,
                                    "mtime": os.path.getmtime(target_path)
                                }
                                target_map[src_fname.lower()] = info
                                target_map[os.path.splitext(src_fname)[0].lower()] = info
            except Exception:
                pass

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
            quick_slug = base_name.lower().replace(" ", "-").replace("_", "-")
            slugified_target = f"{quick_slug}.md"
            
            # 檢查是否已存在於山莊 content 中
            matched_info = None
            clean_title = base_name.split("_")[-1].lower() if "_" in base_name else base_name.lower()
            if f.lower() in target_map:
                matched_info = target_map[f.lower()]
            elif possible_target in target_map:
                matched_info = target_map[possible_target]
            elif slugified_target in target_map:
                matched_info = target_map[slugified_target]
            elif clean_title in target_map:
                matched_info = target_map[clean_title]
            elif f"{clean_title}.md" in target_map:
                matched_info = target_map[f"{clean_title}.md"]
                
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
        
        self.save_config()
        self.log(f"✅ 工作區已成功切換並寫入設定檔: {self.workspace_dir}")
            
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
        
        # 填入表單與正文編輯器
        self.populate_form(fm, body, filepath)

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
        body = ""
        filepath = ""
        if selected:
            filename = selected[0].text()
            filepath = os.path.join(self.workspace_dir, filename)
            fm, body = self.parse_frontmatter(filepath)
        self.populate_form(fm, body, filepath)

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
                self.save_config()
            combo.addItem(clean_name, clean_name)
            combo.setCurrentText(clean_name)
            self.log(f"✅ 已成功新增作品至選單並永久儲存: {clean_name}")

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
                self.save_config()
            combo.addItem(clean_name, clean_name)
            combo.setCurrentText(clean_name)
            self.log(f"✅ 已成功新增門派至選單並永久儲存: {clean_name}")

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

    def populate_form(self, defaults={}, body="", filepath=""):
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
            
            # 專屬邏輯：小說名稱欄位 (novel / book) 升級為動態資料庫下拉選單 + ➕ 新增按鈕
            if field_name in ("novel", "book"):
                lbl = QLabel(f"{field_label} ({field_name}):")
                lbl.setStyleSheet("color: #a2a2ab; font-weight: bold;")
                
                combo_box_layout = QHBoxLayout()
                combo = NoScrollComboBox()
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
                combo = NoScrollComboBox()
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
                    edit = EnhancedPlainTextEdit()
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
                combo = NoScrollComboBox()
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

    def save_pending_file(self, filepath=None, silent=False):
        target_path = filepath or getattr(self, "tab1_current_filepath", None)
        if not target_path or not os.path.exists(target_path):
            if not silent:
                QMessageBox.warning(self, "檔案不存在", "無法定位工作區原始文字檔！")
            return
            
        body_text = getattr(self, "tab1_body_edit", None)
        body_content = body_text.toPlainText() if body_text else ""
        
        # 收集 Frontmatter
        fm_data = {}
        for fname, (ftype, widget) in self.dynamic_widgets.items():
            if ftype == "text_single":
                fm_data[fname] = widget.text().strip()
            elif ftype == "text_multi":
                fm_data[fname] = widget.toPlainText().strip()
            elif ftype == "array":
                fm_data[fname] = widget.get_values()
            elif ftype == "select":
                fm_data[fname] = widget.currentData()
            elif ftype == "combo_custom":
                fm_data[fname] = widget.currentText().strip()
            elif ftype in ["url", "image"]:
                fm_data[fname] = widget.text().strip()
                
        # 組合 YAML Frontmatter + body
        lines = ["---"]
        for k, v in fm_data.items():
            if isinstance(v, list):
                if v:
                    quoted_v = [f'"{x}"' for x in v if x]
                    lines.append(f"{k}: [{', '.join(quoted_v)}]")
            elif isinstance(v, str):
                if v:
                    lines.append(f'{k}: "{v}"')
            else:
                if v is not None and str(v):
                    lines.append(f"{k}: {v}")
        lines.append("---")
        lines.append("")
        lines.append(body_content)
        
        full_content = "\n".join(lines)
        try:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(full_content)
            
            self.is_tab1_dirty = False
            now_str = datetime.datetime.now().strftime("%H:%M:%S")
            self.tab1_save_status_lbl.setText(f"✓ 已存檔 ({now_str})")
            self.tab1_save_status_lbl.setStyleSheet("color: #6edb8f; font-size: 11px; margin-left: 8px; margin-right: 6px;")
            self.log(f"✓ 成功儲存修改至工作區原始文字檔: {os.path.basename(target_path)}")
            
            if not silent:
                QMessageBox.information(self, "儲存成功", f"檔案【{os.path.basename(target_path)}】的修改已成功儲存至工作區！")
        except Exception as e:
            self.log(f"❌ 儲存原始文字檔失敗: {e}")
            if not silent:
                QMessageBox.critical(self, "儲存失敗", f"儲存原始文字檔時發生錯誤:\n{e}")

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
            commit_msg = dialog.get_commit_message()
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

    # =========================================================================
    # 📖 小說極速連載工作台 (Fast Novel Publisher) 專屬邏輯
    # =========================================================================
    def setup_novel_publisher_panel(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a20;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(14)

        # 頂部說明卡片
        intro_card = QFrame()
        intro_card.setObjectName("cardFrame")
        intro_layout = QVBoxLayout(intro_card)
        intro_layout.setContentsMargins(14, 12, 14, 12)
        intro_layout.setSpacing(4)
        intro_title = QLabel("📖 小說極速連載工作台")
        intro_title.setStyleSheet("color: #e5a93b; font-size: 16px; font-weight: bold;")
        intro_desc = QLabel("⚡ 專為長篇連載打造：支援直接手動輸入/修改部、卷、章名稱，或從歷史選單快速帶入。拖入 .md 檔案即可自動發布！")
        intro_desc.setStyleSheet("color: #a2a2ab; font-size: 12px;")
        intro_layout.addWidget(intro_title)
        intro_layout.addWidget(intro_desc)
        layout.addWidget(intro_card)

        # 1. 作品與階層設定卡片 (網格排版，輸入框設定固定高度防擠壓)
        sel_card = QFrame()
        sel_card.setObjectName("cardFrame")
        sel_layout = QVBoxLayout(sel_card)
        sel_layout.setContentsMargins(16, 14, 16, 14)
        sel_layout.setSpacing(12)

        # 作品列
        row_book = QHBoxLayout()
        lbl_book = QLabel("1. 所屬作品:")
        lbl_book.setFixedWidth(85)
        lbl_book.setStyleSheet("color: #e5a93b; font-weight: bold; font-size: 13px;")
        self.novel_book_combo = NoScrollComboBox()
        self.novel_book_combo.setMinimumHeight(34)
        self.novel_book_combo.currentIndexChanged.connect(self.on_novel_publisher_book_changed)
        btn_add_book = QPushButton("➕ 新建作品")
        btn_add_book.setFixedSize(95, 34)
        btn_add_book.clicked.connect(self.add_novel_book_quick_dialog)
        row_book.addWidget(lbl_book)
        row_book.addWidget(self.novel_book_combo, 1)
        row_book.addWidget(btn_add_book)
        sel_layout.addLayout(row_book)

        # 快速帶入歷史章節選單
        row_preset = QHBoxLayout()
        lbl_preset = QLabel("📚 歷史章節:")
        lbl_preset.setFixedWidth(85)
        lbl_preset.setStyleSheet("color: #a2a2ab; font-weight: bold; font-size: 13px;")
        self.novel_history_combo = NoScrollComboBox()
        self.novel_history_combo.setMinimumHeight(34)
        self.novel_history_combo.currentIndexChanged.connect(self.on_novel_history_selected)
        btn_refresh_preset = QPushButton("🔄 重新整理")
        btn_refresh_preset.setFixedSize(95, 34)
        btn_refresh_preset.clicked.connect(self.reload_novel_publisher_data)
        row_preset.addWidget(lbl_preset)
        row_preset.addWidget(self.novel_history_combo, 1)
        row_preset.addWidget(btn_refresh_preset)
        sel_layout.addLayout(row_preset)

        # 階層直接編輯欄位 (部、卷、章 序號與自訂名稱框，使用 QFrame 包裹確保高度充裕)
        hier_box = QFrame()
        hier_box.setStyleSheet("background-color: #16161d; border: 1px solid #2e2e3a; border-radius: 8px; padding: 10px;")
        hier_layout = QVBoxLayout(hier_box)
        hier_layout.setSpacing(10)

        input_qss = "background-color: #22222b; border: 1px solid #3e3e4f; border-radius: 5px; padding: 6px 10px; color: #ffffff; font-size: 13px;"

        # 部 (Part)
        row_p = QHBoxLayout()
        lbl_p_num = QLabel("❖ 部 (Part):")
        lbl_p_num.setFixedWidth(120)
        lbl_p_num.setStyleSheet("color: #e5a93b; font-weight: bold; font-size: 13px;")
        self.novel_part_num_input = QLineEdit("1")
        self.novel_part_num_input.setFixedSize(55, 34)
        self.novel_part_num_input.setAlignment(Qt.AlignCenter)
        self.novel_part_num_input.setStyleSheet(input_qss)
        self.novel_part_num_input.textChanged.connect(self.update_novel_target_preview)
        
        self.novel_part_title_input = QLineEdit("第一部 天命初顯")
        self.novel_part_title_input.setMinimumHeight(34)
        self.novel_part_title_input.setStyleSheet(input_qss)
        self.novel_part_title_input.setPlaceholderText("請輸入部名稱 (如：第一部 天命初顯)")
        self.novel_part_title_input.textChanged.connect(self.update_novel_target_preview)
        
        row_p.addWidget(lbl_p_num)
        row_p.addWidget(QLabel("第"))
        row_p.addWidget(self.novel_part_num_input)
        row_p.addWidget(QLabel("部   名稱:"))
        row_p.addWidget(self.novel_part_title_input, 1)
        hier_layout.addLayout(row_p)

        # 卷 (Volume)
        row_v = QHBoxLayout()
        lbl_v_num = QLabel("❖ 卷 (Volume):")
        lbl_v_num.setFixedWidth(120)
        lbl_v_num.setStyleSheet("color: #e5a93b; font-weight: bold; font-size: 13px;")
        self.novel_vol_num_input = QLineEdit("1")
        self.novel_vol_num_input.setFixedSize(55, 34)
        self.novel_vol_num_input.setAlignment(Qt.AlignCenter)
        self.novel_vol_num_input.setStyleSheet(input_qss)
        self.novel_vol_num_input.textChanged.connect(self.update_novel_target_preview)
        
        self.novel_vol_title_input = QLineEdit("第一卷 風起青萍")
        self.novel_vol_title_input.setMinimumHeight(34)
        self.novel_vol_title_input.setStyleSheet(input_qss)
        self.novel_vol_title_input.setPlaceholderText("請輸入卷名稱 (如：第一卷 風起青萍)")
        self.novel_vol_title_input.textChanged.connect(self.update_novel_target_preview)
        
        row_v.addWidget(lbl_v_num)
        row_v.addWidget(QLabel("第"))
        row_v.addWidget(self.novel_vol_num_input)
        row_v.addWidget(QLabel("卷   名稱:"))
        row_v.addWidget(self.novel_vol_title_input, 1)
        hier_layout.addLayout(row_v)

        # 章 (Chapter)
        row_c = QHBoxLayout()
        lbl_c_num = QLabel("❖ 章 (Chapter):")
        lbl_c_num.setFixedWidth(120)
        lbl_c_num.setStyleSheet("color: #e5a93b; font-weight: bold; font-size: 13px;")
        self.novel_chap_num_input = QLineEdit("1")
        self.novel_chap_num_input.setFixedSize(55, 34)
        self.novel_chap_num_input.setAlignment(Qt.AlignCenter)
        self.novel_chap_num_input.setStyleSheet(input_qss)
        self.novel_chap_num_input.textChanged.connect(self.on_chapter_changed_auto_recalc_section)
        
        self.novel_chap_title_input = QLineEdit("第一章 孤崖夜雨")
        self.novel_chap_title_input.setMinimumHeight(34)
        self.novel_chap_title_input.setStyleSheet(input_qss)
        self.novel_chap_title_input.setPlaceholderText("請輸入章名稱 (如：第一章 孤崖夜雨)")
        self.novel_chap_title_input.textChanged.connect(self.update_novel_target_preview)
        
        row_c.addWidget(lbl_c_num)
        row_c.addWidget(QLabel("第"))
        row_c.addWidget(self.novel_chap_num_input)
        row_c.addWidget(QLabel("章   名稱:"))
        row_c.addWidget(self.novel_chap_title_input, 1)
        hier_layout.addLayout(row_c)

        # 節 (Section) - 支援手動任意修改節數與標題
        row_s = QHBoxLayout()
        lbl_s_num = QLabel("❖ 節 (Section):")
        lbl_s_num.setFixedWidth(120)
        lbl_s_num.setStyleSheet("color: #e5a93b; font-weight: bold; font-size: 13px;")
        self.novel_sec_num_input = QLineEdit("1")
        self.novel_sec_num_input.setFixedSize(55, 34)
        self.novel_sec_num_input.setAlignment(Qt.AlignCenter)
        self.novel_sec_num_input.setStyleSheet(input_qss)
        self.novel_sec_num_input.textChanged.connect(self.on_section_num_text_changed)
        
        self.novel_sec_title_input = QLineEdit("第一節")
        self.novel_sec_title_input.setMinimumHeight(34)
        self.novel_sec_title_input.setStyleSheet(input_qss)
        self.novel_sec_title_input.setPlaceholderText("請輸入節標題 (如：第一節)")
        self.novel_sec_title_input.textChanged.connect(self.update_novel_target_preview)

        btn_recalc_sec = QPushButton("⚡ 重算推薦下一節")
        btn_recalc_sec.setFixedSize(130, 34)
        btn_recalc_sec.setStyleSheet("background-color: #2e3440; color: #88c0d0; font-size: 11px; font-weight: bold;")
        btn_recalc_sec.clicked.connect(self.recalculate_next_section_for_current_chap)
        
        row_s.addWidget(lbl_s_num)
        row_s.addWidget(QLabel("第"))
        row_s.addWidget(self.novel_sec_num_input)
        row_s.addWidget(QLabel("節   標題:"))
        row_s.addWidget(self.novel_sec_title_input, 1)
        row_s.addWidget(btn_recalc_sec)
        hier_layout.addLayout(row_s)

        sel_layout.addWidget(hier_box)

        # 當前準備發布之小節資訊預覽條
        self.novel_target_sec_info = QLabel("❖ 當前準備發布：正在計算章節位置...")
        self.novel_target_sec_info.setMinimumHeight(38)
        self.novel_target_sec_info.setStyleSheet("color: #5af776; font-weight: bold; background: #162419; border: 1px solid #28542e; border-radius: 6px; padding: 8px 12px; font-size: 13px;")
        sel_layout.addWidget(self.novel_target_sec_info)

        layout.addWidget(sel_card)

        # 2. 正文輸入與檔案拖曳區
        content_card = QFrame()
        content_card.setObjectName("cardFrame")
        content_layout = QVBoxLayout(content_card)
        content_layout.setContentsMargins(16, 14, 16, 14)
        content_layout.setSpacing(10)

        lbl_content_title = QLabel("2. 正文內容 (支援直接將 Markdown 檔案拖曳進編輯框):")
        lbl_content_title.setStyleSheet("color: #e5a93b; font-weight: bold; font-size: 13px;")
        content_layout.addWidget(lbl_content_title)

        self.novel_content_edit = DropMarkdownEdit(on_text_changed=self.update_novel_publisher_word_count)
        self.novel_content_edit.setMinimumHeight(240)
        self.novel_content_edit.setStyleSheet("background-color: #22222b; border: 1px solid #3e3e4f; border-radius: 6px; padding: 10px; font-family: 'LXGW WenKai TC', 'Microsoft JhengHei', sans-serif; font-size: 14px; line-height: 1.6;")
        content_layout.addWidget(self.novel_content_edit)

        # 內容輔助工具列
        tools_row = QHBoxLayout()
        btn_paste = QPushButton("📋 貼上剪貼簿內容")
        btn_paste.setMinimumHeight(32)
        btn_paste.setStyleSheet("background-color: #2e3440; color: #88c0d0; font-weight: bold; padding: 4px 12px;")
        btn_paste.clicked.connect(self.paste_novel_clipboard_content)

        btn_browse_md = QPushButton("📂 選擇本機 Markdown 檔案")
        btn_browse_md.setMinimumHeight(32)
        btn_browse_md.clicked.connect(self.browse_novel_md_file)

        btn_clear = QPushButton("🧹 清空")
        btn_clear.setFixedSize(65, 32)
        btn_clear.clicked.connect(lambda: self.novel_content_edit.clear())

        self.lbl_novel_word_count = QLabel("📝 本節字數：0 字")
        self.lbl_novel_word_count.setStyleSheet("color: #a2a2ab; font-size: 12px; font-weight: bold;")

        tools_row.addWidget(btn_paste)
        tools_row.addWidget(btn_browse_md)
        tools_row.addWidget(btn_clear)
        tools_row.addStretch()
        tools_row.addWidget(self.lbl_novel_word_count)
        content_layout.addLayout(tools_row)

        layout.addWidget(content_card)

        # 3. 儲存與推送按鈕列
        action_layout = QHBoxLayout()
        self.btn_save_novel_section = QPushButton("💾 儲存此節並準備下一節 (Ctrl+Enter)")
        self.btn_save_novel_section.setMinimumHeight(44)
        self.btn_save_novel_section.setStyleSheet("""
            QPushButton {
                background-color: #e5a93b;
                color: #1a1a20;
                font-weight: bold;
                font-size: 14px;
                padding: 10px 18px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #f0bc5e;
            }
            QPushButton:pressed {
                background-color: #c98e28;
            }
        """)
        self.btn_save_novel_section.clicked.connect(self.save_current_novel_section)

        self.btn_git_push_novels = QPushButton("🚀 一併推送到網站 (一鍵發布上線)")
        self.btn_git_push_novels.setMinimumHeight(44)
        self.btn_git_push_novels.setStyleSheet("""
            QPushButton {
                background-color: #2d7d46;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                padding: 10px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #389e58;
            }
            QPushButton:pressed {
                background-color: #236337;
            }
        """)
        self.btn_git_push_novels.clicked.connect(self.confirm_publish)

        action_layout.addWidget(self.btn_save_novel_section, 3)
        action_layout.addWidget(self.btn_git_push_novels, 2)
        layout.addLayout(action_layout)

        # 4. 本次連載儲存記錄 (Staging List)
        staging_card = QFrame()
        staging_card.setObjectName("cardFrame")
        staging_layout = QVBoxLayout(staging_card)
        staging_layout.setContentsMargins(14, 10, 14, 10)
        staging_layout.setSpacing(6)

        staging_head = QHBoxLayout()
        lbl_staging = QLabel("📋 本次工作階段已建立小節:")
        lbl_staging.setStyleSheet("color: #a2a2ab; font-size: 12px; font-weight: bold;")
        btn_refresh_novel_tree = QPushButton("🔄 重新整理")
        btn_refresh_novel_tree.setFixedSize(90, 28)
        btn_refresh_novel_tree.setStyleSheet("font-size: 11px; padding: 2px;")
        btn_refresh_novel_tree.clicked.connect(self.reload_novel_publisher_data)
        staging_head.addWidget(lbl_staging)
        staging_head.addStretch()
        staging_head.addWidget(btn_refresh_novel_tree)
        staging_layout.addLayout(staging_head)

        self.novel_staging_list = QListWidget()
        self.novel_staging_list.setMinimumHeight(80)
        self.novel_staging_list.setMaximumHeight(120)
        staging_layout.addWidget(self.novel_staging_list)

        layout.addWidget(staging_card)

        # 初次載入小說資料庫
        self.reload_novel_publisher_data()

        scroll_area.setWidget(panel)
        return scroll_area

    def reload_novel_publisher_data(self):
        """掃描小說作品與章節資料庫，建構階層快取樹"""
        self.novel_hierarchy = {}
        self.novel_history_items = []  # [ { label: str, b_slug, p_num, p_title, v_num, v_title, c_num, c_title, max_s_num } ]
        
        # 1. 讀取作品列表
        novels_dir = os.path.join(self.project_dir, "src", "content", "novels")
        if os.path.exists(novels_dir):
            for fname in os.listdir(novels_dir):
                if fname.endswith((".md", ".yaml", ".json")) and not fname.startswith("_"):
                    book_slug = os.path.splitext(fname)[0]
                    fpath = os.path.join(novels_dir, fname)
                    book_title = book_slug
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            content = f.read()
                            for line in content.split("\n"):
                                if line.startswith("title:"):
                                    book_title = line.replace("title:", "").strip().strip("\"'")
                                    break
                    except Exception:
                        pass
                    self.novel_hierarchy[book_slug] = {
                        "title": book_title,
                        "parts": {}
                    }
        
        if not self.novel_hierarchy:
            self.novel_hierarchy["tianxia"] = { "title": "天下", "parts": {} }

        # 2. 讀取所有現有章節
        chapters_dir = os.path.join(self.project_dir, "src", "content", "novel_chapters")
        if os.path.exists(chapters_dir):
            for fname in os.listdir(chapters_dir):
                if fname.endswith(".md") and not fname.startswith("_"):
                    fpath = os.path.join(chapters_dir, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            text = f.read()
                        
                        import re
                        m = re.search(r"^---\s*\n([\s\S]*?)\n---", text)
                        if m:
                            fm_str = m.group(1)
                            b_slug = "tianxia"
                            p_num, p_title = 1, "第一部 天命初顯"
                            v_num, v_title = 1, "第一卷 風起青萍"
                            c_num, c_title = 1, "第一章 孤崖夜雨"
                            s_num = 1
                            
                            mb = re.search(r"book:\s*[\"']?([^\"'\n]+)", fm_str)
                            if mb: b_slug = mb.group(1).strip()
                            
                            mp_num = re.search(r"part:[\s\S]*?number:\s*(\d+)", fm_str)
                            if mp_num: p_num = int(mp_num.group(1))
                            mp_title = re.search(r"part:[\s\S]*?title:\s*[\"']?([^\"'\n]+)", fm_str)
                            if mp_title: p_title = mp_title.group(1).strip()

                            mv_num = re.search(r"volume:[\s\S]*?number:\s*(\d+)", fm_str)
                            if mv_num: v_num = int(mv_num.group(1))
                            mv_title = re.search(r"volume:[\s\S]*?title:\s*[\"']?([^\"'\n]+)", fm_str)
                            if mv_title: v_title = mv_title.group(1).strip()

                            mc_num = re.search(r"chapter:[\s\S]*?number:\s*(\d+)", fm_str)
                            if mc_num: c_num = int(mc_num.group(1))
                            mc_title = re.search(r"chapter:[\s\S]*?title:\s*[\"']?([^\"'\n]+)", fm_str)
                            if mc_title: c_title = mc_title.group(1).strip()

                            ms_num = re.search(r"section:[\s\S]*?number:\s*(\d+)", fm_str)
                            if ms_num: s_num = int(ms_num.group(1))

                            if b_slug not in self.novel_hierarchy:
                                self.novel_hierarchy[b_slug] = { "title": b_slug, "parts": {} }
                            
                            parts = self.novel_hierarchy[b_slug]["parts"]
                            if p_num not in parts:
                                parts[p_num] = { "title": p_title, "volumes": {} }
                            
                            vols = parts[p_num]["volumes"]
                            if v_num not in vols:
                                vols[v_num] = { "title": v_title, "chapters": {} }
                            
                            chaps = vols[v_num]["chapters"]
                            if c_num not in chaps:
                                chaps[c_num] = { "title": c_title, "sections": [] }
                            
                            if s_num not in chaps[c_num]["sections"]:
                                chaps[c_num]["sections"].append(s_num)
                    except Exception:
                        pass

        # 3. 刷新作品下拉選單
        self.novel_book_combo.blockSignals(True)
        self.novel_book_combo.clear()
        for b_slug, b_info in self.novel_hierarchy.items():
            self.novel_book_combo.addItem(f"{b_info['title']} ({b_slug})", b_slug)
        self.novel_book_combo.blockSignals(False)

        # 4. 刷新歷史章節預設選單
        self.refresh_novel_history_combo()

    def refresh_novel_history_combo(self):
        b_slug = self.novel_book_combo.currentData() or "tianxia"
        b_info = self.novel_hierarchy.get(b_slug, {"parts": {}})
        parts = b_info.get("parts", {})

        self.novel_history_combo.blockSignals(True)
        self.novel_history_combo.clear()
        self.novel_history_combo.addItem("-- 請選擇要帶入的既有章節 (或在下方直接手動輸入) --", None)

        history_items = []
        for p_num, p_data in sorted(parts.items()):
            p_title = p_data["title"]
            for v_num, v_data in sorted(p_data.get("volumes", {}).items()):
                v_title = v_data["title"]
                for c_num, c_data in sorted(v_data.get("chapters", {}).items()):
                    c_title = c_data["title"]
                    secs = c_data.get("sections", [])
                    max_s = max(secs) if secs else 0
                    label = f"{v_title} ➔ {c_title} (已有 {len(secs)} 節)"
                    item_data = {
                        "p_num": p_num,
                        "p_title": p_title,
                        "v_num": v_num,
                        "v_title": v_title,
                        "c_num": c_num,
                        "c_title": c_title,
                        "max_s": max_s
                    }
                    self.novel_history_combo.addItem(label, item_data)
                    history_items.append(item_data)

        self.novel_history_combo.blockSignals(False)

        # 若有歷史章節，預設選取最新的一個章節帶入輸入框
        if history_items:
            latest = history_items[-1]
            self.novel_part_num_input.setText(str(latest["p_num"]))
            self.novel_part_title_input.setText(latest["p_title"])
            self.novel_vol_num_input.setText(str(latest["v_num"]))
            self.novel_vol_title_input.setText(latest["v_title"])
            self.novel_chap_num_input.setText(str(latest["c_num"]))
            self.novel_chap_title_input.setText(latest["c_title"])
            next_sec = latest["max_s"] + 1
            self.novel_sec_num_input.setText(str(next_sec))
            self.novel_sec_title_input.setText(f"第{to_chinese_num(next_sec)}節")
        else:
            # 全新作品或無章節紀錄：預設全部從第 1 開始
            self.novel_part_num_input.setText("1")
            self.novel_part_title_input.setText("第一部")
            self.novel_vol_num_input.setText("1")
            self.novel_vol_title_input.setText("第一卷")
            self.novel_chap_num_input.setText("1")
            self.novel_chap_title_input.setText("第一章")
            self.novel_sec_num_input.setText("1")
            self.novel_sec_title_input.setText("第一節")

        self.update_novel_target_preview()

    def on_novel_publisher_book_changed(self):
        self.refresh_novel_history_combo()

    def on_novel_history_selected(self, index):
        data = self.novel_history_combo.currentData()
        if not data:
            return
        
        self.novel_part_num_input.setText(str(data["p_num"]))
        self.novel_part_title_input.setText(data["p_title"])
        self.novel_vol_num_input.setText(str(data["v_num"]))
        self.novel_vol_title_input.setText(data["v_title"])
        self.novel_chap_num_input.setText(str(data["c_num"]))
        self.novel_chap_title_input.setText(data["c_title"])
        next_sec = data["max_s"] + 1
        self.novel_sec_num_input.setText(str(next_sec))
        self.novel_sec_title_input.setText(f"第{to_chinese_num(next_sec)}節")
        self.update_novel_target_preview()

    def on_chapter_changed_auto_recalc_section(self):
        self.recalculate_next_section_for_current_chap()

    def recalculate_next_section_for_current_chap(self):
        b_slug = self.novel_book_combo.currentData() or "tianxia"
        try:
            p_num = int(self.novel_part_num_input.text().strip() or "1")
            v_num = int(self.novel_vol_num_input.text().strip() or "1")
            c_num = int(self.novel_chap_num_input.text().strip() or "1")
        except ValueError:
            p_num, v_num, c_num = 1, 1, 1

        b_info = self.novel_hierarchy.get(b_slug, {"parts": {}})
        chaps = b_info.get("parts", {}).get(p_num, {}).get("volumes", {}).get(v_num, {}).get("chapters", {}).get(c_num, {})
        secs = chaps.get("sections", []) if isinstance(chaps, dict) else []
        next_s = max(secs) + 1 if secs else 1
        self.novel_sec_num_input.setText(str(next_s))
        self.novel_sec_title_input.setText(f"第{to_chinese_num(next_s)}節")
        self.update_novel_target_preview()

    def on_section_num_text_changed(self):
        try:
            s_num = int(self.novel_sec_num_input.text().strip() or "1")
            self.novel_sec_title_input.setText(f"第{to_chinese_num(s_num)}節")
        except ValueError:
            pass
        self.update_novel_target_preview()

    def update_novel_target_preview(self):
        b_slug = self.novel_book_combo.currentData() or "tianxia"
        try:
            p_num = int(self.novel_part_num_input.text().strip() or "1")
        except ValueError:
            p_num = 1
        try:
            v_num = int(self.novel_vol_num_input.text().strip() or "1")
        except ValueError:
            v_num = 1
        try:
            c_num = int(self.novel_chap_num_input.text().strip() or "1")
        except ValueError:
            c_num = 1
        try:
            s_num = int(self.novel_sec_num_input.text().strip() or "1")
        except ValueError:
            s_num = 1

        p_title = self.novel_part_title_input.text().strip() or f"第{to_chinese_num(p_num)}部"
        v_title = self.novel_vol_title_input.text().strip() or f"第{to_chinese_num(v_num)}卷"
        c_title = self.novel_chap_title_input.text().strip() or f"第{to_chinese_num(c_num)}章"
        s_title = self.novel_sec_title_input.text().strip() or f"第{to_chinese_num(s_num)}節"

        target_filename = f"{b_slug}-vol{v_num:02d}-c{c_num:02d}-s{s_num:02d}.md"

        self.novel_target_sec_info.setText(
            f"❖ 當前準備發布：{p_title} · {v_title} · {c_title} ➔ 【{s_title}】 (預計檔名: {target_filename})"
        )

    def add_novel_book_quick_dialog(self):
        title, ok = QInputDialog.getText(self, "➕ 新建小說作品", "請輸入小說書名 (如：天命長歌):")
        if ok and title.strip():
            slug, ok2 = QInputDialog.getText(self, "網址別名", f"請輸入作品代號 slug (如：tianming):", text=title.strip().lower())
            if ok2 and slug.strip():
                clean_slug = slug.strip().lower()
                clean_title = title.strip()
                if clean_slug not in self.novel_hierarchy:
                    self.novel_hierarchy[clean_slug] = { "title": clean_title, "parts": {} }
                    self.novel_book_combo.addItem(f"{clean_title} ({clean_slug})", clean_slug)
                    self.novel_book_combo.setCurrentIndex(self.novel_book_combo.count() - 1)
                    
                    novels_dir = os.path.join(self.project_dir, "src", "content", "novels")
                    os.makedirs(novels_dir, exist_ok=True)
                    target_file = os.path.join(novels_dir, f"{clean_slug}.md")
                    if not os.path.exists(target_file):
                        with open(target_file, "w", encoding="utf-8") as f:
                            f.write(f"---\ntitle: \"{clean_title}\"\ndescription: \"原創小說 {clean_title}\"\ngenre: [\"仙俠\", \"武俠\"]\nstatus: \"ongoing\"\npubDate: {datetime.date.today().isoformat()}\n---\n\n暫無簡介。\n")
                    self.log(f"✓ 已建立新小說作品檔: {clean_slug}.md")

    def paste_novel_clipboard_content(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            import re
            clean_text = re.sub(r"^---\s*\n[\s\S]*?\n---\s*\n", "", text.strip())
            self.novel_content_edit.setPlainText(clean_text)
            self.log(f"📋 已成功從剪貼簿貼入正文 ({len(clean_text)} 字元)")
        else:
            QMessageBox.information(self, "提示", "剪貼簿目前沒有文字內容。")

    def browse_novel_md_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "選擇小說 Markdown 檔案", self.project_dir, "Markdown Files (*.md *.txt);;All Files (*.*)")
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                import re
                clean_content = re.sub(r"^---\s*\n[\s\S]*?\n---\s*\n", "", content.strip())
                self.novel_content_edit.setPlainText(clean_content)
                self.log(f"📂 已成功載入本機檔案: {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(self, "讀取失敗", f"無法讀取該檔案: {e}")

    def update_novel_publisher_word_count(self):
        text = self.novel_content_edit.toPlainText().strip()
        char_count = len(text)
        chinese_chars = len([c for c in text if not c.isspace()])
        self.lbl_novel_word_count.setText(f"📝 本節字數：約 {chinese_chars} 字 (含標點 {char_count} 字元)")

    def save_current_novel_section(self):
        body = self.novel_content_edit.toPlainText().strip()
        if not body:
            QMessageBox.warning(self, "請填寫正文", "請先拖入 Markdown 檔案或貼上故事正文後再進行儲存！")
            return

        b_slug = self.novel_book_combo.currentData() or "tianxia"
        try:
            p_num = int(self.novel_part_num_input.text().strip() or "1")
        except ValueError:
            p_num = 1
        try:
            v_num = int(self.novel_vol_num_input.text().strip() or "1")
        except ValueError:
            v_num = 1
        try:
            c_num = int(self.novel_chap_num_input.text().strip() or "1")
        except ValueError:
            c_num = 1
        try:
            s_num = int(self.novel_sec_num_input.text().strip() or "1")
        except ValueError:
            s_num = 1

        p_title = self.novel_part_title_input.text().strip() or f"第{to_chinese_num(p_num)}部"
        v_title = self.novel_vol_title_input.text().strip() or f"第{to_chinese_num(v_num)}卷"
        c_title = self.novel_chap_title_input.text().strip() or f"第{to_chinese_num(c_num)}章"
        s_title = self.novel_sec_title_input.text().strip() or f"第{to_chinese_num(s_num)}節"

        order_val = p_num * 1000000 + v_num * 10000 + c_num * 100 + s_num
        target_filename = f"{b_slug}-vol{v_num:02d}-c{c_num:02d}-s{s_num:02d}.md"

        chapters_dir = os.path.join(self.project_dir, "src", "content", "novel_chapters")
        os.makedirs(chapters_dir, exist_ok=True)
        target_filepath = os.path.join(chapters_dir, target_filename)

        frontmatter_str = f"""---
title: "{s_title}"
book: "{b_slug}"
part:
  number: {p_num}
  title: "{p_title}"
volume:
  number: {v_num}
  title: "{v_title}"
chapter:
  number: {c_num}
  title: "{c_title}"
section:
  number: {s_num}
  title: "{s_title}"
order: {order_val}
pubDate: {datetime.date.today().isoformat()}
---

{body}
"""
        try:
            with open(target_filepath, "w", encoding="utf-8") as f:
                f.write(frontmatter_str)

            word_count = len([c for c in body if not c.isspace()])
            item_text = f"✓ [已儲存] {v_title} · {c_title} · {s_title} ({word_count} 字) ➔ {target_filename}"
            self.novel_staging_list.addItem(item_text)
            self.log(f"🎉 成功儲存小節: {target_filename} (字數: {word_count})")

            # 更新本機記憶體 hierarchy
            b_info = self.novel_hierarchy.setdefault(b_slug, {}).setdefault("parts", {})
            vols = b_info.setdefault(p_num, {"title": p_title, "volumes": {}}).setdefault("volumes", {})
            chaps = vols.setdefault(v_num, {"title": v_title, "chapters": {}}).setdefault("chapters", {})
            sec_list = chaps.setdefault(c_num, {"title": c_title, "sections": []}).setdefault("sections", [])
            if s_num not in sec_list:
                sec_list.append(s_num)

            # 儲存成功：自動將節數加 1，清空正文並對焦！
            next_s = s_num + 1
            self.novel_sec_num_input.setText(str(next_s))
            self.novel_sec_title_input.setText(f"第{to_chinese_num(next_s)}節")
            self.novel_content_edit.clear()
            self.update_novel_target_preview()
            self.novel_content_edit.setFocus()

        except Exception as e:
            QMessageBox.critical(self, "儲存失敗", f"無法寫入章節檔案: {e}")
            self.log(f"❌ 寫入失敗: {e}")

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
