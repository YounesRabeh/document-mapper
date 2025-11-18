
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QCheckBox, QHBoxLayout
)
import pandas as pd
import pyqtgraph as pg
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

# Sample data
df = pd.DataFrame({
    "HRV": [70, 65, 80, 75, 60],
    "BPM": [120, 130, 110, 125, 140],
    "HRV_2": [68, 66, 79, 74, 62],
    "BPM_2": [118, 132, 108, 127, 138],
    "Micronutrient": ["Vitamin C", "Iron", "Calcium", "Vitamin D", "Magnesium"],
    "Value": [20, 15, 25, 10, 30]
})

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Health Data Demo with Clickable Pie Chart")
        central = QWidget()
        layout = QVBoxLayout()
        central.setLayout(layout)
        self.setCentralWidget(central)

        # --- PyQtGraph scatter plot ---
        self.scatter_plot = pg.PlotWidget(title="HRV vs BPM")
        self.scatter_plot.setBackground('w')
        self.scatter_plot.addLegend()
        layout.addWidget(self.scatter_plot)

        # Scatter plot items
        self.series1 = self.scatter_plot.plot(
            df["HRV"], df["BPM"], pen=None, symbol='o', symbolBrush='r', name='Series 1'
        )
        self.series2 = self.scatter_plot.plot(
            df["HRV_2"], df["BPM_2"], pen=None, symbol='t', symbolBrush='b', name='Series 2'
        )

        # Zoom / pan restriction
        self.scatter_plot.setLimits(xMin=50, xMax=100, yMin=100, yMax=150)

        # --- Legend / checkboxes to show/hide series ---
        checkbox_layout = QHBoxLayout()
        layout.addLayout(checkbox_layout)
        self.checkbox1 = QCheckBox("Show Series 1")
        self.checkbox1.setChecked(True)
        self.checkbox1.stateChanged.connect(self.toggle_series1)
        checkbox_layout.addWidget(self.checkbox1)

        self.checkbox2 = QCheckBox("Show Series 2")
        self.checkbox2.setChecked(True)
        self.checkbox2.stateChanged.connect(self.toggle_series2)
        checkbox_layout.addWidget(self.checkbox2)

        # --- Matplotlib pie chart with clickable slices ---
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)
        self.draw_pie_chart()

    def draw_pie_chart(self):
        self.ax.clear()
        wedges, texts, autotexts = self.ax.pie(
            df["Value"], labels=df["Micronutrient"], autopct='%1.1f%%', startangle=90
        )
        # Make wedges pickable
        for wedge in wedges:
            wedge.set_picker(True)
        # Connect click event
        self.fig.canvas.mpl_connect('pick_event', self.on_slice_click)
        self.canvas.draw()

    def on_slice_click(self, event):
        wedge = event.artist
        label = wedge.get_label() if hasattr(wedge, 'get_label') else 'Unknown'
        print(f"Clicked on slice: {label}")

    # Toggle visibility functions
    def toggle_series1(self, state):
        self.series1.setVisible(state == 2)

    def toggle_series2(self, state):
        self.series2.setVisible(state == 2)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
