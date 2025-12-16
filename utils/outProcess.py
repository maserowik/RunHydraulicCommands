from datetime import date
import time
import datetime
import time
import pandas as pd
import os
import re
import pprint

# from utils.utilLogProcess import *
import numpy as np

# from colorama import Fore, Style
import statistics


def GetVal(strLine, label):
    """Extract values from OUT file.
    label options are: NAME, TASK, COUNT, VAL

    Args:
        strLine (string): line from out.txt file
        label (string): label (NAME, TASK, COUNT, or VAL)

    Returns:
        string: value of label.
    """
    Out = ""

    if label == "NAME":
        x = re.search("^.+NAME:\s*(\w+)]", strLine)
        if x:
            Out = x.group(1)
    elif label == "TASK":
        x = re.search("^.+TASK:\s*(\w+.yml)", strLine)
        if x:
            Out = x.group(1)

    elif label == "COUNT":
        x = re.search("^.+COUNT:\s*(\w+)]", strLine)
        if x:
            Out = x.group(1)
            # breakpoint()
    elif label == "VAL":
        x = re.search("^.+VAL:\s*(.+)]", strLine)
        if x:
            Out = x.group(1)

    # breakpoint()
    return Out


# strline = "[1732202998.675]  [TASK: lowerMotionLift.yml][NAME: GetMaxVelocityLiftLower_SystemTime][COUNT: 1][VAL:varasd]"

# GetVal(strline, "NAME")


def flt2str(val, dec=2):
    if dec == 0:
        return "{:.0f}".format(val)
    elif dec == 1:
        return "{:.1f}".format(val)
    elif dec == 2:
        return "{:.2f}".format(val)
    elif dec == 3:
        return "{:.3f}".format(val)
    elif dec == 4:
        return "{:.4f}".format(val)
    elif dec == 5:
        return "{:.5f}".format(val)
    elif dec == 6:
        return "{:.6f}".format(val)


class OutProcess:
    def __init__(self, strInputFile, strNameResultsFile, strNameResultsFileCSV):
        self.outFile = strInputFile
        self.Data = {}
        self.strResultsPath = os.path.join(os.getcwd(), strNameResultsFile)
        self.strResultsPathCSV = os.path.join(os.getcwd(), strNameResultsFileCSV)
        self.Df = pd.DataFrame(
            {
                "NAME": pd.Series(dtype="float"),
                "MEAN": pd.Series(dtype="float"),
                "MAX": pd.Series(dtype="float"),
                "MIN": pd.Series(dtype="float"),
                "STDV": pd.Series(dtype="float"),
                "VAL": pd.Series(dtype="float"),
            }
        )
        self.PublishResults()

    def PublishResults(self):
        self.ProcessFile()
        # breakpoint()
        self.GetStats()

        self.CreateDF()
        # self.ProcessFile()
        self.Df = self.Df.sort_values("NAME")
        self.PublishFile()

    def ProcessFile(self):
        """loops through out.txt file.
        creates dictionary at self.Data
        self.Data[NAME], where NAME is unique variable name
        self.DATA[NAME][TASK], is task file
        self.DATA[NAME][VAL] = []  (all values appended)
        """

        def StripNumberSuffix(strIn):
            searchObject = re.search("_\d+$", strIn)
            if searchObject:
                start = searchObject.span()[0]
                end = searchObject.span()[1]
                strOutSuffix = strIn[start:end]
                strOut = strIn.replace(strOutSuffix, "")
                return strOut
            else:
                return strIn

        with open(self.outFile, "r") as file:
            # Read each line in the file
            for line in file:
                TASK = GetVal(line, "TASK")
                NAME = StripNumberSuffix(GetVal(line, "NAME"))
                COUNT = GetVal(line, "COUNT")
                VAL = GetVal(line, "VAL")

                try:
                    VAL = float(VAL)
                except:
                    VAL = VAL

                if NAME not in self.Data:

                    self.Data[NAME] = {}
                    self.Data[NAME]["VAL"] = []
                    self.Data[NAME]["TASK"] = TASK

                self.Data[NAME]["VAL"].append(VAL)

    def GetStats(self):

        def GetStatsPerKey(self, strKey):
            """gets statistical parameters per out values"""
            numList = []
            meanOut = "_"
            minOut = "_"
            maxOut = "_"
            stdOut = "_"

            inLst = self.Data[strKey]["VAL"]
            numList = []
            Out = "_"

            for i in inLst:
                if isinstance(i, int) or isinstance(i, float):
                    if i != 0:
                        numList.append(float(i))

            decValues = 2
            if "Tilt" in key and "Time" not in key:
                decValues = 6

            if len(numList) > 0:
                meanOut = flt2str(statistics.mean(numList), decValues)
                minOut = flt2str(min(numList), decValues)
                maxOut = flt2str(max(numList), decValues)
                stdOut = flt2str(statistics.pstdev(numList), decValues)

            self.Data[strKey]["MEAN"] = meanOut
            self.Data[strKey]["MAX"] = maxOut
            self.Data[strKey]["MIN"] = minOut
            self.Data[strKey]["STDV"] = stdOut

        for key in self.Data:
            # print(key)
            GetStatsPerKey(self, key)

    def CreateDF(self):
        Names = ["NAME", "MEAN", "MAX", "MIN", "STDV"]

        i = 0
        for key in self.Data:
            NAME = key
            MEAN = self.Data[key]["MEAN"]
            MAX = self.Data[key]["MAX"]
            MIN = self.Data[key]["MIN"]
            STDV = self.Data[key]["STDV"]
            VAL = self.Data[key]["VAL"]

            new_row = {
                "NAME": NAME,
                "MEAN": MEAN,
                "MAX": MAX,
                "MIN": MIN,
                "STDV": STDV,
                "VAL": VAL,
            }
            self.Df = self.Df._append(new_row, ignore_index=True)

    def PublishFile(self):
        with open(self.strResultsPath, "w") as f:
            df_string = self.Df.to_string()
            f.write(df_string)
        
        self.Df.to_csv(self.strResultsPathCSV)
            

    def GetTaskFilesProcessedFromOutFile(self):
        lstProcessedTaskFiles = []

        if os.path.isfile(self.outFile):
            with open(self.outFile, "r") as file:
                for line in file:
                    TASK = GetVal(line, "TASK")
                    if TASK:
                        lstProcessedTaskFiles.append(TASK)

        lstTasksProcessed = list(set(lstProcessedTaskFiles))
        return lstTasksProcessed

    # breakpoint()


# # OutFile = "/home/raul/gMyProjects/getHyHealth/checkHydHealth/Results_1732202828/out.txt"

# OP1 = OutProcess()
# OP1.outFile = OutFile
# OP1.ProcessFile()
# OP1.GetStats()
# OP1.CreateDF()
# breakpoint()
