from PyMpc import *
import numpy as np
from time import sleep
from PySide2.QtCore import Qt, QObject, Signal, Slot, QThread, QEventLoop
from PySide2.QtWidgets import QDialog, QLabel, QProgressBar, QVBoxLayout, QApplication
import os
import math

use_dialog = True  # True = Dialog, False = Event Loop



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

        def ModelPara():
            if BaseCondition == "Fixed":
                return  False

            else:
                return  True

        BuildingName = ModelInfo[0]
        FolderPath = ModelInfo[1]
        ResultObj = ModelInfo[2]
        Index = ModelInfo[3]
        BaseCondition = ModelInfo[4]

        SSI_Analysis = ModelPara()


        # Function for Extraction of results, results processing and writing to teh file provided
        def ResultExt_Writer():

            all_times = []
            Drift_sp_target_i = []
            Drift_sp_target_j = []

            all_driftsX = {}
            all_driftsY = {}
            all_dispX = {}
            all_dispY = {}
            all_RotZ = {}
            BaseReactionX = []
            BaseReactionY = []
            BaseMomentX = []
            BaseMomentY = []
            Rotation_X = []
            Rotation_Y = []
            Rotation_Z = []
            Uz_Max = []
            Uz_Max_Node = []
            Uz_Min = []
            Uz_Min_Node = []

            def Extractor():
                # # get document
                doc = App.postDocument()
                # get first database
                if len(doc.databases) == 0:
                    raise Exception("You need a database with ID = 1 for this script")
                db = doc.getDatabase(Index + 1)

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
                for value in db.getStepTimes(last_stage):
                    all_times.append(value)
                # initialize the evaluation options with the last stage
                opt = MpcOdbVirtualResultEvaluationOptions()
                opt.stage = last_stage


                # evaluate all results for each stage
                num_steps = len(all_steps)
                if num_steps == 0:
                    raise Exception("No steps in this stage")


                def IDs_Finder(mesh):
                    tolerance = 1.0e-8

                    All_Nodes_Super = []
                    Element_Nodes_Super = []
                    Element_Nodes_All = {}
                    FloorNodes = {}

                    #Diaphragm Nodes
                    def Node_Z_GT_0(node, node_id, Operation="Plus"):
                        if Operation == "Plus":
                            if node.position.z >= 0 + tolerance:
                                return node_id

                        else:
                            if node.position.z >= 0 - tolerance:
                                return node_id
                    def CheckTolerance(Ref, Tolerance, CheckValue):
                        Ref1 = Ref + Tolerance
                        Ref2 = Ref - Tolerance

                        if ((CheckValue >= Ref1 and CheckValue <= Ref2) or (CheckValue >= Ref2 and CheckValue <= Ref1)):
                            return True
                        else:
                            return False
                    def RemoveListDuplicates(List):
                        Set = set(List)
                        return [x for x in Set]
                    def DataSort(MainData, SortingDataset):
                        SortedData = [x for _, x in sorted(zip(SortingDataset, MainData))]
                        return SortedData
                    def ListUnion(List1, List2):
                        union_list = list(set(List1) | set(List2))
                        return union_list

                    #All Element Nodes
                    ElementNodesNo = [2, 8]
                    for eleNodes in ElementNodesNo:
                        Element_Nodes_All[eleNodes] = []

                    for ele_id, ele in mesh.elements.items():
                        for eleNodes in ElementNodesNo:
                            if len(ele.nodes) == eleNodes:
                                for i in range(eleNodes):
                                    Element_Nodes_All[eleNodes].append(ele.nodes[i].id)

                    for key, value in Element_Nodes_All.items():
                        Value = RemoveListDuplicates(value)
                        Element_Nodes_All[key] = Value

                    # Adding for all the nodes (including free nodes) with z coordinates greater than (0 + tolerance)
                    for node_id, node in mesh.nodes.items():
                        Value = Node_Z_GT_0(node, node_id)
                        if Value != None:
                            All_Nodes_Super.append(Value)

                    #Adding for all the element nodes with z coordineates greater than (0+ tolerance)
                    for ele_id, ele in mesh.elements.items():
                        ElementNodesNo = [2, 8]
                        for eleNodes in ElementNodesNo:
                            if len(ele.nodes) == eleNodes:
                                for i in range(eleNodes):
                                    Value = Node_Z_GT_0(ele.nodes[i], ele.nodes[i].id)
                                    if Value != None:
                                        Element_Nodes_Super.append(Value)


                    def DiaphragmNodesExt():
                        #Freenodes also referred to as Diaphragm nodes (Doesnot include the diaphragm nodes at the base)
                        FreeNodes = [x for x in All_Nodes_Super if x not in Element_Nodes_Super]


                        #Checking for coOrdinates consistency of the Diaphragm nodes (exluding the base diaphragm node) for X and Y value
                        DiaX, DiaY = 0.00, 0.00
                        for index,  node in enumerate(FreeNodes):
                            CoOrdinates = mesh.getNode(node).position
                            x= CoOrdinates[0]
                            y = CoOrdinates[1]
                            if index == 0:
                                DiaX, DiaY = x, y
                            else:
                                if CheckTolerance(DiaX, tolerance, x) is False:
                                    print(f"Diaphragm Tolerance not meet along X for node index {node}")
                                if CheckTolerance(DiaY, tolerance, y) is False:
                                    print(f"Diaphragm Tolerance not meet along Y for node index {node}")


                        #Using the above extracted diaphragm nodes after checking for consistency, extracting the base diaphragm node
                        # from all nodes with Z coordinates greater than (0 - tolerance) and with plan Coordinates exact with teh
                        # previously extracted DiaX and DiaY value.
                        for node_id, node in mesh.nodes.items():
                            x = node.position.x
                            y = node.position.y

                            if CheckTolerance(DiaX, tolerance, x) and CheckTolerance(DiaY, tolerance, y):
                                if Node_Z_GT_0(node, node_id, Operation="Subtract"):
                                    Identifier = True
                                    for key, value in Element_Nodes_All.items():
                                        if node_id in value:
                                            Identifier = False

                                    if Identifier:
                                        FreeNodes.append(node_id)


                        # Arranging the Diaohragm Nodes
                        DiaphragmNodes = RemoveListDuplicates(FreeNodes)

                        nodePositions = []
                        for i in range(len(DiaphragmNodes)):
                            nodePositions.append(displacement_field.mesh.getNode(DiaphragmNodes[i]).position.z)
                        sortedDiaphragm = DataSort(DiaphragmNodes, nodePositions)
                        return sortedDiaphragm

                    def FloorNodesExt(FloorHeights):
                        #Initializing the bucket for storing the story nodes
                        for height in FloorHeights:
                            FloorNodes[height] = []


                        #Element Nodes = 2 for line element
                        ElementNode = 2
                        NodeId = Element_Nodes_All[ElementNode]

                        #Writing for the nodes
                        for node in NodeId:
                            Value = Node_Z_GT_0(mesh.getNode(node), mesh.getNode(node).id, Operation="Subtract")
                            if Value != None:
                                nodeheight = mesh.getNode(node).position.z

                                if nodeheight in FloorHeights:
                                    FloorNodes[nodeheight].append(Value)

                        #Cleaning the floor lists and writing to global list of nodes
                        for key, value in FloorNodes.items():
                            Value = RemoveListDuplicates(value)
                            FloorNodes[key] = Value




                    DiaphragmNodes = DiaphragmNodesExt()

                    FloorHeights = [0, 4,7,10,13,16]
                    FloorNodesExt(FloorHeights)

                    print("I am here")

                    #Adding and cleaning to get the all super nodes
                    for value in DiaphragmNodes:
                        All_Nodes_Super.append(value)

                    Values = []
                    for key, value in FloorNodes.items():
                        for val in value:
                            Values.append(val)
                    for val in Values:
                        All_Nodes_Super.append(val)

                    All_Nodes_Super = RemoveListDuplicates(All_Nodes_Super)
                    print(len(All_Nodes_Super))




                    return DiaphragmNodes, FloorNodes


                process_counter = 1

                # evaluate all results for each stage
                num_steps = len(all_steps)
                num_steps = 20
                for index, step_counter in enumerate(range(num_steps)):

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



                    if index == 0:
                        mesh = displacement_field.mesh
                        sortedDiaphragm, FloorNodes = IDs_Finder(mesh)
                        BaseNodes = FloorNodes[0]


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

                            all_RotZ[i] = [0]

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

                        # Rotation Z
                        i_Rx = rotation_field[i_row, 2]
                        j_Rx = rotation_field[j_row, 2]

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

                        all_RotZ[node_counter].append(i_Rx)

                        if node_counter == len(Drift_sp_target_i) - 1:
                            all_dispX[node_counter + 1].append(j_Ux)
                            all_dispY[node_counter + 1].append(j_Uy)

                            all_RotZ[node_counter + 1].append(j_Rx)

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
                    Rotation_X.append(i_Rox / len(BaseNodes))
                    Rotation_Y.append(i_Roy / len(BaseNodes))
                    Rotation_Z.append(i_Roz / len(BaseNodes))

                    Uz_Max.append(i_Uz_Max)
                    Uz_Max_Node.append(i_Uz_Max_Node)
                    Uz_Min.append(i_Uz_Min)
                    Uz_Min_Node.append(i_Uz_Min_Node)


            Extractor()

            def AbsouluteList(Data):
                value = [abs(ele) for ele in Data]
                return value

            # Data Processing Section
            # Removing the extra residue created during initializing the recorders
            for i in range(0, len(Drift_sp_target_i) + 1):
                def FirstPopper(List):
                    if len(List[i]) != 1:
                        List[i].pop(0)

                FirstPopper(all_driftsX)
                FirstPopper(all_driftsY)
                FirstPopper(all_dispX)
                FirstPopper(all_dispY)
                FirstPopper(all_RotZ)

            # Maximum of the all time steps for each key, Provide set with key as diaphragm node and Value as list of TS value
            def MaxTimeStep(DefinedSet, Displacement = False):

                MaxValue = []
                if Displacement == False:
                    for key, value in DefinedSet.items():
                        MaxValue.append(max(AbsouluteList(value)))
                    return MaxValue

                if Displacement == True:
                    RefDispX = DefinedSet[0]
                    for key, value in DefinedSet.items():
                        RelDispX = value
                        if SSI_Analysis:
                            RelDispX = [a - b for a, b in zip(value, RefDispX)]

                        MaxValue.append(max(AbsouluteList(RelDispX)))
                    return MaxValue

            # Drifts
            DriftX =  MaxTimeStep(all_driftsX)
            DriftY = MaxTimeStep(all_driftsY)
            DisplacementX = MaxTimeStep(all_dispX, Displacement = True)
            DisplacementY = MaxTimeStep(all_dispY, Displacement = True)
            RotationZ = MaxTimeStep(all_RotZ)



            # DriftX = []
            # for key, value in all_driftsX.items():
            #     DriftX.append(max(AbsouluteList(value)))
            #
            # DriftY = []
            # for key, value in all_driftsY.items():
            #     DriftY.append(max(AbsouluteList(value)))
            #
            # # Displacements
            # DisplacementX = []
            # RefDispX = all_dispX[0]
            # for key, value in all_dispX.items():
            #     RelDispX = value
            #     if SSI_Analysis:
            #         RelDispX = [a - b for a, b in zip(value, RefDispX)]
            #
            #     DisplacementX.append(max(AbsouluteList(RelDispX)))
            #
            # DisplacementY = []
            # RefDispY = all_dispY[0]
            # for key, value in all_dispY.items():
            #     RelDispY = value
            #     if SSI_Analysis:
            #         RelDispY = [a - b for a, b in zip(value, RefDispY)]
            #
            #     DisplacementY.append(max(AbsouluteList(RelDispY)))

            # Uplifts and Settlements
            Max_Uplift = max(Uz_Max)
            Max_Uplift_index = Uz_Max.index(Max_Uplift)
            Max_Uplift_Point = Uz_Max_Node[Max_Uplift_index]


            Max_Settlement = min(Uz_Min)
            Max_Settlement_index = Uz_Min.index(Max_Settlement)
            Max_Settlement_Point = Uz_Min_Node[Max_Settlement_index]

            # Base Shear and Its Pseudo time
            try:
                index = BaseReactionX.index(max(AbsouluteList(BaseReactionX)))
            except:
                index = BaseReactionX.index(-max(AbsouluteList(BaseReactionX)))
            print("Hello Here")


            MaxBS_PseudoTime = all_times[index]

            print("Max, Settlement Point", "Max Uplift", Max_Uplift, Max_Settlement)


            #Writing starts from here
            def Writer():
                # def AvgValue(MovList, RefValue, DataList):
                #     RefValue = abs(RefValue)
                #     def AbsListVal(List, FloatIndex):
                #         Deci_Int = math.modf(FloatIndex)
                #         a = int(Deci_Int[1])
                #         b = a + 1
                #         ReqValue = List[a] + Deci_Int[0] * (List[b] - List[a])
                #
                #         return abs(ReqValue)
                #
                #     def Indexed(RefList, RefValue):
                #         Indexes = []
                #         Lenlist = len(RefList)
                #         for index, value in enumerate(RefList):
                #             if index == (Lenlist - 1):
                #                 break
                #             val1 = abs(RefList[index])
                #             val2 = abs(RefList[index + 1])
                #             if val1 <= RefValue:
                #                 if val2 >= RefValue:
                #                     ReqIndex = index + ((abs(RefValue) - abs(val1)) / (abs(val2) - abs(val1)))
                #                     Indexes.append(ReqIndex)
                #
                #
                #             #if ((val1 <= RefValue) and (val2 >= RefValue)):
                #              #   ReqIndex = index + ((abs(RefValue) - abs(val1)) / (abs(val2) - abs(val1)))
                #               #  Indexes.append(ReqIndex)
                #         return Indexes
                #
                #     def ValueExt(DataList, Indexex):
                #         Values = []
                #         for index in Indexex:
                #             value = AbsListVal(DataList, index)
                #             Values.append(value)
                #
                #         Avg = np.average(Values)
                #         return Avg
                #     Indexes = Indexed(MovList, RefValue)
                #     Average = ValueExt(DataList, Indexes)
                #     return Average

                Titles = ["Drift X", "Drift Y", "Displacement X", "Displacement Y","Rotation Z", "Reaction Force X", "Reaction Force Y",
                          "Reaction Moment X", "Reaction Moment Y", "Rocking Angle X", "Rocking Angle Y", "Rocking Angle Z",
                          "Max Uplift", "Max Uplift Point", "Max Settlement", "Max Settlement Point"
                          ]
                for index, value in enumerate(DriftX):
                    print(DriftX)
                    print(DriftY)
                    print(DisplacementX)
                    print(DisplacementY)




                    print(RotationZ)
                    print(BaseReactionX)
                    print(Rotation_X)
                    print(Rotation_Y)
                    print(Rotation_Z)
                    print(MaxBS_PseudoTime)
                    print(ResultObj)


                    Items = [str(DriftX[index]), str(DriftY[index]), str(DisplacementX[index]), str(DisplacementY[index]), str(RotationZ[index])]

                    if index == 0:
                        ResultObj.write('\t'.join(Titles))
                        ResultObj.write('\n')

                        # Items.append(str(AvgValue(all_dispXTOP, float(Displacement), BaseReactionX)))
                        Items.append(str(max(AbsouluteList(BaseReactionX))))
                        Items.append(str(max(AbsouluteList(BaseReactionY))))
                        Items.append(str(max(AbsouluteList(BaseMomentX))))
                        Items.append(str(max(AbsouluteList(BaseMomentY))))
                        Items.append(str(max(AbsouluteList(Rotation_X))))
                        Items.append(str(max(AbsouluteList(Rotation_Y))))
                        Items.append(str(max(AbsouluteList(Rotation_Z))))
                        Items.append(str(Max_Uplift))
                        Items.append(str(Max_Uplift_Point))
                        Items.append(str(Max_Settlement))
                        Items.append(str(Max_Settlement_Point))

                    if index == 1:
                        Items.append(str(MaxBS_PseudoTime))
                    print("All items cretaeed")

                    ResultObj.write('\t'.join(Items))
                    ResultObj.write('\n')
                ResultObj.close()

            Writer()

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
writerBiasedFor = "Fixed"
Drift_sp_file = open(FileName, 'r')

lines = Drift_sp_file.readlines()
Drift_sp_file.close()

ResultObjects = []
Paths = []
for index, line in enumerate(lines):
    path = line.strip()
    ResultFile = "Result.txt"
    ResultPath = os.path.join(path, ResultFile)
    ResultObj = open(ResultPath, 'w+')

    path = line.strip()
    BaseCondition = path.split("\\")[-1]
    print(BaseCondition)
    if BaseCondition == writerBiasedFor:
        Paths.append(path)
        ResultObjects.append(ResultObj)


for index, line in enumerate(Paths):
    path = line.strip()
    BuildingName = path.split("\\")[-3]
    BaseCondition = path.split("\\")[-1]
    unicode_path = path.encode('utf-8')
    items = os.listdir(unicode_path)


    for file in items:
        fileExt = file.decode()[-5:]
        if fileExt == '.mpco':
            RecordPath = os.path.join(unicode_path, file)
            App.runCommand("OpenDatabase", RecordPath)
            break

    ModelInfo = [BuildingName, unicode_path.decode(), ResultObjects[index], index, BaseCondition]

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


    print(f"Well Executed for Index No {index}")
    break

# +++++++++++++++++++++++++++++++++++++++++++++++++++
