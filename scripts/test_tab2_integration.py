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

class TestTab2Integration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.window = MainWindow()

    def tearDown(self):
        self.window.close()

    def test_01_tab2_components_existence(self):
        """測試 Tab 2 三欄並排組件是否存在且正常配置"""
        self.assertIsNotNone(self.window.tab2_splitter)
        self.assertEqual(self.window.tab2_splitter.count(), 3)
        self.assertIsNotNone(self.window.tab2_prop_panel)
        self.assertIsNotNone(self.window.tab2_editor_panel)
        self.assertIsNotNone(self.window.tab2_body_edit)
        self.assertIsNotNone(self.window.tab2_file_list_widget)

    def test_02_prop_panel_toggle(self):
        """測試中欄屬性面板一鍵收折與展開"""
        self.assertFalse(self.window.tab2_prop_panel.isHidden())
        self.window.toggle_tab2_prop_panel()
        self.assertTrue(self.window.tab2_prop_panel.isHidden())
        self.window.toggle_tab2_prop_panel()
        self.assertFalse(self.window.tab2_prop_panel.isHidden())

    def test_03_font_size_adjustment(self):
        """測試字級縮放按鈕"""
        initial_size = self.window.tab2_current_font_size
        self.window.change_tab2_font_size(2)
        self.assertEqual(self.window.tab2_current_font_size, initial_size + 2)
        self.assertEqual(self.window.tab2_lbl_font_size.text(), f"{initial_size + 2}px")
        
        self.window.reset_tab2_font_size()
        self.assertEqual(self.window.tab2_current_font_size, 15)
        self.assertEqual(self.window.tab2_lbl_font_size.text(), "15px")

    def test_04_editing_dirty_and_statistics(self):
        """測試文字輸入、字數統計與 60 秒計時器啟動"""
        self.window.is_tab2_loading = False
        self.window.tab2_body_edit.setPlainText("蜀道難，難於上青天！")
        
        self.assertTrue(self.window.is_tab2_dirty)
        self.assertIn("10 字", self.window.tab2_lbl_char_count.text())
        self.assertTrue(self.window.tab2_autosave_timer.isActive())

    def test_05_search_filtering(self):
        """測試 Tab 2 搜尋框過濾"""
        self.window.refresh_tab2_file_list()
        self.window.tab2_search_input.setText("非存在關鍵字_xyz_123")
        visible_count = sum(
            1 for i in range(self.window.tab2_file_list_widget.count())
            if not self.window.tab2_file_list_widget.item(i).isHidden()
        )
        self.assertEqual(visible_count, 0)
        self.window.tab2_search_input.setText("")

    def test_06_auto_save_mechanism(self):
        """測試 60 秒自動存檔呼叫不拋出異常並正確更新狀態"""
        self.window.refresh_tab2_file_list()
        if self.window.tab2_file_list_widget.count() > 0:
            item = self.window.tab2_file_list_widget.item(0)
            fpath = item.data(Qt.UserRole)
            self.window.load_tab2_file(fpath)
            self.window.mark_tab2_dirty()
            self.assertTrue(self.window.is_tab2_dirty)
            self.window.auto_save_tab2_article()
            self.assertFalse(self.window.is_tab2_dirty)
        else:
            self.window.is_tab2_dirty = False
            self.window.auto_save_tab2_article()
            self.assertFalse(self.window.is_tab2_dirty)

if __name__ == "__main__":
    unittest.main(verbosity=2)

