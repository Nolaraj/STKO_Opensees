import subprocess
import time
import os

MainPathFile = "Main_Path"
status_interval = 5


def monitor_process(command, interval, index = 1):
    full_command = ' & '.join(command)

    process = subprocess.Popen(
        ['start', 'cmd', '/c', full_command],  # Use the 'start' command to open a new command prompt window
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


Analyze()
