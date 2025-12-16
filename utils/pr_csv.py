import pandas as pd
import os
import pprint
import numpy as np

# from utils.utilities import *


class PrCSV:
    """Helper class to process csv/dataframe objects"""

    def __init__(self, strCSVFile: str):
        self.strCSVFile = strCSVFile
        self.ColumnNames = [
            "SystemTime",
            "Command",
            "LastPosition",
            "InterpolatedPosition",
            "FiltVel",
            "TargetPosition",
            "TargetVelocity",
            "ErrPos",
            "ErrVel",
            "Mode",
            "None",
        ]


        self.Df = pd.read_csv(
            os.path.join(self.strCSVFile),
            header=0,
            engine="python",
            sep=",|]",
            names=self.ColumnNames,
        )
        self.iterator = 0
        
        self.Df["Time"] = self.Df["SystemTime"] - self.Df.at[0, "SystemTime"]
        self.length = len(self.Df)
     

    def SetIter(self, intVal):
        self.iterator = intVal

    def GetVal(self, strColName, i):
        return self.Df[strColName].iat[i].item()

    def GetRows(self):
        return self.Df.shape[0]

    def GetIndexAtTime(self, TimeTarget, guessIndex=0):
        """Gets the index for the given time value.
        Uses the lowest nearest index

        Args:
            TimeTarget (float):
            guessIndex (int, optional): guess

        Returns:
            _int_: returns int
        """
        Found = False
        index = min(guessIndex, self.length - 2)

        if TimeTarget < 0:
            return 0

        if TimeTarget >= self.GetVal("Time", self.length - 1):
            return self.length - 1

        ProtectLoop = 0
        while Found == False:
            N0 = index
            N1 = N0 + 1
            T0 = self.GetVal("Time", N0)
            T1 = self.GetVal("Time", N1)

            if TimeTarget >= T0 and TimeTarget < T1:
                return N0
            elif TimeTarget < T0 and TimeTarget < T1:
                index -= 1
            elif TimeTarget > T0 and TimeTarget > T1:
                index += 1
            ProtectLoop += 1
            if ProtectLoop >= self.length:
                # log("Failed finding index", type="error")
                break

    def GetValAtTime(self, strColName, TargetTime):
        for i in range(self.length):
            if i == 0 and TargetTime < 0:
                return self.GetVal(strColName, i)
            T0 = self.GetVal("Time", i - 1)
            T1 = self.GetVal("Time", i)


def GetListOfLogFiles(strDir, strFile):
    lstOfFiles = os.listdir(strDir)
    lstOfFilesOut = []
    logFileLen = len(strFile)
    for f in lstOfFiles:
        if len(f) >= logFileLen:
            if f[:logFileLen] == strFile:
                lstOfFilesOut.append(f)

    # breakpoint()
    return lstOfFilesOut


# def DeleteGetStartOfVelocity(CRV_obj, R1, strFile):

#     for i in range(CRV_obj.length):
#         # initialization of vaiable values
#         V = CRV_obj.Df.at[i, "FiltVel"]
#         T = CRV_obj.Df.at[i, "Time"]
#         if V > 5:
#             Output = {strFile + "StartDelay_sec": T}
#             R1.UpdateResults(Output, os.path.join(R1.strDir, "results.yml"))

#             break

#     return pprint.pformat(Output)
