import os
import sys

# 將腳本所在目錄加入模組搜尋路徑
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

import unittest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from import_gui import MainWindow

class TestGuiIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.window = MainWindow()

    def tearDown(self):
        self.window.close()

    # ----------------------------------------------------
    # 控制台即時日誌折疊測試
    # ----------------------------------------------------
    def test_01_console_panel_toggle(self):
        """測試控制台即時日誌一鍵折疊與展開"""
        self.assertIsNotNone(self.window.console_panel)
        self.assertFalse(self.window.console_panel.isHidden())
        self.window.toggle_console_panel()
        self.assertTrue(self.window.console_panel.isHidden())
        self.window.toggle_console_panel()
        self.assertFalse(self.window.console_panel.isHidden())

    # ----------------------------------------------------
    # Tab 1 (待處理檔案匯入) 測試
    # ----------------------------------------------------
    def test_02_tab1_components_existence(self):
        """測試 Tab 1 三欄並排組件是否存在且正常配置"""
        self.assertIsNotNone(self.window.tab1_splitter)
        self.assertEqual(self.window.tab1_splitter.count(), 3)
        self.assertIsNotNone(self.window.tab1_prop_panel)
        self.assertIsNotNone(self.window.tab1_editor_panel)
        self.assertIsNotNone(self.window.tab1_body_edit)
        self.assertIsNotNone(self.window.file_list_widget)

    def test_03_tab1_prop_panel_toggle(self):
        """測試 Tab 1 中欄屬性面板一鍵收折與展開"""
        self.assertFalse(self.window.tab1_prop_panel.isHidden())
        self.window.toggle_tab1_prop_panel()
        self.assertTrue(self.window.tab1_prop_panel.isHidden())
        self.window.toggle_tab1_prop_panel()
        self.assertFalse(self.window.tab1_prop_panel.isHidden())

    def test_04_tab1_font_size_adjustment(self):
        """測試 Tab 1 字級縮放按鈕"""
        initial_size = self.window.tab1_current_font_size
        self.window.change_tab1_font_size(2)
        self.assertEqual(self.window.tab1_current_font_size, initial_size + 2)
        self.assertEqual(self.window.tab1_lbl_font_size.text(), f"{initial_size + 2}px")
        
        self.window.reset_tab1_font_size()
        self.assertEqual(self.window.tab1_current_font_size, 15)
        self.assertEqual(self.window.tab1_lbl_font_size.text(), "15px")

    def test_05_tab1_editing_and_statistics(self):
        """測試 Tab 1 正文輸入、字數統計與 60 秒計時器啟動"""
        self.window.is_tab1_loading = False
        self.window.tab1_body_edit.setPlainText("待處理草稿文字測試內容")
        
        self.assertTrue(self.window.is_tab1_dirty)
        self.assertIn("11 字", self.window.tab1_lbl_char_count.text())
        self.assertTrue(self.window.tab1_autosave_timer.isActive())

    def test_06_tab1_search_filtering(self):
        """測試 Tab 1 待處理檔案搜尋過濾"""
        self.window.refresh_file_list()
        self.window.tab1_search_input.setText("不存在之測試檔名_xyz_999")
        visible_count = sum(
            1 for i in range(self.window.file_list_widget.count())
            if not self.window.file_list_widget.item(i).isHidden()
        )
        self.assertEqual(visible_count, 0)
        self.window.tab1_search_input.setText("")

    # ----------------------------------------------------
    # Tab 2 (網站既有文章管理) 測試
    # ----------------------------------------------------
    def test_07_tab2_components_and_toggle(self):
        """測試 Tab 2 三欄並排與屬性收折"""
        self.assertIsNotNone(self.window.tab2_splitter)
        self.assertEqual(self.window.tab2_splitter.count(), 3)
        self.assertFalse(self.window.tab2_prop_panel.isHidden())
        self.window.toggle_tab2_prop_panel()
        self.assertTrue(self.window.tab2_prop_panel.isHidden())
        self.window.toggle_tab2_prop_panel()
        self.assertFalse(self.window.tab2_prop_panel.isHidden())

    def test_08_tab2_auto_save(self):
        """測試 Tab 2 60秒自動存檔機制"""
        self.window.refresh_tab2_file_list()
        if self.window.tab2_file_list_widget.count() > 0:
            item = self.window.tab2_file_list_widget.item(0)
            fpath = item.data(Qt.UserRole)
            self.window.load_tab2_file(fpath)
            self.window.mark_tab2_dirty()
            self.assertTrue(self.window.is_tab2_dirty)
            self.window.auto_save_tab2_article()
            self.assertFalse(self.window.is_tab2_dirty)

if __name__ == "__main__":
    unittest.main(verbosity=2)
