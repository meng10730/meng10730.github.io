import os
import sys

# 將腳本所在目錄加入模組搜尋路徑
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

import unittest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest

# 匯入待測模組
from preview_editor_ui import PreviewEditorWindow, SAMPLE_FILES


class TestPreviewEditorUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.window = PreviewEditorWindow()

    def tearDown(self):
        self.window.close()

    def test_01_initialization(self):
        """測試初始狀態與組件存在性"""
        self.assertIsNotNone(self.window.splitter)
        self.assertIsNotNone(self.window.editor)
        self.assertIsNotNone(self.window.file_list)
        self.assertIsNotNone(self.window.search_box)
        self.assertEqual(self.window.file_list.count(), len(SAMPLE_FILES))

    def test_02_file_selection_and_loading(self):
        """測試點擊檔案列表是否正確載入內容至編輯器"""
        # 點選第二個檔案
        self.window.file_list.setCurrentRow(1)
        current_item = self.window.file_list.currentItem()
        filename = current_item.data(Qt.UserRole)
        
        self.assertEqual(self.window.current_filename, filename)
        self.assertEqual(self.window.editor.toPlainText(), SAMPLE_FILES[filename])
        self.assertIn("已同步最新內容", self.window.lbl_save_status.text())

    def test_03_text_editing_and_statistics(self):
        """測試輸入文字時字數統計與未儲存狀態"""
        self.window.file_list.setCurrentRow(0)
        test_text = "唐門絕技，天下無雙。包含中文與標點！"
        self.window.editor.setPlainText(test_text)
        
        # 字數統計驗證 (去除空白與換行)
        expected_char_count = len(test_text.replace(" ", "").replace("\n", "").replace("\r", ""))
        self.assertIn(f"字數: {expected_char_count} 字", self.window.lbl_char_count.text())
        self.assertIn("編輯中 (未儲存)", self.window.lbl_save_status.text())

    def test_04_save_action(self):
        """測試沙盒儲存動作與狀態變更"""
        self.window.file_list.setCurrentRow(0)
        new_content = "# 修改後的測試標題\n全新內容。"
        self.window.editor.setPlainText(new_content)
        
        # 觸發儲存
        self.window.simulate_save()
        
        current_file = self.window.current_filename
        self.assertEqual(SAMPLE_FILES[current_file], new_content)
        self.assertIn("已儲存 (沙盒預覽)", self.window.lbl_save_status.text())

    def test_05_sidebar_toggle(self):
        """測試收合與展開側邊欄"""
        self.assertFalse(self.window.sidebar_widget.isHidden())
        self.window.toggle_sidebar()
        self.assertTrue(self.window.sidebar_widget.isHidden())
        self.window.toggle_sidebar()
        self.assertFalse(self.window.sidebar_widget.isHidden())

    def test_06_search_filtering(self):
        """測試檔案列表搜尋過濾功能"""
        self.window.search_box.setText("人物")
        visible_items = [
            self.window.file_list.item(i).text()
            for i in range(self.window.file_list.count())
            if not self.window.file_list.item(i).isHidden()
        ]
        self.assertEqual(len(visible_items), 1)
        self.assertIn("人物誌", visible_items[0])

    def test_07_large_text_and_special_characters(self):
        """測試極端大文本與特殊符號穩定性"""
        large_text = "【測試章節】\n" + ("夜色沉沉，風吹竹林。\n" * 2000) + "繁體中文測試：龍飛鳳舞，玄機莫測！🌟✨"
        self.window.editor.setPlainText(large_text)
        self.window.update_statistics()
        self.window.update_cursor_status()
        self.assertGreater(len(self.window.editor.toPlainText()), 10000)

if __name__ == "__main__":
    unittest.main(verbosity=2)
