#!/usr/bin/env python3
import argparse
import os
import sys
from datetime import datetime

from remote_ctrl import RemoteTest, RemoteSSH
from tasks_ctrl.task import Task
from utils import logger, YmlManager, OutFile, OutProcess

# ----------------------------------------------------
# CLI Argument Parsing
# ----------------------------------------------------
parser = argparse.ArgumentParser(description="Run Hydraulic Commands Test")
parser.add_argument(
    "-p", "--project", help="Project YAML file", type=str, required=False
)
args = parser.parse_args()
projectFile = args.project

# ----------------------------------------------------
# Initialize YAML Manager
# ----------------------------------------------------
# If project file provided via CLI, use it; else default to 'project.yml'
defaultProjectFile = os.path.join(os.getcwd(), "project.yml")
yamlFileToUse = projectFile if projectFile else defaultProjectFile
myYml = YmlManager(yamlFileToUse)

# Fallback to taskrunner.yml if file not found
if not myYml.CheckIfExists():
    myYml = YmlManager(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), "taskrunner.yml")
    )

if not myYml.CheckIfExists():
    logger.critical(f"{myYml.strFile} file not found. EXITING APPLICATION!!!")
    sys.exit(1)

# ----------------------------------------------------
# Load Project Dictionary
# ----------------------------------------------------
dictProject = myYml.Convert2Dictionary()

# SSH / Remote Settings
strIP = dictProject.get("IPAddress", "")
boolNeedPassword = dictProject.get("PassWordRequired", False)
boolDirectWire = dictProject.get("IsHardWired", False)
StepPause_sec = dictProject.get("StepPause_sec", 1.0)

# Optional new YAML flags
ignorePreviousRuns = dictProject.get("IgnorePreviousRuns", False)
SSHDebug = dictProject.get("SSHDebug", False)
SSHDebugConsole = dictProject.get("SSHDebugConsole", False)
SSHLogDir = dictProject.get("SSHLogDir", "ServoLogs")
SSHRetryFallback = dictProject.get("SSHRetryFallback", True)

# ----------------------------------------------------
# Initialize RemoteSSH
# ----------------------------------------------------
MyRemoteTest = RemoteSSH(
    boolPsswdNeeded=boolNeedPassword,
    strIP=strIP,
    boolDirectWire=boolDirectWire,
    stepPauseSec=StepPause_sec,
)

# Apply optional SSH debug flags
MyRemoteTest.ssh_debug = SSHDebug
MyRemoteTest.ssh_debug_console = SSHDebugConsole
MyRemoteTest.ssh_log_dir = SSHLogDir
MyRemoteTest.ssh_retry_fallback = SSHRetryFallback

# Ensure SSH log directory exists
os.makedirs(SSHLogDir, exist_ok=True)

# ----------------------------------------------------
# Initialize Output Manager
# ----------------------------------------------------
myOut = OutFile(
    os.path.join(os.getcwd(), "out.txt"),
    os.path.join(os.getcwd(), "post_out.txt")
)

logFileLocation = SSHLogDir

# ----------------------------------------------------
# Helper: Get Results
# ----------------------------------------------------
def GetResults():
    if os.path.exists(os.path.join(os.getcwd(), "post_out.txt")):
        myResults = OutProcess("post_out.txt", "results.txt", "results.csv")
    elif os.path.exists(os.path.join(os.getcwd(), "out.txt")):
        myResults = OutProcess("out.txt", "results.txt", "results.csv")

# ----------------------------------------------------
# Task Runner
# ----------------------------------------------------
if "Tasks" not in dictProject:
    logger.critical("Tasks [] not found in task runner file")
    sys.exit(1)

dictTasks = dictProject["Tasks"]

for itask in dictTasks:
    strFileName = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "Tasks", itask["Name"]
    )

    tname = itask["Name"]
    intIterations = itask.get("Repeat", 1)

    # Run initialize or process tasks once
    if "initialize" in tname or "Process" in tname:
        iTask = Task(MyRemoteTest, 1, strFileName, myOut, logFileLocation)
        if "Process" in tname:
            GetResults()
    else:
        # Repeat tasks based on OutFile counts or ignorePreviousRuns flag
        if ignorePreviousRuns:
            for _ in range(intIterations):
                iTask = Task(MyRemoteTest, 1, strFileName, myOut, logFileLocation)
                GetResults()
        else:
            TaskCount = myOut.GetTaskCount(tname)
            limit = intIterations * 2
            while TaskCount < limit:
                TaskCountInit = TaskCount
                iTask = Task(MyRemoteTest, 1, strFileName, myOut, logFileLocation)
                TaskCount = myOut.GetTaskCount(tname)
                GetResults()
                if TaskCountInit == TaskCount:
                    logger.critical(f"TaskCount for {tname} did not increment.")
                    break

logger.info("All tasks completed.")
