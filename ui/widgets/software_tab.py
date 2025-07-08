"""
Software management tab widget.

This module contains the UI components for software package management,
including search, selection, installation, and preset management.
"""

from typing import Set, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QTextEdit, QListWidget, QComboBox,
    QMessageBox, QCheckBox, QGroupBox, QHeaderView, QSizePolicy
)
from PySide6.QtCore import Qt, QThread

from core import ConfigManager


class SoftwareTab(QWidget):
    """
    Software management tab widget.
    
    This widget provides the interface for searching, selecting, and installing
    software packages, as well as managing software presets.
    """
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager
        self.selected_packages: Set[str] = set()
        
        # Thread management
        self.search_thread: Optional[QThread] = None
        self.install_thread: Optional[QThread] = None
        self.choco_thread: Optional[QThread] = None
        
        self._init_ui()
        self._setup_connections()
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        
        # Presets section
        presets_group = self._create_presets_section()
        layout.addWidget(presets_group, 0)
        
        # Search section
        search_group = self._create_search_section()
        layout.addWidget(search_group, 1)
        
        # Selected packages section
        selection_group = self._create_selection_section()
        layout.addWidget(selection_group, 0)
        
        # Installation output section
        output_group = self._create_output_section()
        layout.addWidget(output_group, 0)
        
        self.setLayout(layout)
    
    def _create_presets_section(self) -> QGroupBox:
        """Create the software presets section."""
        presets_group = QGroupBox("Software Presets")
        presets_layout = QHBoxLayout()
        
        presets_layout.addWidget(QLabel("Quick Install Presets:"))
        
        # Preset dropdown
        self.preset_combo = QComboBox()
        self._refresh_preset_combo()
        presets_layout.addWidget(self.preset_combo)
        
        # Load preset button
        self.load_preset_btn = QPushButton("Load Preset")
        self.load_preset_btn.setStyleSheet(
            "QPushButton { background-color: #9C27B0; color: white; font-weight: bold; }"
        )
        presets_layout.addWidget(self.load_preset_btn)
        
        # Edit presets button
        self.edit_presets_btn = QPushButton("Edit Presets File")
        presets_layout.addWidget(self.edit_presets_btn)
        
        presets_layout.addStretch()
        presets_group.setLayout(presets_layout)
        
        return presets_group
    
    def _create_search_section(self) -> QGroupBox:
        """Create the package search section."""
        search_group = QGroupBox("Package Search")
        search_layout = QVBoxLayout()
        
        # Search controls
        search_controls_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Chocolatey packages (e.g., 'chrome', 'firefox')")
        search_controls_layout.addWidget(self.search_input)
        
        self.search_btn = QPushButton("Search")
        search_controls_layout.addWidget(self.search_btn)
        
        self.exact_match_cb = QCheckBox("Exact name match only")
        self.exact_match_cb.setToolTip("Check this to only show packages with exact name matches")
        search_controls_layout.addWidget(self.exact_match_cb)
        
        search_layout.addLayout(search_controls_layout, 0)
        
        # Package table
        self.package_table = QTableWidget(0, 3)
        self.package_table.setHorizontalHeaderLabels(["Package", "Version", "Description"])
        
        # Configure table
        header = self.package_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        self.package_table.setColumnWidth(0, 200)
        self.package_table.setColumnWidth(1, 100)
        self.package_table.setMinimumHeight(200)
        self.package_table.setAlternatingRowColors(True)
        self.package_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.package_table.verticalHeader().setVisible(False)
        self.package_table.setShowGrid(True)
        self.package_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        search_layout.addWidget(self.package_table, 1)
        search_group.setLayout(search_layout)
        search_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        return search_group
    
    def _create_selection_section(self) -> QGroupBox:
        """Create the selected packages section."""
        selection_group = QGroupBox("Selected Packages")
        selection_layout = QVBoxLayout()
        
        # Selected packages list
        self.selected_list = QListWidget()
        self.selected_list.setMaximumHeight(100)
        selection_layout.addWidget(self.selected_list)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        self.install_btn = QPushButton("Install Selected Packages")
        self.install_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }"
        )
        buttons_layout.addWidget(self.install_btn)
        
        self.clear_btn = QPushButton("Clear Selection")
        buttons_layout.addWidget(self.clear_btn)
        
        buttons_layout.addStretch()
        selection_layout.addLayout(buttons_layout)
        
        selection_group.setLayout(selection_layout)
        return selection_group
    
    def _create_output_section(self) -> QGroupBox:
        """Create the installation output section."""
        output_group = QGroupBox("Installation Output")
        output_layout = QVBoxLayout()
        
        self.install_output = QTextEdit()
        self.install_output.setReadOnly(True)
        self.install_output.setMaximumHeight(200)
        output_layout.addWidget(self.install_output)
        
        output_group.setLayout(output_layout)
        return output_group
    
    def _setup_connections(self):
        """Setup signal connections."""
        # Preset connections
        self.load_preset_btn.clicked.connect(self._load_preset_packages)
        self.edit_presets_btn.clicked.connect(self._edit_presets_file)
        
        # Search connections
        self.search_input.returnPressed.connect(self._search_packages)
        self.search_btn.clicked.connect(self._search_packages)
        
        # Selection connections
        self.package_table.cellChanged.connect(self._handle_checkbox_change)
        self.install_btn.clicked.connect(self._install_selected)
        self.clear_btn.clicked.connect(self._clear_selection)
    
    def _refresh_preset_combo(self):
        """Refresh the preset combo box with available presets."""
        self.preset_combo.clear()
        self.preset_combo.addItem("Select a preset...")
        
        presets = self.config_manager.get_preset_names()
        for preset_name in presets:
            self.preset_combo.addItem(preset_name)
    
    def _load_preset_packages(self):
        """Load packages from the selected preset."""
        preset_name = self.preset_combo.currentText()
        if preset_name == "Select a preset...":
            QMessageBox.information(self, "No Selection", "Please select a preset to load.")
            return
        
        preset_packages = self.config_manager.get_preset(preset_name)
        if not preset_packages:
            QMessageBox.warning(self, "Preset Error", f"Preset '{preset_name}' not found or empty.")
            return
        
        # Clear current selection and add preset packages
        self._clear_selection()
        for package in preset_packages:
            self.selected_packages.add(package)
        
        self._refresh_selected_list()
        
        # Update output
        self.install_output.append(f"Loaded preset '{preset_name}' with {len(preset_packages)} packages:")
        for package in preset_packages:
            self.install_output.append(f"  • {package}")
        
        QMessageBox.information(
            self,
            "Preset Loaded",
            f"Loaded preset '{preset_name}' with {len(preset_packages)} packages.\\n\\n"
            "You can now install them or add more packages manually."
        )
    
    def _edit_presets_file(self):
        """Open the presets configuration file for editing."""
        import os
        import subprocess
        import platform
        
        config_file = self.config_manager.app_path / self.config_manager.presets_file.name
        
        try:
            if platform.system() == "Windows":
                os.startfile(config_file)
            else:
                subprocess.run(["xdg-open", str(config_file)])
            
            QMessageBox.information(
                self,
                "Edit Presets", 
                f"Opening presets configuration file:\\n{config_file}\\n\\n"
                "After editing, restart the application to see changes."
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Cannot Open File",
                f"Could not open presets file automatically.\\n\\n"
                f"File location: {config_file}\\n\\nError: {str(e)}"
            )
    
    def _search_packages(self):
        """Search for Chocolatey packages."""
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.information(self, "Search", "Please enter a search term")
            return
        
        # TODO: Implement package search using software module
        # This will be implemented when we create the software management module
        self.install_output.append(f"Searching for packages containing '{query}'...")
        self.install_output.append("Note: Package search will be implemented in the software management module.")
    
    def _handle_checkbox_change(self, row: int, column: int):
        """Handle package selection changes in the table."""
        if column == 0:  # Only handle checkbox changes in package name column
            item = self.package_table.item(row, column)
            if item:
                pkg_name = item.text()
                if item.checkState() == Qt.Checked:
                    self.selected_packages.add(pkg_name)
                else:
                    self.selected_packages.discard(pkg_name)
                self._refresh_selected_list()
    
    def _refresh_selected_list(self):
        """Update the selected packages list display."""
        self.selected_list.clear()
        for pkg in sorted(self.selected_packages):
            self.selected_list.addItem(pkg)
    
    def _clear_selection(self):
        """Clear all selected packages."""
        self.selected_packages.clear()
        self._refresh_selected_list()
        
        # Update checkboxes in table
        self.package_table.blockSignals(True)
        for row in range(self.package_table.rowCount()):
            item = self.package_table.item(row, 0)
            if item:
                item.setCheckState(Qt.Unchecked)
        self.package_table.blockSignals(False)
    
    def _install_selected(self):
        """Install selected packages."""
        if not self.selected_packages:
            QMessageBox.information(self, "No Selection", "Please select at least one package to install.")
            return
        
        # TODO: Implement package installation using software module
        # This will be implemented when we create the software management module
        package_list = '\\n'.join(f"• {pkg}" for pkg in sorted(self.selected_packages))
        self.install_output.append(f"Would install {len(self.selected_packages)} package(s):")
        self.install_output.append(package_list)
        self.install_output.append("Note: Package installation will be implemented in the software management module.")
    
    def cleanup(self):
        """Cleanup resources when the tab is closed."""
        # Stop any running threads
        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.quit()
            self.search_thread.wait()
        
        if self.install_thread and self.install_thread.isRunning():
            self.install_thread.quit()
            self.install_thread.wait()
        
        if self.choco_thread and self.choco_thread.isRunning():
            self.choco_thread.quit()
            self.choco_thread.wait()
    
    def get_selected_packages(self) -> Set[str]:
        """Get the currently selected packages."""
        return self.selected_packages.copy()
    
    def add_package_to_selection(self, package_name: str):
        """Add a package to the selection."""
        self.selected_packages.add(package_name)
        self._refresh_selected_list()
    
    def remove_package_from_selection(self, package_name: str):
        """Remove a package from the selection."""
        self.selected_packages.discard(package_name)
        self._refresh_selected_list()
    
    def set_selected_packages(self, packages: Set[str]):
        """Set the selected packages."""
        self.selected_packages = packages.copy()
        self._refresh_selected_list()
