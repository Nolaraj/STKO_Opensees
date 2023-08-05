
'''This code is preferred over the Parametric code as it efficiently captures the cmd responses and prevents for the STKO GUI Freezing type of inconvenience'''

import subprocess
import time
import os
import tkinter as tk
from tkinter import filedialog


status_interval = 5


def open_file_dialog():
    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        title="Select a .txt file containng path of all script folder",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )

    return file_path

MainPathFile = open_file_dialog()

def monitor_process(command, interval, index = 1):
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


        print(process.poll(), "Completed Successfully")
        time.sleep(interval)


    except KeyboardInterrupt:
        # Handle keyboard interrupt (e.g., Ctrl+C)
        print("Monitoring interrupted.")

def Analyze():
    # Launcher_File = "LaunchSTKOMonitor.bat"

    Paths_File = open(f'{MainPathFile}', "r")
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
    Analyze()
