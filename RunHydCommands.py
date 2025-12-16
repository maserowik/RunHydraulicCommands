#!/usr/bin/env python3
from remote_ctrl import RemoteTest, RemoteSSH
from tasks_ctrl import Task
from utils import logger, YmlManager, OutFile, OutProcess
import os
import sys

# from modules.yml_manager import YmlManager


myYml = YmlManager(os.path.join(os.getcwd(), "project.yml"))
myOut = OutFile(
    os.path.join(os.getcwd(), "out.txt"), os.path.join(os.getcwd(), "post_out.txt")
)
logFileLocation = "ServoLogs"


# checking if local file
if myYml.CheckIfExists() == True:
    logger.info("local task runner file found")
else:
    # using default taskrunner.yml
    myYml = YmlManager(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), "taskrunner.yml")
    )

# Exist if local file not found
if myYml.CheckIfExists() == False:
    logger.critical("{} file not found".format(myYml.strFile))
    logger.critical("EXITING APPLICATION!!!")
    sys.exit(1)


# Get tasks
dictProject = myYml.Convert2Dictionary()

# MyRemoteTest = RemoteTest()

if "IsHardWired" in dictProject:
    boolIsHardWired = dictProject["IsHardWired"]
   
else:
    boolIsHardWired= False


if "StepPause_sec" in dictProject:
    StepPause_sec = dictProject["StepPause_sec"]
   
else:
    boolIsHardWired= 0
MyRemoteTest = RemoteSSH(dictProject["PassWordRequired"], dictProject["IPAddress"], boolIsHardWired, StepPause_sec)


def GetResults():
    if os.path.exists(os.path.join(os.getcwd(), "post_out.txt")):
        myResults = OutProcess("post_out.txt", "results.txt", "results.csv")
    elif os.path.exists(os.path.join(os.getcwd(), "out.txt")):
        myResults = OutProcess("out.txt", "results.txt", "results.csv")


# Check if Tasks [] present
if "Tasks" not in dictProject:
    logger.critical("Tasks [] not found in task runner file")

dictTasks = dictProject["Tasks"]

for itask in dictTasks:
    strFileName = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "Tasks", itask["Name"]
    )

    if "initialize" in itask["Name"]:
        # run initialize once
        iTask = Task(MyRemoteTest, 1, strFileName, myOut, logFileLocation)
    elif "Process" in itask["Name"]:
        # run initialize once
        iTask = Task(MyRemoteTest, 1, strFileName, myOut, logFileLocation)
        GetResults()
    else:
        # Read current Tasks Present in out.file, if < intIterations
        # Need function to read amount of tasks present
        # TaskCount = myOut.GetTaskCount(itask["Name"])
        intIterations = 1 if "Repeat" not in itask else itask["Repeat"]
        TaskCount = myOut.GetTaskCount(itask["Name"])
        while TaskCount < (intIterations * 2):
            TaskCountInit = TaskCount
            # breakpoint()
            iTask = Task(MyRemoteTest, 1, strFileName, myOut, logFileLocation)
            TaskCount = myOut.GetTaskCount(itask["Name"])
            GetResults()
            if TaskCountInit == TaskCount:
                logger.critical(
                    "TaskCount for {} did not increment".format(itask["Name"])
                )

# Create Results file


# if os.path.exists(os.path.join(os.getcwd(), "post_out.txt")):
#     myResults = OutProcess("post_out.txt", "results.txt", "results.csv")
# elif os.path.exists(os.path.join(os.getcwd(), "out.txt")):
#     myResults = OutProcess("out.txt", "results.txt", "results.csv")
logger.info("job completed")
