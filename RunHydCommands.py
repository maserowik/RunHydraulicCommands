#!/usr/bin/env python3
import argparse
import os
import sys

from remote_ctrl import RemoteTest
from tasks_ctrl.task import Task
from utils import logger, YmlManager, OutFile, OutProcess

# -----------------------------
# CLI Arguments
# -----------------------------
parser = argparse.ArgumentParser(description="Run Hydraulic Commands Test")
parser.add_argument("-p", "--project", type=str, required=False)
parser.add_argument("-r", "--results_folder", type=str, required=False)
parser.add_argument("robot")
parser.add_argument("load_type")
args = parser.parse_args()

robot = args.robot
load_type = args.load_type

# -----------------------------
# Load Project YAML
# -----------------------------
defaultProjectFile = os.path.join(os.getcwd(), "project.yml")
yamlFileToUse = args.project if args.project else defaultProjectFile
myYml = YmlManager(yamlFileToUse)

if not myYml.CheckIfExists():
    myYml = YmlManager(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), "taskrunner.yml")
    )

if not myYml.CheckIfExists():
    logger.critical("Task runner YAML not found")
    sys.exit(1)

dictProject = myYml.Convert2Dictionary()

# -----------------------------
# Create RemoteTest (concrete class)
# -----------------------------
MyRemoteTest = RemoteTest(
    boolPsswdNeeded=dictProject.get("PassWordRequired", False),
    strIP=dictProject.get("IPAddress", ""),
    boolDirectWire=dictProject.get("IsHardWired", False),
    stepPauseSec=dictProject.get("StepPause_sec", 1.0),
)

# Apply SSH settings
MyRemoteTest.remote_ssh.ssh_debug = dictProject.get("SSHDebug", False)
MyRemoteTest.remote_ssh.ssh_debug_console = dictProject.get("SSHDebugConsole", False)
MyRemoteTest.remote_ssh.ssh_log_dir = dictProject.get("SSHLogDir", "ServoLogs")
MyRemoteTest.remote_ssh.ssh_retry_fallback = dictProject.get("SSHRetryFallback", True)
os.makedirs(MyRemoteTest.remote_ssh.ssh_log_dir, exist_ok=True)

# -----------------------------
# Get Robot Serial (with fallback)
# -----------------------------
try:
    robot_serial = MyRemoteTest.remote_ssh.GetRobotSerial()
except Exception as e:
    logger.warning(f"Failed to get robot serial via SSH: {e}")
    logger.info(f"Falling back to robot name from CLI: {robot}")
    robot_serial = robot  # fallback

# Clean serial for folder names
robot_serial = robot_serial.replace(" ", "_").replace("/", "_").lower()

# -----------------------------
# Results Folder
# -----------------------------
base_results = args.results_folder if args.results_folder else os.getcwd()
results_folder = os.path.join(
    base_results,
    robot_serial,
    load_type.lower()
)
os.makedirs(results_folder, exist_ok=True)

# -----------------------------
# Output Files
# -----------------------------
out_txt = os.path.join(results_folder, "out.txt")
post_out_txt = os.path.join(results_folder, "post_out.txt")
results_txt = os.path.join(results_folder, "results.txt")
results_csv = os.path.join(results_folder, "results.csv")

myOut = OutFile(out_txt, post_out_txt)

# -----------------------------
# Task Runner
# -----------------------------
dictTasks = dictProject.get("Tasks", [])
if not dictTasks:
    logger.critical("No tasks found in YAML")
    sys.exit(1)

def GetResults():
    if os.path.exists(post_out_txt):
        OutProcess(post_out_txt, results_txt, results_csv)
    elif os.path.exists(out_txt):
        OutProcess(out_txt, results_txt, results_csv)

for itask in dictTasks:
    task_file = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "Tasks",
        itask["Name"]
    )
    iterations = itask.get("Repeat", 1)

    for _ in range(iterations):
        Task(MyRemoteTest, 1, task_file, myOut, results_folder)
        GetResults()

# -----------------------------
# DONE — GUI READS THIS
# -----------------------------
print(f"Serial Number: {robot_serial}")
print(f"Load Type: {load_type}")
print(f"Results Folder: {results_folder}")
logger.info("All tasks completed successfully")

