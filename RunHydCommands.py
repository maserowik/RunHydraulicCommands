#!/usr/bin/env python3
import argparse
import os
import sys
from datetime import datetime

from remote_ctrl import RemoteTest, RemoteSSH
from tasks_ctrl.task import Task
from utils import logger, YmlManager, OutFile, OutProcess

# -----------------------------
# CLI Arguments
# -----------------------------
parser = argparse.ArgumentParser(description="Run Hydraulic Commands Test")
parser.add_argument("-p", "--project", help="Project YAML file", type=str, required=False)
parser.add_argument("-r", "--results_folder", help="Results folder path", type=str, required=False)
parser.add_argument("robot", help="Robot name: RS1 or CR1")
parser.add_argument("load_type", help="Loaded or Unloaded")
args = parser.parse_args()

projectFile = args.project
results_folder = args.results_folder if args.results_folder else os.getcwd()
robot = args.robot
load_type = args.load_type

# Ensure results folder exists
os.makedirs(results_folder, exist_ok=True)

# -----------------------------
# Initialize YAML Manager
# -----------------------------
defaultProjectFile = os.path.join(os.getcwd(), "project.yml")
yamlFileToUse = projectFile if projectFile else defaultProjectFile
myYml = YmlManager(yamlFileToUse)

if not myYml.CheckIfExists():
    myYml = YmlManager(os.path.join(os.path.dirname(os.path.realpath(__file__)), "taskrunner.yml"))

if not myYml.CheckIfExists():
    logger.critical(f"{myYml.strFile} file not found. EXITING APPLICATION!!!")
    sys.exit(1)

dictProject = myYml.Convert2Dictionary()

# -----------------------------
# SSH / Remote Settings
# -----------------------------
strIP = dictProject.get("IPAddress", "")
boolNeedPassword = dictProject.get("PassWordRequired", False)
boolDirectWire = dictProject.get("IsHardWired", False)
StepPause_sec = dictProject.get("StepPause_sec", 1.0)

ignorePreviousRuns = dictProject.get("IgnorePreviousRuns", False)
SSHDebug = dictProject.get("SSHDebug", False)
SSHDebugConsole = dictProject.get("SSHDebugConsole", False)
SSHLogDir = dictProject.get("SSHLogDir", "ServoLogs")
SSHRetryFallback = dictProject.get("SSHRetryFallback", True)

# -----------------------------
# Initialize RemoteSSH
# -----------------------------
MyRemoteTest = RemoteSSH(
    boolPsswdNeeded=boolNeedPassword,
    strIP=strIP,
    boolDirectWire=boolDirectWire,
    stepPauseSec=StepPause_sec,
)
MyRemoteTest.ssh_debug = SSHDebug
MyRemoteTest.ssh_debug_console = SSHDebugConsole
MyRemoteTest.ssh_log_dir = SSHLogDir
MyRemoteTest.ssh_retry_fallback = SSHRetryFallback
os.makedirs(SSHLogDir, exist_ok=True)

# -----------------------------
# Initialize Output Manager
# -----------------------------
out_txt = os.path.join(results_folder, "out.txt")
post_out_txt = os.path.join(results_folder, "post_out.txt")
results_txt = os.path.join(results_folder, "results.txt")
results_csv = os.path.join(results_folder, "results.csv")

myOut = OutFile(out_txt, post_out_txt)

# -----------------------------
# Task Runner
# -----------------------------
if "Tasks" not in dictProject:
    logger.critical("Tasks [] not found in task runner file")
    sys.exit(1)

dictTasks = dictProject["Tasks"]

def GetResults():
    if os.path.exists(post_out_txt):
        OutProcess(post_out_txt, results_txt, results_csv)
    elif os.path.exists(out_txt):
        OutProcess(out_txt, results_txt, results_csv)

for itask in dictTasks:
    task_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Tasks", itask["Name"])
    tname = itask["Name"]
    intIterations = itask.get("Repeat", 1)

    if "initialize" in tname or "Process" in tname:
        iTask = Task(MyRemoteTest, 1, task_file, myOut, results_folder)
        if "Process" in tname:
            GetResults()
    else:
        if ignorePreviousRuns:
            for _ in range(intIterations):
                iTask = Task(MyRemoteTest, 1, task_file, myOut, results_folder)
                GetResults()
        else:
            TaskCount = myOut.GetTaskCount(tname)
            limit = intIterations * 2
            while TaskCount < limit:
                TaskCountInit = TaskCount
                iTask = Task(MyRemoteTest, 1, task_file, myOut, results_folder)
                TaskCount = myOut.GetTaskCount(tname)
                GetResults()
                if TaskCountInit == TaskCount:
                    logger.critical(f"TaskCount for {tname} did not increment.")
                    break

# -----------------------------
# Done
# -----------------------------
logger.info(f"All tasks completed for {robot} {load_type}")
print(f"Serial Number: {robot}_{load_type}")  # GUI can read this
print(f"Results saved in: {results_folder}")
