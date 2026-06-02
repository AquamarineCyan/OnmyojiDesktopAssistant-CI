import sys
from enum import Enum

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    ComboBox,
)


class GameFunction(Enum):
    """游戏功能"""

    YUHUN = "御魂副本"
    YONGSHENGZHIHAI = "永生之海副本"
    YEYUANHUO = "业原火副本"
    YULING = "御灵副本"
    GERENTUPO = "个人突破"
    LIAOTUPO = "寮突破"
    DAOGUANTUPO = "道馆突破"
    ZHAOHUAN = "普通召唤"
    BAIGUIYEXING = "百鬼夜行"
    HUODONG = "限时活动"
    RILUN = "日轮副本"
    TANSUO = "单人探索"
    QILING = "契灵之境"
    JUEXING = "觉醒副本"
    LIUDAOZHIMEN = "六道之门速刷"
    DOUJI = "斗技自动上阵"
    YINGJIESHILIAN = "英杰试炼"
    HUIJUAN = "绘卷刷分"


class GameFunctionSelectorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("GameFunctionSelector")

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(10)

        self.function_selector_card = FunctionSelectorCard()
        self.function_list_card = FunctionListCard()

        self.main_layout.addWidget(self.function_selector_card)
        self.main_layout.addWidget(self.function_list_card)

        self._setup_connection()

    def _setup_connection(self):
        self.function_list_card.checkbox_toggled.connect(self._on_checkbox_toggled)
        self.function_list_card.all_toggled.connect(self._on_all_toggled)
        self.function_list_card.order_changed.connect(self._on_order_changed)

    def _on_checkbox_toggled(self, func: GameFunction, checked: bool):
        self.function_selector_card.func_combobox.setCurrentIndex(-1)
        if checked:
            self.function_selector_card.add_function(func)
        else:
            self.function_selector_card.remove_function(func)
        self.function_selector_card._reorder_items()

    def _on_all_toggled(self, all_checked: bool):
        self.function_selector_card.func_combobox.setCurrentIndex(-1)
        if all_checked:
            self.function_selector_card.add_all_functions()
        else:
            self.function_selector_card.clear_all_functions()

    def _on_order_changed(self, order: list):
        self.function_selector_card.set_function_order(order)


class FunctionSelectorCard(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(20, 11, 11, 11)
        self.hBoxLayout.setSpacing(15)

        self.func_label = BodyLabel("选择功能")
        self.func_label.setFixedWidth(60)

        self.func_combobox = ComboBox()
        self.func_combobox.setCurrentIndex(-1)
        self.func_combobox.setFixedWidth(200)

        self.hBoxLayout.addWidget(self.func_label)
        self.hBoxLayout.addWidget(self.func_combobox)
        self.hBoxLayout.addStretch(1)

        self._func_to_index = {}
        self._current_order = list(GameFunction)

        self.func_combobox.currentIndexChanged.connect(self._on_current_index_changed)

        self.add_all_functions()

    def _on_current_index_changed(self, index: int):
        if index >= 0:
            func = self.func_combobox.itemData(index)
            if func is not None:
                print(f"选中功能: {func.name} - {func.value}")
            else:
                text = self.func_combobox.itemText(index)
                print(f"选中功能(无数据): {text}")

    def get_function_text(self, func: GameFunction, index: int = None) -> str:
        if index is None:
            index = self._current_order.index(func) + 1
        return f"{index}.{func.value}"

    def add_function(self, func: GameFunction):
        if func in self._func_to_index:
            return

        insert_index = 0
        for i in range(self.func_combobox.count()):
            item_func = self.func_combobox.itemData(i)
            if item_func is not None:
                item_pos = self._current_order.index(item_func)
                func_pos = self._current_order.index(func)
                if func_pos > item_pos:
                    insert_index = i + 1
                else:
                    break

        text = self.get_function_text(func, insert_index + 1)
        self.func_combobox.insertItem(insert_index, text)
        self.func_combobox.setItemData(insert_index, func)
        self._func_to_index[func] = insert_index

    def remove_function(self, func: GameFunction):
        if func not in self._func_to_index:
            return

        index = self._func_to_index[func]
        current_text = self.func_combobox.currentText()
        func_text = self.get_function_text(func)

        self.func_combobox.removeItem(index)
        del self._func_to_index[func]

        if current_text == func_text:
            self.func_combobox.setCurrentIndex(-1)

    def add_all_functions(self):
        self.func_combobox.clear()
        self._func_to_index = {}

        for i, func in enumerate(self._current_order):
            text = self.get_function_text(func)
            self.func_combobox.addItem(text)
            self.func_combobox.setItemData(i, func)
            self._func_to_index[func] = i

        self.func_combobox.setCurrentIndex(-1)

    def clear_all_functions(self):
        self.func_combobox.clear()
        self._func_to_index = {}

    def set_function_order(self, order: list[GameFunction]):
        self._current_order = order.copy()
        self._reorder_items()

    def _reorder_items(self):
        items = []
        for i in range(self.func_combobox.count()):
            func = self.func_combobox.itemData(i)
            if func is not None:
                items.append(func)

        items.sort(key=lambda f: self._current_order.index(f))

        self.func_combobox.clear()
        self._func_to_index = {}

        for i, func in enumerate(items):
            text = self.get_function_text(func, i + 1)
            self.func_combobox.addItem(text)
            self.func_combobox.setItemData(i, func)
            self._func_to_index[func] = i

    def get_selected_function(self) -> str:
        return self.func_combobox.currentText()

    def set_selected_function(self, index: int):
        self.func_combobox.setCurrentIndex(index)


class FunctionListCard(CardWidget):
    checkbox_toggled = Signal(GameFunction, bool)
    all_toggled = Signal(bool)
    order_changed = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(20, 11, 11, 11)
        self.vBoxLayout.setSpacing(10)

        self.title_label = BodyLabel("功能选择列表")
        self.vBoxLayout.addWidget(self.title_label)

        self.list_widget = QListWidget()
        self.list_widget.setFixedHeight(300)

        self._function_items = []
        self._create_function_list()

        self.vBoxLayout.addWidget(self.list_widget)

    def _create_function_list(self):
        from PySide6.QtWidgets import QPushButton

        func_list = list(GameFunction)
        for i, func in enumerate(func_list):
            widget = QWidget()
            h_layout = QHBoxLayout(widget)
            h_layout.setContentsMargins(0, 0, 0, 0)
            h_layout.setSpacing(8)

            checkbox = QCheckBox(func.value)
            checkbox.setChecked(True)
            checkbox.setStyleSheet("QCheckBox { spacing: 8px; }")
            checkbox.toggled.connect(lambda checked, f=func: self._on_checkbox_toggled(f, checked))
            checkbox.setFixedHeight(24)

            up_btn = QPushButton("↑")
            up_btn.setFixedSize(24, 24)
            up_btn.clicked.connect(lambda checked, f=func: self._on_move_up(f))
            up_btn.setEnabled(i > 0)

            down_btn = QPushButton("↓")
            down_btn.setFixedSize(24, 24)
            down_btn.clicked.connect(lambda checked, f=func: self._on_move_down(f))
            down_btn.setEnabled(i < len(func_list) - 1)

            h_layout.addWidget(checkbox)
            h_layout.addStretch(1)
            h_layout.addWidget(up_btn)
            h_layout.addWidget(down_btn)

            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

            self._function_items.append((func, checkbox, up_btn, down_btn))

    def _on_checkbox_toggled(self, func: GameFunction, checked: bool):
        self.checkbox_toggled.emit(func, checked)

    def _on_move_up(self, func: GameFunction):
        index = next((i for i, (f, _, _, _) in enumerate(self._function_items) if f == func), -1)
        if index > 0:
            self._function_items[index], self._function_items[index - 1] = (
                self._function_items[index - 1],
                self._function_items[index],
            )
            self._refresh_list()
            func_order = [f for f, _, _, _ in self._function_items]
            self.order_changed.emit(func_order)

    def _on_move_down(self, func: GameFunction):
        index = next((i for i, (f, _, _, _) in enumerate(self._function_items) if f == func), -1)
        if index < len(self._function_items) - 1:
            self._function_items[index], self._function_items[index + 1] = (
                self._function_items[index + 1],
                self._function_items[index],
            )
            self._refresh_list()
            func_order = [f for f, _, _, _ in self._function_items]
            self.order_changed.emit(func_order)

    def _refresh_list(self):
        self.list_widget.clear()
        from PySide6.QtWidgets import QPushButton

        for i, (func, checkbox, up_btn, down_btn) in enumerate(self._function_items):
            widget = QWidget()
            h_layout = QHBoxLayout(widget)
            h_layout.setContentsMargins(0, 0, 0, 0)
            h_layout.setSpacing(8)

            new_checkbox = QCheckBox(func.value)
            new_checkbox.setChecked(checkbox.isChecked())
            new_checkbox.setStyleSheet("QCheckBox { spacing: 8px; }")
            new_checkbox.toggled.connect(lambda checked, f=func: self._on_checkbox_toggled(f, checked))
            new_checkbox.setFixedHeight(24)

            new_up_btn = QPushButton("↑")
            new_up_btn.setFixedSize(24, 24)
            new_up_btn.clicked.connect(lambda checked, f=func: self._on_move_up(f))
            new_up_btn.setEnabled(i > 0)

            new_down_btn = QPushButton("↓")
            new_down_btn.setFixedSize(24, 24)
            new_down_btn.clicked.connect(lambda checked, f=func: self._on_move_down(f))
            new_down_btn.setEnabled(i < len(self._function_items) - 1)

            h_layout.addWidget(new_checkbox)
            h_layout.addStretch(1)
            h_layout.addWidget(new_up_btn)
            h_layout.addWidget(new_down_btn)

            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

            self._function_items[i] = (func, new_checkbox, new_up_btn, new_down_btn)

    def get_selected_functions(self) -> list[tuple[GameFunction, bool]]:
        return [(func, checkbox.isChecked()) for func, checkbox, _, _ in self._function_items]

    def set_function_selected(self, func: GameFunction, selected: bool):
        for f, checkbox, _, _ in self._function_items:
            if f == func:
                checkbox.setChecked(selected)
                break

    def scroll_to_function(self, func: GameFunction):
        for i, (f, _, _, _) in enumerate(self._function_items):
            if f == func:
                self.list_widget.scrollToItem(self.list_widget.item(i))
                break

    def select_all(self):
        for _, checkbox, _, _ in self._function_items:
            checkbox.setChecked(True)
        self.all_toggled.emit(True)

    def deselect_all(self):
        for _, checkbox, _, _ in self._function_items:
            checkbox.setChecked(False)
        self.all_toggled.emit(False)

    def get_function_order(self) -> list[GameFunction]:
        return [func for func, _, _, _ in self._function_items]


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle("Game Function Selector")
    window.setFixedSize(400, 500)

    selector = GameFunctionSelectorWidget()
    layout = QVBoxLayout(window)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.addWidget(selector)

    window.show()
    sys.exit(app.exec())
