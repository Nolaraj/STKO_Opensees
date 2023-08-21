from PyMpc import *
import numpy as np
from time import sleep
from PySide2.QtCore import Qt, QObject, Signal, Slot, QThread, QEventLoop
from PySide2.QtWidgets import QDialog, QLabel, QProgressBar, QVBoxLayout, QApplication
import os

use_dialog = True  # True = Dialog, False = Event Loop


# App.runCommand("OpenDatabase", "C:/VBShared/di_michele/micro_inplane.mpco")

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


# addPlotGroup = QBlockingSlot(addPlotGroup_function)


def addChartData_function(cdata):
    doc.addChartData(cdata)
    doc.commitChanges()
    doc.dirty = True
    doc.select(cdata)


# addChartData = QBlockingSlot(addChartData_function)


def addChart_function(chart):
    doc.addChart(chart)
    doc.commitChanges()
    doc.dirty = True
    doc.select(chart)


# addChart = QBlockingSlot(addChart_function)


class Worker(QObject):
    sendPercentage = Signal(int)
    finished = Signal()
    executeTask = Signal(list)

    @Slot()
    def run(self, ModelInfo):

        def ModelPara(BuildingName):
            DiaphragmNodes = []
            BaseNodes = []
            if BuildingName == "S":
                DiaphragmNodes = [244, 245, 273, 328, 384, 356]
                BaseNodes = [134, 199, 135, 223, 159, 139, 155, 208, 144, 148, 149, 213, 154, 163, 166, 167, 231, 173, 174,
                             238, 176, 181, 186, 189, 191, 194, 196, 205, 209, 216, 220, 222, 225, 235, 241, 243]

            elif BuildingName == "L1":
                DiaphragmNodes = [226, 227, 255, 310, 366, 338]
                BaseNodes = [110, 206, 142, 113, 116, 196, 132, 123, 136, 128, 133, 197, 144, 208, 146, 210, 199, 203, 204,
                             205, 207, 209, 211, 212, 213, 214, 216, 218, 220, 221, 222, 224, 225]

            elif BuildingName == "L2":
                DiaphragmNodes = [208, 209, 237, 292, 348, 320]
                BaseNodes = [93, 125, 96, 99, 115, 106, 111, 175, 183, 119, 116, 180, 127, 191, 128, 176, 178, 181, 182,
                             184, 185, 186, 187, 188, 195, 198, 199, 205, 206, 207]

            elif BuildingName == "L3":
                DiaphragmNodes = [190, 191, 219, 274, 330, 302]
                BaseNodes = [72, 75, 155, 91, 78, 150, 86, 102, 82, 92, 156, 95, 159, 104, 151, 154, 157, 158, 160, 161,
                             165, 169, 171, 172, 187, 188, 189]

            elif BuildingName == "L4":
                DiaphragmNodes = [172, 173, 201, 256, 312, 284]
                BaseNodes = [161, 97, 129, 100, 132, 101, 103, 104, 131, 107, 171, 134, 135, 136, 139, 141, 154, 156, 157,
                             158, 162, 163, 169, 170]

            elif BuildingName == "R":
                DiaphragmNodes = [117, 118, 127, 191, 163, 219]
                BaseNodes = [66, 69, 93, 101, 73, 95, 96, 99, 100, 107, 108, 109, 110, 111, 112, 113, 115, 116]

            return DiaphragmNodes, BaseNodes


        FolderPath = ModelInfo[1]
        ResultObj = ModelInfo[2]

        DiaphragmNodes, BaseNodes = ModelPara(ModelInfo[0])

        SSI_Analysis = True


        # doc = App.postDocument()
        # doc.clearPlotGroups()
        # doc.clearCharts()
        # doc.clearChartData()
        # doc.commitChanges()
        # doc.dirty = True
        # doc.select(None)

        # Function for Extraction of results, results processing and writing to teh file provided
        def ResultExt_Writer():
            # # get document
            doc = App.postDocument()
            # get first database
            if len(doc.databases) == 0:
                raise Exception("You need a database with ID = 1 for this script")
            db = doc.getDatabase(1)

            Drift_sp_target_i = []
            Drift_sp_target_j = []

            all_driftsX = {}
            all_driftsY = {}
            all_dispX = {}
            all_dispY = {}
            BaseReactionX = []
            BaseReactionY = []
            BaseMomentX = []
            BaseMomentY = []
            RotationX = []
            RotationY = []
            RotationZ = []
            Uz_Max = []
            Uz_Max_Node = []
            Uz_Min = []
            Uz_Min_Node = []

            # get all the results that we need to reproduce the recorders
            # you wrote manually in OpenSees.
            #
            # for displacement we can get the first results that containts the word "Displacement"
            # since there is only one of them
            displacement = db.getNodalResult("Displacement", match=MpcOdb.Contains)
            reactionForce = db.getNodalResult("Reaction Force", match=MpcOdb.Contains)
            reactionMoment = db.getNodalResult("Reaction Moment", match=MpcOdb.Contains)
            rotation = db.getNodalResult("Rotation", match=MpcOdb.Contains)

            # create evaluation options
            # here we want to extract data for all steps of the last stage
            all_stages = db.getStageIDs()  # get all model stages
            last_stage = all_stages[-1]  # get the last stage (pushover)
            all_steps = db.getStepIDs(last_stage)  # get all steps of the last stage
            all_times = db.getStepTimes(last_stage)  # get all step times of the last stage
            # initialize the evaluation options with the last stage
            opt = MpcOdbVirtualResultEvaluationOptions()
            opt.stage = last_stage

            process_counter = 1

            # evaluate all results for each stage
            num_steps = len(all_steps)
            num_steps = 5
            for step_counter in range(num_steps):

                # get step id and time
                step_id = all_steps[step_counter]
                step_time = all_times[step_counter]

                # write something...
                # and process all application events to avoid GUI freezing...
                print('Evaluate results at step {} t = {}'.format(step_id, step_time))
                self.sendPercentage.emit(float(step_counter + 1) / float(num_steps) * 100.0)
                sleep(0.05)

                # put the current step id in the evaluation options
                opt.step = step_id

                # evaluate all the results at the current step
                displacement_field = displacement.evaluate(opt)
                reactionForce_field = reactionForce.evaluate(opt)
                reactionMoment_field = reactionMoment.evaluate(opt)
                rotation_field = rotation.evaluate(opt)

                if process_counter == 1:
                    # Arranging the Diaohragm Nodes
                    nodePositions = []
                    for i in range(len(DiaphragmNodes)):
                        nodePositions.append(displacement_field.mesh.getNode(DiaphragmNodes[i]).position.z)

                    sortedDiaphragm = [x for _, x in sorted(zip(nodePositions, DiaphragmNodes))]
                    print(sortedDiaphragm)

                    # open the files for the recorders

                    for i in range(len(sortedDiaphragm) - 1):
                        Drift_sp_target_i.append(sortedDiaphragm[i])
                        Drift_sp_target_j.append(sortedDiaphragm[i + 1])

                    # get all the results that we need to reproduce the recorders
                    # you wrote manually in OpenSees.

                    # Initializing the recorder

                    for i in range(0, len(Drift_sp_target_i) + 1):
                        all_driftsX[i] = [0]
                        all_driftsY[i] = [0]

                        all_dispX[i] = [0]
                        all_dispY[i] = [0]

                    process_counter += 1

                # This is how you extract data from a nodal result at one or multiple nodes
                # and compute the relative drift accessing the mesh data
                # this is a nodal field. The row is the nodal id

                # Structural Resposes
                for node_counter in range(len(Drift_sp_target_i)):
                    i_node_id = Drift_sp_target_i[node_counter]
                    j_node_id = Drift_sp_target_j[node_counter]
                    i_row = MpcOdbResultField.node(i_node_id)
                    j_row = MpcOdbResultField.node(j_node_id)
                    # this gives the Ux value using both row and column
                    # the column is a 0-based index, so for Ux it is 0 (1 for Uy and 2 for Uz)
                    i_Pz = displacement_field.mesh.getNode(i_node_id).position.z
                    j_Pz = displacement_field.mesh.getNode(j_node_id).position.z
                    dZ = abs(j_Pz - i_Pz)

                    # Displacement X
                    i_Ux = displacement_field[i_row, 0]
                    j_Ux = displacement_field[j_row, 0]

                    # Drift X
                    driftx = (j_Ux - i_Ux) / dZ

                    # Displacement Y
                    i_Uy = displacement_field[i_row, 1]
                    j_Uy = displacement_field[j_row, 1]

                    # Drift Y
                    drifty = (j_Uy - i_Uy) / dZ

                    # Record Keeper
                    all_driftsX[node_counter + 1].append(driftx)
                    all_driftsY[node_counter + 1].append(drifty)

                    all_dispX[node_counter].append(i_Ux)
                    all_dispY[node_counter].append(i_Uy)

                    if node_counter == len(Drift_sp_target_i) - 1:
                        all_dispX[node_counter + 1].append(j_Ux)
                        all_dispY[node_counter + 1].append(j_Uy)

                # Base Reactions and Deformations
                i_Rx = 0
                i_Ry = 0
                i_Mx = 0
                i_My = 0
                i_Rox = 0
                i_Roy = 0
                i_Roz = 0
                i_Uz_Max = 0
                i_Uz_Max_Node = ""
                i_Uz_Min = 0
                i_Uz_Min_Node = ""
                for node_counter in range(len(BaseNodes)):
                    i_node_id = BaseNodes[node_counter]
                    i_row = MpcOdbResultField.node(i_node_id)
                    # this gives the Ux value using both row and column
                    # the column is a 0-based index, so for Ux it is 0 (1 for Uy and 2 for Uz)

                    # Base Reaction Force X, Y
                    i_Rx += reactionForce_field[i_row, 0]
                    i_Ry += reactionForce_field[i_row, 1]

                    # Reaction Moment X, Y
                    i_Mx += reactionMoment_field[i_row, 0]
                    i_My += reactionMoment_field[i_row, 1]

                    # Rotation X, Y, Z
                    i_Rox += rotation_field[i_row, 0]
                    i_Roy += rotation_field[i_row, 1]
                    i_Roz += rotation_field[i_row, 2]

                    # Base Movements

                    if i_Uz_Max < displacement_field[i_row, 2]:
                        i_Uz_Max = displacement_field[i_row, 2]

                        i_Px = displacement_field.mesh.getNode(i_node_id).position.x
                        i_Py = displacement_field.mesh.getNode(i_node_id).position.y
                        i_Pz = displacement_field.mesh.getNode(i_node_id).position.z
                        i_Uz_Max_Node = "X_" + str(i_Px) + " Y_" + str(i_Py) + " Z_" + str(i_Pz)

                    if i_Uz_Min > displacement_field[i_row, 2]:
                        i_Uz_Min = displacement_field[i_row, 2]

                        i_Px = displacement_field.mesh.getNode(i_node_id).position.x
                        i_Py = displacement_field.mesh.getNode(i_node_id).position.y
                        i_Pz = displacement_field.mesh.getNode(i_node_id).position.z
                        i_Uz_Min_Node = "X_" + str(i_Px) + " Y_" + str(i_Py) + " Z_" + str(i_Pz)

                # Record Keeper
                BaseReactionX.append(i_Rx)
                BaseReactionY.append(i_Ry)
                BaseMomentX.append(i_Mx)
                BaseMomentY.append(i_My)
                RotationX.append(i_Rox / len(BaseNodes))
                RotationY.append(i_Roy / len(BaseNodes))
                RotationZ.append(i_Roz / len(BaseNodes))

                Uz_Max.append(i_Uz_Max)
                Uz_Max_Node.append(i_Uz_Max_Node)
                Uz_Min.append(i_Uz_Min)
                Uz_Min_Node.append(i_Uz_Min_Node)

            def AbsouluteList(Data):
                value = [abs(ele) for ele in Data]
                return value

            # Data Processing Section
            # Drifts
            DriftX = []
            for key, value in all_driftsX.items():
                DriftX.append(max(AbsouluteList(value)))

            DriftY = []
            for key, value in all_driftsY.items():
                DriftY.append(max(AbsouluteList(value)))

            # Displacements
            DisplacementX = []
            RefDispX = all_dispX[0]
            for key, value in all_dispX.items():
                RelDispX = value
                if SSI_Analysis:
                    RelDispX = [a - b for a, b in zip(value, RefDispX)]

                DisplacementX.append(max(AbsouluteList(RelDispX)))

            DisplacementY = []
            RefDispY = all_dispY[0]
            for key, value in all_dispY.items():
                RelDispY = value
                if SSI_Analysis:
                    RelDispY = [a - b for a, b in zip(value, RefDispY)]

                DisplacementY.append(max(AbsouluteList(RelDispY)))

            # Uplifts and Settlements
            Max_Uplift = max(Uz_Max)
            Max_Uplift_index = Uz_Max.index(Max_Uplift)
            Max_Uplift_Point = Uz_Max_Node[Max_Uplift_index]

            Max_Settlement = min(Uz_Min)
            Max_Settlement_index = Uz_Min.index(Max_Settlement)
            Max_Settlement_Point = Uz_Min_Node[Max_Settlement_index]
            
            print("Max, Settlement Point", "Max Uplift", Max_Uplift, Max_Settlement)


            # #_________________Writing Starts from here
            Titles = ["Drift X", "Drift Y", "Displacement X", "Displacement Y", "Reaction Force X", "Reaction Force Y",
                      "Reaction Moment X", "Reaction Moment Y", "Rocking Angle X", "Rocking Angle Y", "Rocking Angle Z",
                      "Max Uplift", "Max Uplift Point", "Max Settlement", "Max Settlement Point"
                      ]
            for index, value in enumerate(DriftX):

                Items = [str(DriftX[index]), str(DriftY[index]), str(DisplacementX[index]), str(DisplacementY[index])]

                if index == 0:
                    ResultObj.write('\t'.join(Titles))
                    ResultObj.write('\n')

                    Items.append(str(max(AbsouluteList(BaseReactionX))))
                    Items.append(str(max(AbsouluteList(BaseReactionY))))
                    Items.append(str(max(AbsouluteList(BaseMomentX))))
                    Items.append(str(max(AbsouluteList(BaseMomentY))))
                    Items.append(str(max(AbsouluteList(RotationX))))
                    Items.append(str(max(AbsouluteList(RotationY))))
                    Items.append(str(max(AbsouluteList(RotationZ))))
                    Items.append(str(Max_Uplift))
                    Items.append(str(Max_Uplift_Point))
                    Items.append(str(Max_Settlement))
                    Items.append(str(Max_Settlement_Point))

                ResultObj.write('\t'.join(Items))
                ResultObj.write('\n')
            ResultObj.close()



        ResultExt_Writer()

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

# +++++++++++++++++++++++++++++++++++++++++++++++++++
FileName = 'Main_Path.txt'
Drift_sp_file = open(FileName, 'r')

lines = Drift_sp_file.readlines()
Drift_sp_file.close()

ResultObjects = []
for index, line in enumerate(lines):
    path = line.strip()
    ResultFile = "Result.txt"
    ResultPath = os.path.join(path, ResultFile)
    ResultObj = open(ResultPath, 'w+')
    ResultObjects.append(ResultObj)

for index, line in enumerate(lines):
    path = line.strip()
    BuildingName = path.split("\\")[-3]
    unicode_path = path.encode('utf-8')
    items = os.listdir(unicode_path)

    for file in items:
        fileExt = file.decode()[-5:]
        if fileExt == '.mpco':
            RecordPath = os.path.join(unicode_path, file)
            App.runCommand("OpenDatabase", RecordPath)
            break

    ModelInfo = [BuildingName, unicode_path.decode(), ResultObjects[index]]

    thread = QThread()
    worker = Worker()
    worker.moveToThread(thread)

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

    print("I am here 5")

    print(f"Well Executed for Index No {index}")

# +++++++++++++++++++++++++++++++++++++++++++++++++++
