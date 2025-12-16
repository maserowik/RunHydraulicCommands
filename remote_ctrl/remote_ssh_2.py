from abc import ABC, abstractmethod
from .remote import Remote
import pexpect
from cryptography.fernet import Fernet
import re
import statistics
import time

from utils import flt2str, logger, GetYearMonthDate, GetEpochTime, ReduceStringSize

def CleanTextFileTimeColumn(text_string):
    lines = text_string.splitlines()
    lines = lines[7:]

    pattern = r"^(\[.+]\s+).+"
    linesClean = []
    for line_single in lines:
        try:
            match = re.search(pattern, line_single)
            str_remove = match.group(1)
            line_single = line_single.replace(str_remove, "")
            linesClean.append(line_single)
        except:
            pass
    linesClean.insert(
        0,
        "Time_s,Cmd,LastPos,EstPos,EstVel,TgtPos,TgtVel,ErrPos,ErrVel,State,AxisError",
    )
    print("===================")
    textClean = "\n".join(linesClean)
    return textClean


class RemoteSSH(Remote):
    def __init__(self, boolPsswdNeeded: bool, strIP: str, boolDirectWire:bool, stepPauseSec: float):
        self.hi = "asdf"
        self.keyDecript = self.GetKey()
        self.__defAxis = ""
        self.boolNeed2GetLatestFile = False
        self.strRemoteLogFile: str = ""
        self.passWdRequired = boolPsswdNeeded
        self.strIP = strIP
        self.directWire = boolDirectWire
        self.stepPauseSec = stepPauseSec

    def GetDefAxis(self):
        return self.__defAxis
    

    def SetDefAxis(self, strAxis):
        if strAxis != self.GetDefAxis():
            self.boolNeed2GetLatestFile = True

        self.__defAxis = strAxis

    def GetKey(self):

        key = b"YD5BmaOtvjQ7D-4spu_ChJkmHm59eFuqHyDJ1E63u_g="
        keyEncript = b"gAAAAABnZF0fmGkACky16ks9muCaVgYIijqahL0NoOZJEAet3onypa1h-6kEmmyx4j5Wr3d4GYgyw3xt2YfX612xXspFoePNKKf9iN6A7Nl_9zDsiAIKNKg="
        fernet = Fernet(key)
        keyDecript = fernet.decrypt(keyEncript).decode()
        return keyDecript
    
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

        keyWord = "END"
        directWire = self.directWire
        

        if self.directWire==False:
            if withJump == False:
                cmd = r'ssh seegrid@{} "{};echo {}"'.format(self.strIP, strCmd, keyWord)
            elif withJump == True:
                cmd = r'ssh -J seegrid@{} seegrid@rcn "{};echo {}"'.format(
                    self.strIP, strCmd, keyWord
                )
        else:
            if withJump == False:
                cmd = r'ssh seegrid@10.0.0.2 "{};echo {}"'.format(strCmd, keyWord)
            elif withJump == True:
                cmd = r'ssh seegrid@10.0.0.9 "{};echo {}"'.format(strCmd, keyWord)

        logger.info("Running cmd: " + cmd)

        def ExpectSpawn(cmd):
            child = pexpect.spawn(cmd, timeout=120)
            logger.info("Spawing command {}".format(cmd))
            
            if withJump == True and self.passWdRequired == True:
                logger.info("Wating for password /w jump")
                #need to remove interact()
                # child.interact()
                child.expect("password:")
                child.sendline(self.keyDecript)
            elif directWire==True:
                logger.info("Wating for password")
                #need to remove interact()
                # child.interact()
                child.expect("password:")
                child.sendline(self.keyDecript)

          

            child.expect(keyWord)

            strOut = child.before.decode("utf-8")

            logger.info("Output: " + "\n" + ReduceStringSize(strOut))
            return strOut

        try: 
            strOut=ExpectSpawn(cmd)
        except:
            try:
                logger.info("Failed running {} in expect.spawn, attempting second time".format(cmd))  
                strOut=ExpectSpawn(cmd)
            except:
                logger.info("Failed running {} in expect.spawn, attempting third time".format(cmd))  
                strOut=ExpectSpawn(cmd)

        return strOut
    
    def RunHydrCommand(self, strAxis, tgPosition, start=False):
        if start == False:
            hydCommand = r"./trunk/bin/util/rcn/hydraulics-control-tuner -a {} -b -c {} -c 0".format(
                strAxis, tgPosition
            )
        else:
            hydCommand = r"./trunk/bin/util/rcn/hydraulics-control-tuner -a {} -b -o -r -c {} -c 0".format(
                strAxis, tgPosition
            )
   

        stdout = self.sendSSHCommand(hydCommand, withJump=True)
        time.sleep(3)
        if self.stepPauseSec>1:
            logger.info("Waiting {} seconds for hydraulic cool down".format(self.stepPauseSec))
            time.sleep(self.stepPauseSec)

        if self.boolNeed2GetLatestFile == True:
            logger.info("Identifying latest log file")
            _, self.strRemoteLogFile = self.GetLogFileAtMachine()
            self.boolNeed2GetLatestFile = False

        return (True,)
    
    def GetLogFileAtMachine(self):
        strLogLocation = "/home/seegrid/Logs"
        strYear, strMonth, strDate = GetYearMonthDate()
        strLogLocationToday = "{}/{}/{}/{}".format(
            strLogLocation, strYear, strMonth, strDate
        )

        logger.info("Log file location: " + strLogLocationToday)

        strFindCommand = r'find {} -name "*servo-axis-{}*"'.format(
            strLogLocationToday, self.GetDefAxis()
        )

        logger.info("Submit command for file find: \n" + strFindCommand)

        stdout: str = self.sendSSHCommand(strFindCommand)

        lstFiles = stdout.splitlines()

        strMatchPattern = "^.+/(\d+)_(\d+)_(\d+)-hydraulic-control-tuner"

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

        if len(listFilesAndDates)==0:
            self.strRemoteLogFile="noFileFound"
            return (True, "noFileFound")
    

        def getThird(e):
            return e[1]

        listFilesAndDates.sort(key=getThird, reverse=True)
        # breakpoint()
        outFile = listFilesAndDates[0][0]
        logger.info("Found file: " + outFile)
        self.strRemoteLogFile=outFile
        return (True, outFile)
    
    def GetLogFileOutput(self):
        strFileName = self.strRemoteLogFile
  
        strCmd = r"cat {}".format(strFileName)
        # breakpoint()
        strOut = self.sendSSHCommand(strCmd)
        # breakpoint()
 
        strOut =CleanTextFileTimeColumn(strOut)
       

        logger.info("Log file output: \n {}".format(ReduceStringSize(strOut)))
        return (True, strOut)
    
    def GetCurrentPosition(self, strAxis):
        strCmd = "~/trunk/util/misc/print-hydraulic-positions.py -a {}".format(strAxis)
        strCmd = "timeout 2s {}".format(strCmd)
        logger.info("Getting current position for " + strAxis + ":")
        logger.info("Running command \n" + strCmd)

        stdout: str = self.sendSSHCommand(strCmd)
        lstLines = stdout.splitlines(True)

        strMatchPattern = "^{}:\s+([-]?\d+\.\d+)".format(strAxis)
        newList = [
            float(re.search(strMatchPattern, x).group(1))
            for x in lstLines
            if re.search(strMatchPattern, x)
        ]

        try:
            outMean = statistics.mean(newList)
        except:
            print("arrr")
            breakpoint()
        logger.info("Mean: " + str(outMean))

        if strAxis == "tilt":
            outMean = outMean * 0.0174533

        # return outMean
        return (True, outMean)
    
    def GetLineCount(self):

        return (True, 1)