
import os
from time import sleep
import importlib
import utils.ThreadUtils

importlib.reload(utils.ThreadUtils)
import utils.ThreadUtils as tu
from PySide2.QtCore import Qt, QObject, Signal, Slot, QThread
from PySide2.QtWidgets import QMessageBox, QApplication
from PyMpc import *
from PyMpc import MpcOdbVirtualResult as vr

# clear terminal
App.clearTerminal()

# Exception
the_exception = None


# my worker class
class Worker(QObject):
    # signals
    sendPercentage = Signal(int)
    finished = Signal()

    print("Inside Worker")

    # lengthy function
    @Slot()
    def run(self):
        print(FileData)

        # enclose your function into a try-except-finally block
        # so that, in case of exceptions, the finished signal
        # will always be emitted.
        try:
            print("I am here")






        except Exception as ex:
            # Store the exception outside in the global variable
            global the_exception
            the_exception = ex
        finally:
            # Done
            self.finished.emit()






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
for line in lines:
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
    		print(RecordPath)
    		

    		
    




    
    tu.runOnWorkerThread(Worker())
    
    print("Done with the work provided")

    break










# If we catched an exception in the working
# thread, re-raise it here
if the_exception is not None:
    raise the_exception
