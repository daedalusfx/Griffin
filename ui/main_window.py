# ui/main_window.py
# Contains the MainWindow class, with bug fixes and stability improvements.

import os
import logging
import warnings
import pandas as pd
from dotenv import load_dotenv
import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QGroupBox, QTabWidget, QTableView,
    QListWidget, QComboBox, QSpinBox, QProgressBar, QStatusBar, QMessageBox,
    QListWidgetItem, QSizePolicy
)
from PyQt6.QtCore import QThreadPool, pyqtSlot, Qt

from core.analysis_engine import AnalysisEngine
from utils.worker import Worker
from utils.pandas_model import PandasModel

# --- Basic Configuration ---
warnings.simplefilter("ignore")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()
pg.setConfigOption('background', '#2E3440')
pg.setConfigOption('foreground', '#D8DEE9')

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Intelligent Broker Analyzer v1.5 (Stable)")
        self.setGeometry(100, 100, 1200, 700)
        self.thread_pool = QThreadPool()
        self.analysis_engine = AnalysisEngine()
        self.init_ui()
        self.apply_stylesheet()
        self.load_settings()

    def init_ui(self):
        """Initializes all UI components."""
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        # --- Left Panel ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setFixedWidth(350)

        # DB Settings
        db_group = QGroupBox("InfluxDB Connection")
        db_layout = QVBoxLayout()
        self.db_url = QLineEdit()
        self.db_token = QLineEdit()
        self.db_org = QLineEdit()
        self.db_bucket = QLineEdit()
        self.db_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.fetch_button = QPushButton("Fetch Data from DB")
        db_layout.addWidget(QLabel("URL:"))
        db_layout.addWidget(self.db_url)
        db_layout.addWidget(QLabel("Token:"))
        db_layout.addWidget(self.db_token)
        db_layout.addWidget(QLabel("Organization:"))
        db_layout.addWidget(self.db_org)
        db_layout.addWidget(QLabel("Bucket:"))
        db_layout.addWidget(self.db_bucket)
        db_layout.addWidget(self.fetch_button)
        db_group.setLayout(db_layout)

        # Analysis Settings
        self.analysis_group = QGroupBox("Analysis Parameters")
        analysis_layout = QVBoxLayout()
        self.symbol_combo = QComboBox()
        self.timeframe_combo = QComboBox()
        self.min_points_spin = QSpinBox()
        self.min_points_spin.setRange(50, 1000)
        self.min_points_spin.setValue(240)
        analysis_layout.addWidget(QLabel("Symbol:"))
        analysis_layout.addWidget(self.symbol_combo)
        analysis_layout.addWidget(QLabel("Timeframe:"))
        analysis_layout.addWidget(self.timeframe_combo)
        analysis_layout.addWidget(QLabel("Minimum Data Points:"))
        analysis_layout.addWidget(self.min_points_spin)
        self.analysis_group.setLayout(analysis_layout)

        # Broker List
        self.broker_group = QGroupBox("Broker Selection")
        broker_layout = QVBoxLayout()
        broker_button_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.deselect_all_btn = QPushButton("Deselect All")
        broker_button_layout.addWidget(self.select_all_btn)
        broker_button_layout.addWidget(self.deselect_all_btn)
        self.broker_list_widget = QListWidget()
        broker_layout.addLayout(broker_button_layout)
        broker_layout.addWidget(self.broker_list_widget)
        self.broker_group.setLayout(broker_layout)

        # Control Button
        self.start_button = QPushButton("Start Analysis")
        
        left_layout.addWidget(db_group)
        left_layout.addWidget(self.analysis_group)
        left_layout.addWidget(self.broker_group)
        left_layout.addWidget(self.start_button)
        
        # --- Right Panel: Output ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        self.tabs = QTabWidget()
        self.plot_tab = QWidget()
        self.report_tab = QWidget()
        self.tabs.addTab(self.plot_tab, "Cluster Plot")
        self.tabs.addTab(self.report_tab, "Detailed Report")
        
        self.plot_layout = QVBoxLayout(self.plot_tab)
        self.plot_widget = pg.PlotWidget()
        self.plot_layout.addWidget(self.plot_widget)

        # FIX: Initialize hover text and connect signal only once
        self.hover_text = pg.TextItem("", anchor=(0, 1), color='#FFFFFF', fill=pg.mkBrush(0,0,0,150))
        self.plot_widget.addItem(self.hover_text)
        self.plot_widget.scene().sigMouseMoved.connect(self.on_mouse_hover)

        self.report_layout = QVBoxLayout(self.report_tab)
        self.report_table = QTableView()
        self.report_layout.addWidget(self.report_table)

        right_layout.addWidget(self.tabs)

        # --- Status Bar ---
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.progress_bar = QProgressBar()
        self.status_bar.addPermanentWidget(self.progress_bar)

        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)

        # --- Initial State & Connections ---
        self.set_analysis_controls_enabled(False)
        self.fetch_button.clicked.connect(self.fetch_metadata)
        self.start_button.clicked.connect(self.run_analysis)
        self.select_all_btn.clicked.connect(self.select_all_brokers)
        self.deselect_all_btn.clicked.connect(self.deselect_all_brokers)
        self.analysis_engine.finished.connect(self.on_analysis_finished)
        self.analysis_engine.progress.connect(self.update_progress)
        self.analysis_engine.error.connect(self.show_error)
        self.analysis_engine.metadata_found.connect(self.on_metadata_found)

    def set_analysis_controls_enabled(self, enabled):
        """Helper to enable/disable all analysis-related controls."""
        self.analysis_group.setEnabled(enabled)
        self.broker_group.setEnabled(enabled)
        self.start_button.setEnabled(enabled)

    def load_settings(self):
        self.db_url.setText(os.getenv("INFLUX_URL", ""))
        self.db_token.setText(os.getenv("INFLUX_TOKEN", ""))
        self.db_org.setText(os.getenv("INFLUX_ORG", ""))
        self.db_bucket.setText(os.getenv("INFLUX_BUCKET", ""))

    def fetch_metadata(self):
        self.fetch_button.setEnabled(False)
        self.set_analysis_controls_enabled(False)
        self.status_bar.showMessage("Fetching metadata from database...")
        self.progress_bar.setValue(0)
        settings = {"url": self.db_url.text(), "token": self.db_token.text(), "org": self.db_org.text(), "bucket": self.db_bucket.text()}
        worker = Worker(self.analysis_engine.fetch_metadata, settings)
        self.thread_pool.start(worker)

    def run_analysis(self):
        self.start_button.setEnabled(False)
        self.fetch_button.setEnabled(False)
        self.status_bar.showMessage("Starting analysis...")
        self.progress_bar.setValue(0)
        
        selected_brokers = [self.broker_list_widget.item(i).text() for i in range(self.broker_list_widget.count()) if self.broker_list_widget.item(i).checkState() == Qt.CheckState.Checked]
        if not selected_brokers:
            self.show_error("Please select at least one broker.")
            return

        settings = {
            "url": self.db_url.text(), "token": self.db_token.text(), "org": self.db_org.text(),
            "bucket": self.db_bucket.text(), "brokers": selected_brokers,
            "symbol": self.symbol_combo.currentText(), "timeframe": self.timeframe_combo.currentText(),
            "min_points": self.min_points_spin.value(), "min_brokers": 2
        }
        worker = Worker(self.analysis_engine.run_analysis, settings)
        self.thread_pool.start(worker)

    def select_all_brokers(self):
        for i in range(self.broker_list_widget.count()):
            self.broker_list_widget.item(i).setCheckState(Qt.CheckState.Checked)

    def deselect_all_brokers(self):
        for i in range(self.broker_list_widget.count()):
            self.broker_list_widget.item(i).setCheckState(Qt.CheckState.Unchecked)

    @pyqtSlot(int, str)
    def update_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.status_bar.showMessage(message)

    @pyqtSlot(dict)
    def on_metadata_found(self, metadata):
        self.fetch_button.setEnabled(True)
        self.status_bar.showMessage("Metadata loaded. Please select parameters and start analysis.", 5000)
        
        self.broker_list_widget.clear()
        for broker in sorted(metadata['brokers']):
            item = QListWidgetItem(broker)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.broker_list_widget.addItem(item)
            
        self.symbol_combo.clear()
        self.symbol_combo.addItems(sorted(metadata['symbols']))
        self.timeframe_combo.clear()
        self.timeframe_combo.addItems(sorted(metadata['timeframes']))
        
        self.set_analysis_controls_enabled(True)

    @pyqtSlot(pd.DataFrame, pd.DataFrame)
    def on_analysis_finished(self, report_df, pca_df):
        self.start_button.setEnabled(True)
        self.fetch_button.setEnabled(True)
        self.status_bar.showMessage("Analysis finished successfully.", 5000)
        self.draw_plot(pca_df)
        model = PandasModel(report_df.reset_index().round(4))
        self.report_table.setModel(model)
        self.report_table.resizeColumnsToContents()
        self.tabs.setCurrentWidget(self.plot_tab)
    
    def draw_plot(self, pca_df):
        """Draws the cluster plot using PyQtGraph."""
        try:
            self.plot_widget.clear()
            variance = pca_df.attrs.get('explained_variance', [0, 0])
            self.plot_widget.setTitle("Broker Clustering Map", size="12pt")
            self.plot_widget.setLabel('left', f"Principal Component 2 ({variance[1]:.1%} variance)")
            self.plot_widget.setLabel('bottom', f"Principal Component 1 ({variance[0]:.1%} variance)")
            self.plot_widget.showGrid(x=True, y=True)
            
            legend = self.plot_widget.addLegend()
            
            # FIX: Use pyqtgraph's built-in colormap instead of relying on matplotlib
            colors = pg.colormap.get('viridis').getColors(mode='qcolor')
            
            for i, profile_name in enumerate(pca_df['Profile'].unique()):
                color_index = int(i * (len(colors) - 1) / max(1, len(pca_df['Profile'].unique()) - 1))
                color = colors[color_index]
                cluster_data = pca_df[pca_df['Profile'] == profile_name]
                
                scatter = pg.ScatterPlotItem(
                    size=10,
                    pen=pg.mkPen(None),
                    brush=pg.mkBrush(color),
                    name=profile_name
                )

                spots = [{'pos': [row.PC1, row.PC2], 'data': row.Index} for row in cluster_data.itertuples()]
                scatter.addPoints(spots)
                self.plot_widget.addItem(scatter)
                
                for spot in spots:
                    text = pg.TextItem(spot['data'], anchor=(0.5, 1.5), color='#D8DEE9')
                    text.setPos(spot['pos'][0], spot['pos'][1])
                    self.plot_widget.addItem(text)
        except Exception as e:
            logging.error(f"Failed to draw plot: {e}", exc_info=True)
            self.show_error(f"An error occurred while drawing the plot: {e}")

    def on_mouse_hover(self, pos):
        """Shows broker name when hovering over a point."""
        try:
            point = self.plot_widget.getViewBox().mapSceneToView(pos)
            items = self.plot_widget.scene().items(pos)
            scatter_items = [item for item in items if isinstance(item, pg.ScatterPlotItem)]
            
            if scatter_items:
                points_at_pos = scatter_items[0].pointsAt(point)
                if len(points_at_pos) > 0:
                    broker_name = points_at_pos[0].data()
                    self.hover_text.setText(f"Broker: {broker_name}")
                    self.hover_text.setPos(point)
                    return
            self.hover_text.setText("")
        except Exception:
            # Failsafe in case of any unexpected error during hover event
            self.hover_text.setText("")

    @pyqtSlot(str)
    def show_error(self, message):
        """Shows a more user-friendly error message box."""
        self.start_button.setEnabled(True)
        self.fetch_button.setEnabled(True)
        self.status_bar.showMessage(f"Error: {message}", 5000)
        self.progress_bar.setValue(0)
        
        if "No broker had enough data" in message:
            friendly_message = ("Analysis Failed: No Data\n\n"
                                "None of the selected brokers had enough data points "
                                "for the chosen symbol and timeframe.\n\n"
                                "Please try:\n"
                                "- Selecting a different symbol or timeframe.\n"
                                "- Choosing other brokers.\n"
                                "- Lowering the 'Minimum Data Points' value.")
            QMessageBox.warning(self, "Data Error", friendly_message)
        else:
            QMessageBox.critical(self, "Error", message)

    def apply_stylesheet(self):
        qss = """
            QWidget { background-color: #2E3440; color: #D8DEE9; font-size: 14px; }
            QMainWindow { border: 1px solid #4C566A; }
            QGroupBox { border: 1px solid #4C566A; border-radius: 5px; margin-top: 1ex; font-weight: bold; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 3px; }
            QLineEdit, QSpinBox, QComboBox { background-color: #434C5E; border: 1px solid #4C566A; border-radius: 4px; padding: 5px; }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus { border-color: #88C0D0; }
            QPushButton { background-color: #5E81AC; color: #ECEFF4; border: none; padding: 8px 16px; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #81A1C1; }
            QPushButton:pressed { background-color: #88C0D0; }
            QPushButton:disabled { background-color: #4C566A; color: #6a7388; }
            QTabWidget::pane { border: 1px solid #4C566A; border-radius: 4px; }
            QTabBar::tab { background: #434C5E; color: #D8DEE9; padding: 8px; border-top-left-radius: 4px; border-top-right-radius: 4px; border: 1px solid #4C566A; border-bottom: none; }
            QTabBar::tab:selected { background: #5E81AC; color: #ECEFF4; }
            QTableView { gridline-color: #4C566A; border: 1px solid #4C566A; }
            QHeaderView::section { background-color: #434C5E; padding: 4px; border: 1px solid #4C566A; font-weight: bold; }
            QStatusBar { color: #D8DEE9; }
            QProgressBar { border: 1px solid #4C566A; border-radius: 4px; text-align: center; color: #ECEFF4; }
            QProgressBar::chunk { background-color: #88C0D0; border-radius: 4px; }
            QListWidget { background-color: #3B4252; border: 1px solid #4C566A; border-radius: 4px; }
        """
        self.setStyleSheet(qss)
