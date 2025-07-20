# utils/pandas_model.py
# A QStandardItemModel subclass for displaying pandas DataFrames in a QTableView.

from PyQt6.QtGui import QStandardItemModel, QStandardItem

class PandasModel(QStandardItemModel):
    """A model to interface a Qt view with a pandas DataFrame."""
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self._data = data
        self.setColumnCount(len(data.columns))
        self.setRowCount(len(data))
        self.setHorizontalHeaderLabels(data.columns)

        for i, row in enumerate(data.itertuples(index=False)):
            for j, val in enumerate(row):
                self.setItem(i, j, QStandardItem(str(val)))
