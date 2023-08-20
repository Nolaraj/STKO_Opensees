from PyMpc import *
import numpy as np
from time import sleep
from PySide2.QtCore import Qt, QObject, Signal, Slot, QThread, QEventLoop
from PySide2.QtWidgets import QDialog, QLabel, QProgressBar, QVBoxLayout, QApplication
import os
use_dialog = False  # True = Dialog, False = Event Loop


#App.runCommand("OpenDatabase", "C:/VBShared/di_michele/micro_inplane.mpco")

class QBlockingSlot(QObject):
    requestCall = Signal(tuple)
    done = Signal()

    def __init__(self, function, parent=None):
        super(QBlockingSlot, self).__init__(parent)
        self.requestCall.connect(self.run)
        self.function = function

    def run(self, data):
        self.function(data)
        self.done.emit()

    def call(self, data):
        loop = QEventLoop()
        self.done.connect(loop.quit)
        self.requestCall.emit(data)
        loop.exec_()


def addPlotGroup_function(pgroup):
    doc.addPlotGroup(pgroup)
    doc.commitChanges()
    doc.dirty = True
    doc.select(pgroup)
    doc.setActivePlotGroup(pgroup)
    info = MpcOdpRegeneratorUpdateInfo()
    info.onlyTexture = True
    pgroup.update(info)


#addPlotGroup = QBlockingSlot(addPlotGroup_function)


def addChartData_function(cdata):
    doc.addChartData(cdata)
    doc.commitChanges()
    doc.dirty = True
    doc.select(cdata)


#addChartData = QBlockingSlot(addChartData_function)


def addChart_function(chart):
    doc.addChart(chart)
    doc.commitChanges()
    doc.dirty = True
    doc.select(chart)


#addChart = QBlockingSlot(addChart_function)





class Worker(QObject):
    sendPercentage = Signal(int)
    finished = Signal()
    executeTask = Signal(list)

    @Slot()
    def run(self, model_info):
        print(model_info)
        
        
        ##Place your working code here


        self.finished.emit()



if use_dialog:
    dialog = QDialog()
    dialog.setLayout(QVBoxLayout())
    dialog.layout().addWidget(QLabel("Work in progres. Please wait"))
    pbar = QProgressBar()
    pbar.setRange(1, 100)
    pbar.setTextVisible(True)
    dialog.layout().addWidget(pbar)
else:
    loop = QEventLoop()


#+++++++++++++++++++++++++++++++++++++++++++++++++++
FileName = 'Main_Path.txt'
Drift_sp_file = open(FileName, 'r')
lines = Drift_sp_file.readlines()
print(len(lines))
for index, line in enumerate(lines):
    doc = App.postDocument()
    doc.clearPlotGroups()
    doc.clearCharts()
    doc.clearChartData()
    doc.commitChanges()
    doc.dirty = True
    doc.select(None)

    thread = QThread()
    worker = Worker()
    worker.moveToThread(thread)

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
            
    ModelInfo = ["S", "R"]
    
    worker.finished.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.started.connect(worker.run)
    thread.finished.connect(thread.deleteLater)

    # Connect the executeTask signal to the run slot
    worker.executeTask.connect(worker.run)

    # Start the thread and run dialog or event loop
    thread.start()

    if use_dialog:
        worker.sendPercentage.connect(pbar.setValue)
        thread.finished.connect(dialog.accept)
    else:
        thread.finished.connect(loop.quit)

    # Emit the executeTask signal with the ModelInfo argument
    worker.executeTask.emit(ModelInfo)  # Pass the ModelInfo list as an argument


    if use_dialog:
        dialog.exec_()
    else:
        loop.exec_()
        
    print(f"Well Executed for Index No {index}")




