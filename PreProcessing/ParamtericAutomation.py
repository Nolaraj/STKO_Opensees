from PyMpc import *
from PyMpc.MPC_INTERNALS import run_solver
from opensees.mpc_solver_write_input import write_tcl
import os
import shutil
import subprocess
import time
from pathlib import Path
from subprocess import Popen, PIPE
import signal

App.clearTerminal()
doc = App.caeDocument()

if not App.hasCurrentSolver():
    raise Exception("No solver defined")
solver_command = App.currentSolverCommand()

# Available Names = [S, L1, L2, L3, L4, R]
Building_Name = "R"

Soil_Parameters_Soft = {"Layer1": [1.83, 65352, 196056, 42, 0.35, 0, 100, 0.0] ,
"Layer2" : [1.83, 69883, 209649, 42, 0.35, 0, 100, 0.0],
"Layer3" : [1.83, 133396, 400189, 100, 0.35, 0, 100, 0.0]
}

Soil_Parameters_Medium = {"Layer1": [1.79, 55195, 165586, 38, 0.35, 0, 100, 0.0] ,
"Layer2" : [1.81, 95811, 287435, 38, 0.35, 0, 100, 0.0],
"Layer3" : [1.81, 133396, 400189, 100, 0.35, 0, 100, 0.0]
}

Soil_Parameters_Hard = {"Layer1": [1.69, 78895, 236686, 17, 0.35, 24, 100, 0.0] ,
"Layer2" : [1.97, 152818, 458456, 17, 0.35, 32, 100, 0.0],
"Layer3" : [1.92, 188263, 564790, 100, 0.35, 32, 100, 0.0]}


Soil_Name = ["Soft", "Medium", "Hard"]
Soils = [Soil_Parameters_Soft, Soil_Parameters_Medium, Soil_Parameters_Hard]

Earthquake_Parameters = {"Gorkha": [9, 4000, 20],
                        "Northridge": [7, 1500, 15],
                         "San Fernando" : [8, 4000, 20]
 }




Soil1ID = 2
Soil2ID = 3
SOil3ID = 4
SoilIDs = [Soil1ID, Soil2ID, SOil3ID]
UniformExcID = 10
monitorTopID = 11
monitorBottomID = 12
RecorderID = 2
TrainsientAID = 13

# For Analyze Only the MainPathFile should contains folder containg Main.tcl file and Script had been properly written
WriteScriptQ = True
AnalyzeQ = False
status_interval = 5
MainPathFile = "FilePaths"

# SoilPara = doc.getPhysicalProperty(Soil1ID)
# SoilPara = doc.getPhysicalProperty(Soil2ID)
# SoilPara = doc.getPhysicalProperty(SOil3ID)

UniformEXc = doc.getAnalysisStep(UniformExcID)
monitorTop = doc.getAnalysisStep(monitorTopID)
monitorBottom = doc.getAnalysisStep(monitorBottomID)
Recorder = doc.getAnalysisStep(RecorderID)
TransientAnalysis = doc.getAnalysisStep(TrainsientAID)



def ScriptWriter():
    fileIndex = 1
    Input_Files = []
    for EqName, EqValues in Earthquake_Parameters.items():
        for soilIndex, soil in enumerate(Soils):
            SName = Soil_Name[soilIndex]

            i = 0
            for LName, Svalues in soil.items():
                SoilPara = doc.getPhysicalProperty(SoilIDs[i])

                # SOil Parameters Udpate
                SoilPara.XObject.getAttribute("rho").quantityScalar.value = Svalues[0]
                SoilPara.XObject.getAttribute("refShearModul").quantityScalar.value = Svalues[1]
                SoilPara.XObject.getAttribute("refBulkModul").quantityScalar.value = Svalues[2]
                SoilPara.XObject.getAttribute("cohesi").quantityScalar.value = Svalues[3]
                SoilPara.XObject.getAttribute("peakShearStra").real = Svalues[4]
                SoilPara.XObject.getAttribute("Optional").boolean = True
                SoilPara.XObject.getAttribute("frictionAng").real = Svalues[5]
                SoilPara.XObject.getAttribute("refPress").quantityScalar.value = Svalues[6]
                SoilPara.XObject.getAttribute("pressDependCoe").real = Svalues[7]
                SoilPara.commitXObjectChanges()
                i += 1

            # Earthquake Changes
            UniformEXc.XObject.getAttribute("tsTag").index = EqValues[0]
            UniformEXc.commitXObjectChanges()

            #Transient Analysis Step Changes
            TransientAnalysis.XObject.getAttribute("numIncr").integer = EqValues[1]
            TransientAnalysis.XObject.getAttribute("duration/transient").real = EqValues[2]
            TransientAnalysis.commitXObjectChanges()


            # Monitor Update
            monitorTop.XObject.getAttribute("Use Custom Name").boolean = True
            monitorTop.XObject.getAttribute("Custom Name").string = f"{SName}_{EqName}_Top"
            monitorTop.commitXObjectChanges()

            monitorBottom.XObject.getAttribute("Use Custom Name").boolean = True
            monitorBottom.XObject.getAttribute("Custom Name").string = f"{SName}_{EqName}_Base"
            monitorBottom.commitXObjectChanges()

            # Recorder Update
            Recorder.XObject.getAttribute("name").string = f"{Building_Name}_{SName}_{EqName}"
            Recorder.commitXObjectChanges()

            # Commissioning of Changes
            doc.dirty = True
            doc.commitChanges()
            App.runCommand("Regenerate", "l")
            App.processEvents()

            # Creating Directory
            FolderPath = os.path.join(os.getcwd(), Building_Name, EqName, SName)
            if os.path.exists(FolderPath) is False:
                os.makedirs(FolderPath)

            # Writing the Script to the assigned Directory]
            write_tcl(FolderPath)
            Input_Files.append(FolderPath)

            print(f"File No {fileIndex} has successfully been written")
            fileIndex += 1

    # Writing the text file for future
    txtPath = os.path.join(os.getcwd(), f'{MainPathFile}.txt')
    Paths_File = open(txtPath, 'a')
    for path in Input_Files:
        Paths_File.write(path)
        Paths_File.write('\n')





def monitor_process(command, interval, index = 1):
    full_command = ' & '.join(command)

    process = subprocess.Popen(
        ['start', 'cmd', '/c', full_command],  # Use the 'start' command to open a new command prompt window
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)


    try:
        print(f"Running for {index}. {command[0]}")
        while process.poll() is None:
            # Read and print lines from stdout
            for line in process.stdout:
                print(line.strip())

            # Read and print lines from stderr
            for line in process.stderr:
                print(line.strip())

            # Wait for the specified interval
            time.sleep(interval)


        print(process.poll(), "Completed Successfully")
        time.sleep(interval)


    except KeyboardInterrupt:
        # Handle keyboard interrupt (e.g., Ctrl+C)
        print("Monitoring interrupted.")



def Analyze():
    # Launcher_File = "LaunchSTKOMonitor.bat"

    Paths_File = open(f'{MainPathFile}.txt', "r")
    Input_Files = Paths_File.readlines()

    # Running for the process
    # Input_Files = [Input_Files[0]]
    for index, Item in enumerate(Input_Files):
        # Running for Laucnher
        Item = Item.split("\n")
        print(Item)

        path = r""
        for i in Item:
            path = os.path.join(path, i)
        Item = path

        command_to_run = [
            f'cd {Item}',
            'dir',
            'C:\OpenSees-Solvers\openseesmp.bat .\main.tcl 4'
        ]

        monitor_process(command_to_run, status_interval, index=index + 1)


if __name__ == '__main__':
    if WriteScriptQ:
        ScriptWriter()
    elif AnalyzeQ:
        Analyze()
    else:
        print("Nothing is performed ")

    print("_________________All Code Executed. End of Process !____________________")


