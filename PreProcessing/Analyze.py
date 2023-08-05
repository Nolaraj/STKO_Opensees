
'''This code is preferred over the Parametric code as it efficiently captures the cmd responses and prevents for the STKO GUI Freezing type of inconvenience'''

import subprocess
import time
import os
import tkinter as tk
from tkinter import filedialog


status_interval = 5
CompletedFile = "DoneAnalysis.txt"

def open_file_dialog():
    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        title="Select a .txt file containng path of all script folder",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )

    return file_path

def RunCMD(command, interval, index = 1):
    Item = command[0]
    command[0] = f'cd {Item}'
    full_command = ' & '.join(command)

    process = subprocess.Popen(
        ['start', 'cmd', '/c', full_command],
        # Use the 'start' command to open a new command prompt window
        # /c automatically closes the window after task finished. (/k doesnot automatically closes)
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

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


        print("Completed Successfully")
        DoneFile.write(Item)
        DoneFile.write("\n")


    except KeyboardInterrupt:
        # Handle keyboard interrupt (e.g., Ctrl+C)
        print("Monitoring interrupted.")

def PathRefiner(List):
    Paths = []
    for Item in List:
        Item = Item.split("\n")

        path = r""
        for i in Item:
            path = os.path.join(path, i)
        Paths.append(path)
    return Paths




def Analyze():
    # Launcher_File = "LaunchSTKOMonitor.bat"

    Paths_File = open(f'{MainPathFile}', "r")
    Input_Files = Paths_File.readlines()
    Paths = PathRefiner(Input_Files)


    for index, Item in enumerate(Paths):
        if Item not in DonePaths:
            command_to_run = [
                Item ,
                'dir',
                'C:\OpenSees-Solvers\openseesmp.bat .\main.tcl 4'
            ]

            RunCMD(command_to_run, status_interval, index=index + 1)



if __name__ == '__main__':
    MainPathFile = open_file_dialog()

    FolderPath = os.path.dirname(MainPathFile)
    AnalysisDonePath = os.path.join(FolderPath, CompletedFile)
    DonePaths = []
    if os.path.exists(AnalysisDonePath):
        file1 = open(AnalysisDonePath, "r")
        Input_Files = file1.readlines()
        DonePaths = PathRefiner(Input_Files)
        file1.close()

    DoneFile = open(AnalysisDonePath, "a")

    Analyze()
    DoneFile.close()
