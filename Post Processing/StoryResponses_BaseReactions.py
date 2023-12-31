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

    # lengthy function
    @Slot()
    def run(self):

        # enclose your function into a try-except-finally block
        # so that, in case of exceptions, the finished signal
        # will always be emitted.
        try:

            # get document
            doc = App.postDocument()

            # get first database
            if len(doc.databases) == 0:
                raise Exception("You need a database with ID = 1 for this script")
            db = doc.getDatabase(1)

            FileName = "Gorkha Nonlinear"

            DiaphragmNodes = [1,3558,164,165,3556,3557]
            BaseNodes = [154,90,91,161,97,100,108,101,112,104,110,136,137,140,147,148,150,151,152,153,156,157,158,159,160,162,163]

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


                    #Initializing the recorder

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


                    #Record Keeper
                    all_driftsX[node_counter + 1].append(driftx)
                    all_driftsY[node_counter + 1].append(drifty)

                    all_dispX[node_counter].append(i_Ux)
                    all_dispY[node_counter].append(i_Uy)

                    if node_counter == len(Drift_sp_target_i) - 1:
                        all_dispX[node_counter + 1 ].append(j_Ux)
                        all_dispY[node_counter + 1 ].append(j_Uy)



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


                    #Reaction Moment X, Y
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





                #Record Keeper
                BaseReactionX.append(i_Rx)
                BaseReactionY.append(i_Ry)
                BaseMomentX.append(i_Mx)
                BaseMomentY.append(i_My)
                RotationX.append(i_Rox/len(BaseNodes))
                RotationY.append(i_Roy/len(BaseNodes))
                RotationZ.append(i_Roz/len(BaseNodes))

                Uz_Max.append(i_Uz_Max)
                Uz_Max_Node.append(i_Uz_Max_Node)
                Uz_Min.append(i_Uz_Min)
                Uz_Min_Node.append(i_Uz_Min_Node)















            def AbsouluteList(Data):
                value = [abs(ele) for ele in Data]
                return value


            #Data Processing Section
            #Drifts
            DriftX = []
            for key, value in all_driftsX.items():
                DriftX.append(max(AbsouluteList(value)))

            DriftY = []
            for key, value in all_driftsY.items():
                DriftY.append(max(AbsouluteList(value)))


            #Displacements
            DisplacementX = []
            RefDispX = all_dispX[0]
            for key, value in all_dispX.items():
                RelDispX = [a - b for a,b in zip(value, RefDispX)]
                DisplacementX.append(max(AbsouluteList(RelDispX)))

            DisplacementY = []
            RefDispY = all_dispY[0]
            for key, value in all_dispY.items():
                RelDispY = [a - b for a,b in zip(value, RefDispY)]
                DisplacementY.append(max(AbsouluteList(RelDispY)))


            #Uplifts and Settlements
            Max_Uplift = max(Uz_Max)
            Max_Uplift_index = Uz_Max.index(Max_Uplift)
            Max_Uplift_Point = Uz_Max_Node[Max_Uplift_index]

            Max_Settlement = min(Uz_Min)
            Max_Settlement_index = Uz_Min.index(Max_Settlement)
            Max_Settlement_Point = Uz_Min_Node[Max_Settlement_index]





            # Txt Writer
            # open the files for the recorders
            Drift_sp_file = open(f'{FileName}.txt', 'w+')

            Titles = ["Drift X", "Drift Y", "Displacement X", "Displacement Y", "Reaction Force X", "Reaction Force Y",
                      "Reaction Moment X", "Reaction Moment Y", "Rocking Angle X", "Rocking Angle Y", "Rocking Angle Z",
                      "Max Uplift", "Max Uplift Point", "Max Settlement", "Max Settlement Point"
                      ]
            for index, value in enumerate(DriftX):
                Items = [str(DriftX[index]), str(DriftY[index]), str(DisplacementX[index]), str(DisplacementY[index])]

                if index == 0:
                    Drift_sp_file.write('\t'.join(Titles))
                    Drift_sp_file.write('\n')

                    Items.append( str(max(AbsouluteList(BaseReactionX))))
                    Items.append( str(max(AbsouluteList(BaseReactionY)) ))
                    Items.append( str(max(AbsouluteList(BaseMomentX)) ))
                    Items.append( str(max( AbsouluteList(BaseMomentY))))
                    Items.append(str(max(AbsouluteList(RotationX))))
                    Items.append(str(max(AbsouluteList(RotationY))))
                    Items.append(str(max(AbsouluteList(RotationZ))))
                    Items.append(str(Max_Uplift))
                    Items.append(str(Max_Uplift_Point))
                    Items.append(str(Max_Settlement))
                    Items.append(str(Max_Settlement_Point))



                Drift_sp_file.write('\t'.join(Items))
                Drift_sp_file.write('\n')





        except Exception as ex:
            # Store the exception outside in the global variable
            global the_exception
            the_exception = ex
        finally:
            # Done
            self.finished.emit()


# run it
tu.runOnWorkerThread(Worker())

# If we catched an exception in the working
# thread, re-raise it here
if the_exception is not None:
    raise the_exception
