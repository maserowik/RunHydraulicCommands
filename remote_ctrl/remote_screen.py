from abc import ABC, abstractmethod
from .remote import Remote
import pexpect
from cryptography.fernet import Fernet
import re
import statistics
import time
from .screen import SCREEN
import remote_ctrl.screen as scr
import os


from utils import flt2str, logger, GetYearMonthDate, GetEpochTime, ReduceStringSize


class RemoteSCREEN(Remote):
    def __init__(self, boolPsswdNeeded: bool, strIP: str):
        self.hi = "asdf"
        # self.keyDecript = self.GetKey()
        self.__defAxis = ""
        self.boolNeed2GetLatestFile = False
        self.strRemoteLogFile: str = ""
        self.passWdRequired = boolPsswdNeeded
        self.strIP = strIP
        self.CallerPath = os.getcwd()

        self.VSM_short = scr.SCREEN("VSM_short", self.CallerPath)

        self.VSM_clear = scr.SCREEN("VSM_clear", self.CallerPath)

        self.VSM_brd = scr.SCREEN("VSM_brd", self.CallerPath)

        self.VSM_pos = scr.SCREEN("VSM_pos", self.CallerPath)

        self.RCN_short = scr.SCREEN("RCN_short", self.CallerPath)

    def GetDefAxis(self):
        return self.__defAxis

    def SetDefAxis(self, strAxis):
        self.VSM_pos.setAxis(strAxis)
        self.VSM_pos.StartAxisMeasurement()

        if strAxis != self.GetDefAxis():
            self.boolNeed2GetLatestFile = True

        self.__defAxis = strAxis

    def GetVehicleName(self) -> str:
        strCmd = "cat /etc/hostname"
        strOutName = self.sendSSHCommand(strCmd)
        # logger.info("VEH NAME: " + strOutName)
        strCmd = "cat /etc/motd"
        strOutSoft = self.sendSSHCommand(strCmd)
        strOutString = "VEH NAME: {}  SOFT: {}".format(strOutName, strOutSoft)
        logger.info(strOutString)
        return strOutString

    def sendSSHCommand(self, strCmd, withJump=False):

        logger.info("Running cmd: " + strCmd)

        if withJump == False:
            strOut = self.VSM_short.SendShortCommand(strCmd)
        else:
            strOut = self.RCN_short.SendShortCommand(strCmd)

        logger.info("Output: " + "\n" + ReduceStringSize(strOut))

        return strOut

    def GetLineCount(self):
        strMatch = ".+\.([a-z]+)"

        strFileType = re.match(strMatch, self.strRemoteLogFile).group(1)

        if strFileType == ".gz":
            strCommand = "zcat {} | wc -l".format(self.strRemoteLogFile)
        else:
            strCommand = "cat {} | wc -l".format(self.strRemoteLogFile)

        stdout: str = self.sendSSHCommand(strCommand)
        return (True, int(stdout.splitlines()[0]))

    def RunHydrCommand(self, strAxis, tgPosition, start=False):
        if start == False:
            hydCommand = r"./trunk/bin/util/rcn/hydraulics-control-tuner -a {} -c {} -c 0".format(
                strAxis, tgPosition
            )
        else:
            hydCommand = r"./trunk/bin/util/rcn/hydraulics-control-tuner -a {} -o -r -c {} -c 0".format(
                strAxis, tgPosition
            )
        # strCommand = r'ssh -J seegrid@{} seegrid@rcn "{}"'.format(hostname, hydCommand)

        stdout = self.sendSSHCommand(hydCommand, withJump=True)
        print("Hydcommand finished")

        if self.boolNeed2GetLatestFile == True:
            logger.info("Identifying latest log file")
            _, self.strRemoteLogFile = self.GetLogFileAtMachine()
            self.boolNeed2GetLatestFile = False

        return (True,)

    def GetCurrentPosition(self, strAxis):
        outMean = self.VSM_pos.GetAxisFeedback()

        if strAxis == "tilt":
            outMean = outMean * 0.0174533

        return (True, outMean)

    def GetLogFileOutput(self, intStartRow, intEndRow):
        strFileName = self.strRemoteLogFile
        strCmd = r'awk "NR > {}  && NR <= {}" {}'.format(
            str(intStartRow), str(intEndRow), strFileName
        )
        # breakpoint()
        strOut = self.sendSSHCommand(strCmd)
        logger.info("Log file output: \n {}".format(ReduceStringSize(strOut)))
        return (True, strOut)

    def GetLogFileAtMachine(self):
        strLogLocation = "/home/seegrid/Logs"
        strYear, strMonth, strDate = GetYearMonthDate()
        strLogLocationToday = "{}/{}/{}/{}".format(
            strLogLocation, strYear, strMonth, strDate
        )

        logger.info("Log file location: " + strLogLocationToday)

        # strFindCommand = r'find {} -name "*servo-axis-{}*" -printf "%p %t\n"'.format(strLogLocationToday, strAxis)

        # r'find /home/seegrid/Logs/2024/10/28 -name "*servo-axis-lift*" -printf "%p %t\n"'
        strFindCommand = r'find {} -name "*servo-axis-{}*"'.format(
            strLogLocationToday, self.GetDefAxis()
        )

        logger.info("Submit command for file find: \n" + strFindCommand)

        stdout: str = self.sendSSHCommand(strFindCommand)

        lstFiles = stdout.splitlines()

        strMatchPattern = "^.+/(\d+)_(\d+)_(\d+)"

        # strYear, strMonth, strDate = self.L1.GetYearMonthDate()
        listFilesAndDates = []
        for i in lstFiles:
            if re.search(strMatchPattern, i):
                hr = re.search(strMatchPattern, i).group(1)
                min = re.search(strMatchPattern, i).group(2)
                sec = re.search(strMatchPattern, i).group(3)

                strTimeStamp = "{} {} {} {}:{}:{}".format(
                    strYear, strMonth, strDate, hr, min, sec
                )
                intEpochTime = GetEpochTime(
                    strTimeStamp, strTimeFromat="%Y %m %d %H:%M:%S"
                )
                listFilesAndDates.append([i, intEpochTime])

        def getThird(e):
            return e[1]

        listFilesAndDates.sort(key=getThird, reverse=True)
        # breakpoint()
        outFile = listFilesAndDates[0][0]
        logger.info("Found file: " + outFile)
        return (True, outFile)
