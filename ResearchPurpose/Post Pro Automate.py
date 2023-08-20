import os
import importlib
import utils.ThreadUtils

importlib.reload(utils.ThreadUtils)
import utils.ThreadUtils as tu
from PySide2.QtCore import Qt, QObject, Signal, Slot, QThread, QMutex
from PySide2.QtWidgets import QApplication
from PyMpc import *

# clear terminal
App.clearTerminal()

# Exception
the_exception = None

# Mutex for synchronization
mutex = QMutex()

# Custom signal for worker finished
class WorkerFinishedSignal(QObject):
    finished = Signal()

# my worker class
class Worker(QObject):
    sendPercentage = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker_finished_signal = WorkerFinishedSignal()

    @Slot(str, str)  # Modified the slot to accept an additional argument
    def run(self, CustomArgument):
        try:
            print("I am here")
            print(CustomArgument)  # Use the custom argument here

            # Your lengthy processing code

        except Exception as ex:
            # Store the exception outside in the global variable
            global the_exception
            the_exception = ex
        finally:
            # Done
            self.worker_finished_signal.finished.emit()

# Create the worker thread
class WorkerThread(QThread):
    def __init__(self, worker, custom_argument, parent=None):  # Add custom_argument parameter
        super().__init__(parent)
        self.worker = worker
        self.custom_argument = custom_argument

    def run(self):
        self.worker.run(self.custom_argument)  # Pass both arguments here

#__________________________________________________________________

doc = App.postDocument()

doc.clearPlotGroups()
doc.clearCharts()
doc.clearChartData()
doc.commitChanges()
doc.dirty = True
doc.select(None)

FileName = 'Main_Path.txt'
Drift_sp_file = open(FileName, 'r')

lines = Drift_sp_file.readlines()
print(len(lines))
for index, line in enumerate(lines):
    path = line.strip()
    unicode_path = path.encode('utf-8')
    items = os.listdir(unicode_path)
    from os import *
    for file in items:
        fileExt = file.decode()[-5:]
        if fileExt == '.mpco':
            RecordPath = os.path.join(unicode_path, file)
            App.runCommand("OpenDatabase", RecordPath)
            break

    # Create the worker instance and move it to the worker thread
    custom_argument = [unicode_path, "Hello"]
    worker_instance = Worker()
    thread = WorkerThread(worker_instance, custom_argument)  # Pass the custom argument here
    worker_instance.moveToThread(thread)

    # Connect the custom finished signal to printing message
    worker_instance.worker_finished_signal.finished.connect(lambda: print("Done with the work provided"))

    # Start the thread
    thread.start()
    thread.wait()

    print("Waiting for worker to finish...")
    mutex.lock()
    mutex.unlock()

    break

# If we caught an exception in the working thread, re-raise it here
if the_exception is not None:
    raise the_exception
