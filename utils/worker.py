# utils/worker.py
# A generic QRunnable worker for executing functions in a separate thread.

from PyQt6.QtCore import QRunnable, pyqtSlot

class Worker(QRunnable):
    """
    Worker thread for running functions without freezing the GUI.
    """
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    @pyqtSlot()
    def run(self):
        """Executes the target function with provided arguments."""
        self.fn(*self.args, **self.kwargs)
