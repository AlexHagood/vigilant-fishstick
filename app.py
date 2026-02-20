import sys
from typing import List, Optional
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QListWidget, QTextEdit, QLabel, QPushButton, QDoubleSpinBox, QListWidgetItem
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from backend import Backend, Skin
import pandas as pd

class RowWidget(QWidget):
    def __init__(
        self, 
        skin: Skin,
        parent_list: QListWidget,
        parent_calculator: 'TradeCalculator',
    ) -> None:
        super().__init__()

        self.parent_list: QListWidget = parent_list
        self.parent_calculator: 'TradeCalculator' = parent_calculator
        self.skin: Skin = skin

        layout: QHBoxLayout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)

        # Left text
        self.label: QLabel = QLabel(skin.name)
        self.label.setStyleSheet(f"color: {skin.get_color().name()};")

        # Float input
        self.spinbox: QDoubleSpinBox = QDoubleSpinBox()
        self.spinbox.setDecimals(2)
        self.spinbox.setRange(self.skin.min_float, self.skin.max_float)
        self.spinbox.setSingleStep(0.01)
        self.spinbox.setFixedWidth(100)
        
        # Set default value to min float and update skin.float
        self.skin.float = self.skin.min_float
        self.spinbox.setValue(self.skin.min_float)
        
        self.spinbox.valueChanged.connect(self.on_value_changed)

        # Delete button
        self.delete_btn: QPushButton = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_self)

        layout.addWidget(self.label)
        layout.addStretch()
        layout.addWidget(self.spinbox)
        layout.addWidget(self.delete_btn)

        self.setLayout(layout)
    
    def on_value_changed(self) -> None:
        """Called when the spinbox value changes"""
        self.skin.float = self.spinbox.value()
        self.parent_calculator.analyze_and_display_selection()

    def delete_self(self) -> None:
        # Find and remove this row from the list
        for i in range(self.parent_list.count()):
            if self.parent_list.itemWidget(self.parent_list.item(i)) == self:
                self.parent_list.takeItem(i)
                break
        
        # Reset the filter when an item is deleted
        self.parent_calculator.reset_filter()
        
        # Update the analysis after deletion
        self.parent_calculator.analyze_and_display_selection()

class TradeCalculator(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Searchable List UI")
        self.resize(800, 1200)

        self.backend: Backend = Backend(self)
        
        # Get list of all item IDs (already filtered by backend)
        self.item_ids: List[int] = self.backend.get_item_list()
        
        # Pre-build lookup dictionaries for fast filtering (cache skin properties)
        self._id_to_name = {}
        self._id_to_rarity = {}
        for item_id in self.item_ids:
            skin = self.backend.get_skin(item_id)
            self._id_to_name[item_id] = skin.name.lower()
            self._id_to_rarity[item_id] = skin.rarity
        
        self.current_rarity_filter: Optional[str] = None  # Track current rarity filter

        self.init_ui()

    def init_ui(self) -> None:
        main_layout: QVBoxLayout = QVBoxLayout()
        
        # Search bar
        self.search_bar: QLineEdit = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.textChanged.connect(self.filter_list)

        # Horizontal layout for left/right
        content_layout: QHBoxLayout = QHBoxLayout()

        # Left list
        self.list_widget: QListWidget = QListWidget()
        self.populate_list(self.item_ids)
        self.list_widget.itemClicked.connect(self.show_item)

        # Right display
        self.detail_view: QListWidget = QListWidget()
        self.detail_view.setDisabled(False)

        content_layout.addWidget(self.list_widget, 1)
        content_layout.addWidget(self.detail_view, 2)

        main_layout.addWidget(self.search_bar)
        main_layout.addLayout(content_layout)

        self.setLayout(main_layout)

        self.output_box: QTextEdit = QTextEdit()
        self.output_box.setReadOnly(True)
        main_layout.addWidget(self.output_box)

    def populate_list(self, item_ids: List[int]) -> None:
        """Add items to the list with rarity-based colors"""
        from PyQt6.QtGui import QBrush
        
        for item_id in item_ids:
            skin = self.backend.get_skin(item_id)
            list_item: QListWidgetItem = QListWidgetItem(skin.name)
            list_item.setData(Qt.ItemDataRole.UserRole, item_id)  # Store ID in item
            list_item.setForeground(QBrush(skin.get_color()))
            self.list_widget.addItem(list_item)

    def filter_list(self, text: str) -> None:
        """Fast filtering using cached name lookups"""
        self.list_widget.clear()
        if not text:
            self.populate_list(self.item_ids)
            return
            
        text_lower = text.lower()
        filtered_ids = [item_id for item_id in self.item_ids 
                       if text_lower in self._id_to_name[item_id]]
        self.populate_list(filtered_ids)
    
    def filter_by_rarity(self, rarity: str) -> None:
        """Fast filtering by rarity using cached lookups"""
        self.list_widget.clear()
        self.current_rarity_filter = rarity
        
        search_text = self.search_bar.text().lower()
        
        if search_text:
            filtered_ids = [item_id for item_id in self.item_ids 
                           if self._id_to_rarity[item_id] == rarity 
                           and search_text in self._id_to_name[item_id]]
        else:
            filtered_ids = [item_id for item_id in self.item_ids 
                           if self._id_to_rarity[item_id] == rarity]
        
        self.populate_list(filtered_ids)
    
    def reset_filter(self) -> None:
        """Reset the rarity filter and show all items"""
        self.current_rarity_filter = None
        search_text = self.search_bar.text()
        if search_text:
            self.filter_list(search_text)
        else:
            self.list_widget.clear()
            self.populate_list(self.item_ids)

    def show_item(self, item: QListWidgetItem) -> None:
        # Get the item ID from the list item
        item_id: int = item.data(Qt.ItemDataRole.UserRole)
        
        # Create a Skin instance
        skin: Skin = self.backend.get_skin(item_id)
        
        # Filter the left list to show only items with the same rarity
        self.filter_by_rarity(skin.rarity)
        
        # Create a list item
        list_item: QListWidgetItem = QListWidgetItem(self.detail_view)
        
        # Create the custom row widget with skin
        row_widget: RowWidget = RowWidget(skin, self.detail_view, self)
        
        # Set size hint so the item is tall enough for the widget
        list_item.setSizeHint(row_widget.sizeHint())
        
        # Add the item and set the custom widget
        self.detail_view.addItem(list_item)
        self.detail_view.setItemWidget(list_item, row_widget)
        
        # Analyze and display the selected items
        self.analyze_and_display_selection()
    
    def analyze_and_display_selection(self) -> None:
        """Collect all selected skins and analyze them"""
        selected_skins: List[Skin] = []
        
        # Iterate through all items in the detail view
        for i in range(self.detail_view.count()):
            widget = self.detail_view.itemWidget(self.detail_view.item(i))
            if isinstance(widget, RowWidget):
                selected_skins.append(widget.skin)
        
        # Get analysis from backend
        analysis_result: str = self.backend.analyze_selected_skins(selected_skins)
        
        # Update output
        self.update_output(f"Selected {len(selected_skins)} items\n\n{analysis_result}")

    def update_output(self, text: str) -> None:
        self.output_box.setText(text)

app: QApplication = QApplication(sys.argv)
window: TradeCalculator = TradeCalculator()
window.show()
sys.exit(app.exec())