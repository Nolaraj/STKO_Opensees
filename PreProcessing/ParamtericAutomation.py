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
Building_Nmae = "L3"

Soil_Paramters = {"Soft": [1.61, 37476, 112429, 29.4, 0.1, 6.7, 100, 0.0]}
#    ,
# "Medium" : [7,8,5,5,8,5,5,9],
# "Soft" : [7,2,3,6,9,8,5,7]
# }

Earthquake_Paramters = {"Gorkha": [11],
                        "Northridge": [13]}
#     ,
# "San Fernando" : [7]
# }


Soil1ID = 21
# Soil2ID =
# SOil3ID =
UniformExcID = 27
monitorTopID = 28
monitorBottomID = 29
RecorderID = 2


# For Analyze Only the MainPathFile should contains folder containg Main.tcl file and Script had been properly written
WriteScriptQ = True
status_interval = 5
AnalyzeQ = True
MainPathFile = "Main_Path"

SoilPara = doc.getPhysicalProperty(Soil1ID)
UniformEXc = doc.getAnalysisStep(UniformExcID)
monitorTop = doc.getAnalysisStep(monitorTopID)
monitorBottom = doc.getAnalysisStep(monitorBottomID)
Recorder = doc.getAnalysisStep(RecorderID)


def ScriptWriter():
    Input_Files = []
    for SName, Svalues in Soil_Paramters.items():
        for EqName, EqValues in Earthquake_Paramters.items():

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

            # Earthquake Changes
            UniformEXc.XObject.getAttribute("tsTag").index = EqValues[0]
            UniformEXc.commitXObjectChanges()

            # Monitor Update
            monitorTop.XObject.getAttribute("Use Custom Name").boolean = True
            monitorTop.XObject.getAttribute("Custom Name").string = f"{SName}_{EqName}_Top"
            monitorTop.commitXObjectChanges()

            monitorBottom.XObject.getAttribute("Use Custom Name").boolean = True
            monitorBottom.XObject.getAttribute("Custom Name").string = f"{SName}_{EqName}_Base"
            monitorBottom.commitXObjectChanges()

            # Recorder Update
            Recorder.XObject.getAttribute("name").string = f"{Building_Nmae}_{SName}_{EqName}"
            Recorder.commitXObjectChanges()

            # Commissioning of Changes
            doc.dirty = True
            doc.commitChanges()
            App.runCommand("Regenerate", "l")
            App.processEvents()

            # Creating Directory
            FolderPath = os.path.join(os.getcwd(), Building_Nmae, SName, EqName)
            if os.path.exists(FolderPath) is False:
                os.makedirs(FolderPath)

            # Writing the Script to the assigned Directory]
            write_tcl(FolderPath)
            Input_Files.append(FolderPath)

    # Writing the text file for future
    Paths_File = open(f'{MainPathFile}.txt', 'w+')
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
