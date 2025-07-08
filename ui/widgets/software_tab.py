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
from software import PackageSearcher, PackageInstaller, ChocolateyManager
from software.package_search import PackageSearchWorker
from software.package_installer import PackageInstallWorker
from software.chocolatey_manager import ChocolateyInstallWorker


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
        
        # Backend managers
        self.chocolatey_manager = ChocolateyManager()
        self.package_searcher = PackageSearcher()
        self.package_installer = PackageInstaller()
        
        # Thread management
        self.search_thread: Optional[QThread] = None
        self.install_thread: Optional[QThread] = None
        self.choco_thread: Optional[QThread] = None
        
        self._init_ui()
        self._setup_connections()
        
        # Check Chocolatey status on startup
        self._check_chocolatey_status()
    
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
        self.package_table = QTableWidget(0, 4)
        self.package_table.setHorizontalHeaderLabels(["Select", "Package", "Version", "Description"])
        
        # Configure table
        header = self.package_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Select column
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)       # Package column
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Version column
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)           # Description column
        
        self.package_table.setColumnWidth(1, 200)
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
        
        # Clear output button
        clear_output_btn = QPushButton("Clear Output")
        clear_output_btn.clicked.connect(self.install_output.clear)
        output_layout.addWidget(clear_output_btn)
        
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
        self.install_btn.clicked.connect(self._install_selected)
        self.clear_btn.clicked.connect(self._clear_selection)
    
    def _check_chocolatey_status(self):
        """Check Chocolatey installation status on startup."""
        if not self.chocolatey_manager.is_chocolatey_installed():
            self.install_output.append("⚠ Warning: Chocolatey is not installed.")
            self.install_output.append("Package search and installation require Chocolatey.")
            self.install_output.append("Some features may not work until Chocolatey is installed.")
        else:
            version = self.chocolatey_manager.get_chocolatey_version()
            self.install_output.append(f"✓ Chocolatey is available (version: {version})")
    
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
            f"Loaded preset '{preset_name}' with {len(preset_packages)} packages.\n\n"
            "You can now install them or add more packages manually."
        )
    
    def _edit_presets_file(self):
        """Open the presets configuration file for editing."""
        import os
        import subprocess
        import platform
        
        config_file = self.config_manager.presets_file
        
        try:
            if platform.system() == "Windows":
                os.startfile(config_file)
            else:
                subprocess.run(["xdg-open", str(config_file)])
            
            QMessageBox.information(
                self,
                "Edit Presets", 
                f"Opening presets configuration file:\n{config_file}\n\n"
                "After editing, restart the application to see changes."
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Cannot Open File",
                f"Could not open presets file automatically.\n\n"
                f"File location: {config_file}\n\nError: {str(e)}"
            )
    
    def _search_packages(self):
        """Search for Chocolatey packages."""
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.information(self, "Search", "Please enter a search term")
            return
        
        # Check if Chocolatey is available
        if not self.chocolatey_manager.is_chocolatey_installed():
            QMessageBox.warning(
                self, 
                "Chocolatey Required", 
                "Chocolatey is required for package search.\n\n"
                "Would you like to install Chocolatey first?"
            )
            return
        
        # Stop any existing search thread
        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.quit()
            self.search_thread.wait()
        
        # Disable search button during search
        self.search_btn.setEnabled(False)
        self.search_btn.setText("Searching...")
        
        # Clear previous results
        self.package_table.setRowCount(0)
        
        # Create search options
        search_options = {
            'exact_match': self.exact_match_cb.isChecked(),
            'limit': 50  # Reasonable limit for UI display
        }
        
        # Create search worker and thread
        self.search_thread = QThread()
        self.search_worker = PackageSearchWorker(query, search_options)
        self.search_worker.moveToThread(self.search_thread)
        
        # Connect signals
        self.search_thread.started.connect(self.search_worker.run)
        self.search_worker.signals.progress.connect(self._on_search_progress)
        self.search_worker.signals.result.connect(self._on_search_complete)
        self.search_worker.signals.error.connect(self._on_search_error)
        self.search_worker.signals.finished.connect(self.search_thread.quit)
        self.search_worker.signals.finished.connect(self._on_search_finished)
        
        # Start the search
        self.search_thread.start()
    
    def _on_search_progress(self, message: str):
        """Handle search progress updates."""
        self.install_output.append(message)
    
    def _on_search_complete(self, packages):
        """Handle search completion with results."""
        self.package_table.setRowCount(len(packages))
        
        for row, package in enumerate(packages):
            # Checkbox for selection
            checkbox = QCheckBox()
            checkbox.stateChanged.connect(lambda state, pkg=package.name: self._on_package_checkbox_changed(pkg, state))
            self.package_table.setCellWidget(row, 0, checkbox)
            
            # Package name
            name_item = QTableWidgetItem(package.name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.package_table.setItem(row, 1, name_item)
            
            # Version
            version_item = QTableWidgetItem(package.version)
            version_item.setFlags(version_item.flags() & ~Qt.ItemIsEditable)
            self.package_table.setItem(row, 2, version_item)
            
            # Description
            description_item = QTableWidgetItem(package.description)
            description_item.setFlags(description_item.flags() & ~Qt.ItemIsEditable)
            self.package_table.setItem(row, 3, description_item)
        
        self.install_output.append(f"Found {len(packages)} packages")
    
    def _on_search_error(self, error_message: str):
        """Handle search errors."""
        self.install_output.append(f"Search error: {error_message}")
        QMessageBox.warning(self, "Search Error", f"Search failed: {error_message}")
    
    def _on_search_finished(self):
        """Handle search completion (success or failure)."""
        self.search_btn.setEnabled(True)
        self.search_btn.setText("Search")
    
    def _on_package_checkbox_changed(self, package_name: str, state: int):
        """Handle package checkbox state changes."""
        if state == Qt.Checked:
            self.selected_packages.add(package_name)
        else:
            self.selected_packages.discard(package_name)
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
        for row in range(self.package_table.rowCount()):
            checkbox = self.package_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(False)
    
    def _install_selected(self):
        """Install selected packages."""
        if not self.selected_packages:
            QMessageBox.information(self, "No Selection", "Please select at least one package to install.")
            return
        
        # Check if Chocolatey is available
        if not self.chocolatey_manager.is_chocolatey_installed():
            reply = QMessageBox.question(
                self,
                "Chocolatey Required", 
                "Chocolatey is required for package installation.\n\n"
                "Would you like to install Chocolatey first?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self._install_chocolatey()
            return
        
        # Confirm installation
        package_list = '\n'.join(f"• {pkg}" for pkg in sorted(self.selected_packages))
        reply = QMessageBox.question(
            self,
            "Confirm Installation",
            f"Install {len(self.selected_packages)} package(s)?\n\n{package_list}\n\n"
            "This may take several minutes.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Stop any existing install thread
        if self.install_thread and self.install_thread.isRunning():
            self.install_thread.quit()
            self.install_thread.wait()
        
        # Disable install button during installation
        self.install_btn.setEnabled(False)
        self.install_btn.setText("Installing...")
        
        # Create install worker and thread
        self.install_thread = QThread()
        self.install_worker = PackageInstallWorker(list(self.selected_packages))
        self.install_worker.moveToThread(self.install_thread)
        
        # Connect signals
        self.install_thread.started.connect(self.install_worker.run)
        self.install_worker.signals.progress.connect(self._on_install_progress)
        self.install_worker.signals.result.connect(self._on_install_complete)
        self.install_worker.signals.error.connect(self._on_install_error)
        self.install_worker.signals.finished.connect(self.install_thread.quit)
        self.install_worker.signals.finished.connect(self._on_install_finished)
        
        # Start the installation
        self.install_thread.start()
    
    def _install_chocolatey(self):
        """Install Chocolatey."""
        reply = QMessageBox.question(
            self,
            "Install Chocolatey",
            "This will install Chocolatey package manager.\n\n"
            "Administrator privileges are required.\n"
            "This may take several minutes.\n\n"
            "Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Stop any existing choco thread
        if self.choco_thread and self.choco_thread.isRunning():
            self.choco_thread.quit()
            self.choco_thread.wait()
        
        # Create Chocolatey install worker and thread
        self.choco_thread = QThread()
        self.choco_worker = ChocolateyInstallWorker()
        self.choco_worker.moveToThread(self.choco_thread)
        
        # Connect signals
        self.choco_thread.started.connect(self.choco_worker.run)
        self.choco_worker.signals.progress.connect(self._on_install_progress)
        self.choco_worker.signals.result.connect(self._on_chocolatey_install_complete)
        self.choco_worker.signals.error.connect(self._on_install_error)
        self.choco_worker.signals.finished.connect(self.choco_thread.quit)
        self.choco_worker.signals.finished.connect(self._on_install_finished)
        
        # Start Chocolatey installation
        self.choco_thread.start()
    
    def _on_install_progress(self, message: str):
        """Handle installation progress updates."""
        self.install_output.append(message)
        # Auto-scroll to bottom
        self.install_output.verticalScrollBar().setValue(
            self.install_output.verticalScrollBar().maximum()
        )
    
    def _on_install_complete(self, results):
        """Handle installation completion."""
        successful = [r for r in results if r.status.value == "success"]
        failed = [r for r in results if r.status.value == "failed"]
        
        if successful:
            QMessageBox.information(
                self,
                "Installation Complete",
                f"Successfully installed {len(successful)} out of {len(results)} packages!\n\n"
                f"See output for details."
            )
        else:
            QMessageBox.warning(
                self,
                "Installation Failed",
                f"No packages were successfully installed.\n\n"
                f"See output for error details."
            )
    
    def _on_chocolatey_install_complete(self, success: bool):
        """Handle Chocolatey installation completion."""
        if success:
            QMessageBox.information(
                self,
                "Chocolatey Installed",
                "Chocolatey has been installed successfully!\n\n"
                "You can now search and install packages."
            )
        else:
            QMessageBox.warning(
                self,
                "Installation Failed",
                "Chocolatey installation failed.\n\n"
                "See output for error details."
            )
    
    def _on_install_error(self, error_message: str):
        """Handle installation errors."""
        self.install_output.append(f"Error: {error_message}")
    
    def _on_install_finished(self):
        """Handle installation completion (success or failure)."""
        self.install_btn.setEnabled(True)
        self.install_btn.setText("Install Selected Packages")
    
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