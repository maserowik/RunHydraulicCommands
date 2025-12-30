import subprocess
import time
import sys
import re
import os
from utils import logger
import statistics
from .keys import GetKeyRoot, GetKeySeeg

# startCode = "ADD HERE"
# endCode = "ADD HERE"
# cmd = "screen -S s1 -d -m watch -n 1 date"
# results = subprocess.run(cmd, capture_output=True, text=True, shell=True)


def GetStartCode():
    return "sadfoiuYbciu23"


def GetEndCode():
    return "d8ik4n_asdf"


def Test():
    print("test")


def remove_control_characters(text):
    """Removes control characters and color codes from a string."""

    # Remove ANSI escape sequences (color codes, etc.)
    text = re.sub(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])", "", text)

    # Remove other control characters
    # text = re.sub(r"[\x00-\x1F\x7F-\x9F]", "", text)

    return text


def TermCmd(strCmd: str):
    """send string of command to terminal, waits for response, closes terminal.
        Does not use screen, use for simple terminal command request

    Args:
        strCmd (string): Command String

    Returns:
        _type_: string
    """
    result = subprocess.run(strCmd, capture_output=True, text=True, shell=True)
    return result.stdout


def getScreenSessions():
    """return list of tuples [(session ID as string, session name as string)]

    Returns:
        _type_: return list of tuples
    """
    strOutput = TermCmd("screen -ls")
    lstLines = strOutput.splitlines()
    pattern = r"^\s*(\d*)\.(\w*)"

    out = []
    for l in lstLines:

        match = re.search(pattern, l)

        if match:
            out.append((match.group(1), match.group(2)))

    return out


def IsScreenPresent(strScreenName):
    lstScreens = getScreenSessions()
    if len(lstScreens) > 0:
        unzipped_list = list(zip(*lstScreens))
        lstIDs, lstNames = [list(x) for x in unzipped_list]
        if strScreenName in lstNames:
            return True
        else:
            return False

    return False


def KillScreenSession(strScreenName):
    lstScreens = getScreenSessions()
    if len(lstScreens) > 0:
        # unzipped_list = list(zip(*lstScreens))
        # lstIDs, lstNames = [list(x) for x in unzipped_list]
        for i in lstScreens:
            if i[1] == strScreenName:
                TermCmd("screen -XS {} quit".format(i[0]))


def getLogOutput(strLogFileName, Type="long"):
    """get log output

    Args:
        strLogFileName (_type_): log file, use complete path

    Returns:
        _type_: string
    """

    strLogFileName = "'{}'".format(strLogFileName)

    if Type == "long":
        out = TermCmd("cat {}".format(strLogFileName))
    else:
        out = TermCmd("tail -5 {}".format(strLogFileName))
    return remove_control_characters(out)


# x =
# def waitUntilCondition(lambdaFun, timeOut):
#     TimeOut = 2
#     Time = 0
#     while os.path.exists(strLogFileName) == False:
#         Time = Time + 0.2
#         time.sleep(0.2)
#         if Time > TimeOut:
#             break


def KillAllScreenSessions():
    logger.debug("killing all screen sessions")
    lstSessionIDs = getScreenSessions()
    logger.debug(lstSessionIDs)

    for ii in lstSessionIDs:
        # breakpoint()
        cmd = "screen -X -S {} quit".format(ii[0])
        TermCmd(cmd)


def OpenScreenSession(strName):
    strCmd = "screen -S {} -d -m /bin/bash".format(strName)
    logger.debug("  OpeningScreen session with: {}".format(strCmd))
    TermCmd(strCmd)
    logger.debug("  Finished OpenScreenSession")
    time.sleep(3)


def setUpLogginSession(strSessionName, strLogFile, intUpdateRate):

    # strLog = "screen -S {} -X colon 'logfile \"{}\" ^M'".format(
    #     strSessionName, strLogFile
    # )

    strLog = r"""screen -S {} -X colon 'logfile "{}" ^M'""".format(
        strSessionName, strLogFile
    )
    strUpdateRate = "screen -S {} -X colon 'logfile flush {}^M'".format(
        strSessionName, str(intUpdateRate)
    )

    logger.debug("  Setting up logging session with:")
    logger.debug("      {}".format(strLog))
    logger.debug("      {}".format(strUpdateRate))
    TermCmd(strLog)
    TermCmd(strUpdateRate)
    logger.debug("  Finished setUpLogginSession")
    # breakpoint()


def StartLog(strSessionName):
    logger.debug(" StartLog for {}".format(strSessionName))
    strCmd = "screen -S {} -X log on".format(strSessionName)
    logger.debug("      {}".format(strCmd))
    TermCmd(strCmd)
    time.sleep(1)


def StopLog(strSessionName):
    logger.debug(" StopLog for {}".format(strSessionName))
    strCmd = "screen -S {} -X log off".format(strSessionName)
    logger.debug("      {}".format(strCmd))
    TermCmd(strCmd)
    time.sleep(1)


def ClearLogFile(strLogFileName):
    if os.path.exists(strLogFileName):
        TermCmd("> {}".format(strLogFileName))
    time.sleep(1)


def CheckLogForKeyWord(strLogFileName, strKeyWord, TimeOut=60):
    pass


def SendCommandWithPasswordPrompt(
    strSessionName, strCommand, strLogFileName, strPassword
):
    ClearLogFile(strLogFileName)
    StartLog(strSessionName)
    SendCommandToSession(strSessionName, strCommand)

    Timer = 0
    KeepLooping = True
    while KeepLooping:
        out = getLogOutput(strLogFileName)
        listOut = out.splitlines()
        for line in listOut:
            if "Password:" in line:
                time.sleep(1)
                SendCommandToSession(strSessionName, strPassword)
                StopLog(strSessionName)
                KeepLooping = False
                break
        if KeepLooping == False:
            break

        Timer = Timer + 0.2
        time.sleep(0.2)
        if Timer > 20:
            logger.critical("Never received Password prompt")
            breakpoint()
            break


def SendCommandToSessionWithFeedback(strSessionName, strCommand, strLogFileName):
    # breakpoint()
    if os.path.exists(strLogFileName):

        TermCmd("> '{}'".format(strLogFileName))

    StartLog(strSessionName)

    SendCommandToSession(
        strSessionName, r"echo \$startCode ;" + strCommand + r"; echo \$endCode"
    )

    Timer = 0
    while True:
        out = getLogOutput(strLogFileName, Type="short")
        listOut = out.splitlines()

        if len(listOut) > 1:
            if listOut[-2] == GetEndCode():
                outRaw = getLogOutput(strLogFileName)
                outRawLines = outRaw.splitlines()

                startLine = 0
                endLine = 0
                i = 0
                for line in outRawLines:
                    if line == GetStartCode():
                        startLine = i
                    if line == GetEndCode():
                        endLine = i

                    i = i + 1
                outRawLinesReduced = outRawLines[startLine + 1 : endLine]
                out = "\n".join(outRawLinesReduced)

                StopLog(strSessionName)
                TermCmd("> '{}'".format(strLogFileName))
                return out

        time.sleep(0.1)
        Timer = Timer + 0.1
        if Timer > 120:
            breakpoint()


def SendCommandToSession(strSessionName, strCommand):
    strCmd = "screen -S {} -X stuff '{}^M'".format(strSessionName, strCommand)
    TermCmd(strCmd)
    time.sleep(1)


def SendCtrl_C(strSessionName):
    strCmd = "screen -S {} -X stuff '^C^M'".format(strSessionName)
    TermCmd(strCmd)


def SetEnvVarCode(strSession):

    SendCommandToSession(strSession, "startCode='{}'".format(GetStartCode()))
    SendCommandToSession(strSession, "endCode='{}'".format(GetEndCode()))


class SCREEN:

    def __init__(self, strScreenName, strPath):
        logger.debug("Initializing Screen object for {}".format(strScreenName))
        self.strScreenName = strScreenName
        self.strPath = strPath
        # self.fullLogFile = os.path.join(strPath, strScreenName + ".log")
        self.fullLogFile = strScreenName + ".log"
        self.defAxis = ""
        self.seeg_pswd = GetKeySeeg()
        self.root_pswd = GetKeyRoot()

        pass

    def StartScreen(self):
        logger.debug("StartingScreen()")
        OpenScreenSession(self.strScreenName)
        setUpLogginSession(self.strScreenName, self.fullLogFile, 1)
        # StartLog(self.strScreenName)
        SetEnvVarCode(self.strScreenName)

    def RunHydralicPosCommand(self, intPos, strAxis, HomeOnStart=False):
        cmd = r"./trunk/bin/util/rcn/hydraulics-control-tuner -a {} -c {} -c 0".format(
            strAxis, str(intPos)
        )

        cmd_home = r"./trunk/bin/util/rcn/hydraulics-control-tuner -a {} -o -r -c {} -c 0".format(
            strAxis, str(intPos)
        )

        if HomeOnStart == True:
            cmd = cmd_home
        # breakpoint()
        self.SendShortCommand(cmd)
        # breakpoint()

    def SSHIntoVGU(self, strIpAddress):
        SendCommandToSession(self.strScreenName, "ssh seegrid@{}".format(strIpAddress))
        time.sleep(5)
        SetEnvVarCode(self.strScreenName)
        time.sleep(1)

    def SSHIntoRCN(self, strIpAddress):

        SendCommandToSession(
            self.strScreenName, "ssh -J seegrid@{} seegrid@rcn".format(strIpAddress)
        )
        time.sleep(5)
        SetEnvVarCode(self.strScreenName)
        time.sleep(1)

    def StopVSM(self):
        # SendCommandToSession(self.strScreenName, "systemctl stop vsm")
        SendCommandWithPasswordPrompt(
            self.strScreenName, "systemctl stop vsm", self.fullLogFile, self.seeg_pswd
        )
        # time.sleep(2)
        # SendCommandToSession(self.strScreenName, self.seeg_pswd)
        # time.sleep(5)

    def RunClearSafetyStop(self):
        SendCommandToSession(self.strScreenName, "./trunk/bin/clear-safety-stop")

    def RunBroadcastHeartBeat(self):
        SendCommandToSession(self.strScreenName, "./trunk/bin/broadcast-vsm-heartbeat")

    def RestartRCN(self):
        SendCommandWithPasswordPrompt(
            self.strScreenName,
            "systemctl restart rcn",
            self.fullLogFile,
            self.root_pswd,
        )

    def SendShortCommand(self, strCommand):
        """Return output from short command."""
        out = SendCommandToSessionWithFeedback(
            self.strScreenName, strCommand, self.fullLogFile
        )
        logger.debug("SendShortCommand: {}".format(strCommand))
        return out

    def setAxis(self, strAxis):
        self.defAxis = strAxis

    def StartAxisMeasurement(self):

        SendCtrl_C(self.strScreenName)
        time.sleep(1)

        strCommand = "./trunk/util/misc/print-hydraulic-positions.py -a {}".format(
            self.defAxis
        )

        SendCommandToSession(self.strScreenName, strCommand)
        time.sleep(1)

    def GetAxisFeedback(self):
        self.StartAxisMeasurement()
        if os.path.exists(self.fullLogFile):
            TermCmd("> '{}'".format(self.fullLogFile))
        StartLog(self.strScreenName)
        lineCount = 0
        time.sleep(1)
        while lineCount < 100:
            localCmd = "cat '{}' |wc -l ".format(self.fullLogFile)
            LineCount_str = TermCmd(localCmd)
            lineCount = int(LineCount_str)
            time.sleep(0.5)
        StopLog(self.strScreenName)

        raw_out = getLogOutput(self.fullLogFile)
        pattern = "^{}: ([+-]?([0-9]*[.])?[0-9]+)".format(self.defAxis)
        raw_out_lst = raw_out.splitlines()
        valList = []
        for line in raw_out_lst:
            match = re.search(pattern, line)
            if match:
                val = match.group(1)
                valList.append(float(val))

        try:
            valMean = statistics.mean(valList)
            # breakpoint()
        except:
            breakpoint()

        logger.debug(valMean)
        return valMean

    def __del__(self):
        pass
        # print("killing screen session {}".format(self.strScreenName))
        # TermCmd("rm {}".format(self.fullLogFile))
        # KillScreenSession(self.strScreenName)

    def killScreen(self):
        pass


# OpenScreenSession("s3")

# setUpLogginSession("s3", 1)
# StartLog("s3")
# time.sleep(0.5)
# SetEnvVarCode("s3")
# SendCommandToSession("s3", "for run in {1..10}; do date; done")
# time.sleep(0.5)
# strOut = TermCmd("cat s3.log")
# strOut = remove_control_characters(strOut)


"""
Create linux Session Object

Start Session

VSM---f1.stop_vsm()----|
RCN-------------------pause()----f2.restart_rcn---|
VSM2--------------------------------------------------f3.broadcast_vsm_heartbeat()---------------------------->
VSM3--------------------------------------------------f4.run_clear_safety_stop()------------------------------>
VSM4--------------------------------------------------------------------------------f4.run_axis_feedback------>
VSM5--------------------------------------------------------------------------------------f5.execute_hyd_cmd-->



Pseudo Code

1) StopVSM()   (blocking function)
2) pause
3) RestartRCN()  (blocking function)
4) pause
5) VSM_Obj1 = startVSMSession()
6) VSM_Obj1.sendCommand("broadcast_vsm_heartbeat()")
7) VSM_Obj2 = startVSMSession()
8) VSM_Obj2.sendCommand("clear_safey_stop()")
9) pause
10) VSM_Ob3.sendCommand("run_axis_feedback")
11) pause
12) VSM_Ob3.getPosFeedback(strAxis)  (blocking function)
13) RCN_Ob4 = startRCNSession()
14) pause
15) RCN_Ob4.runAxisFeedback("hyd command")  (blocking function)


Sending command with fixed short life and no return value

1) Initialize session object
2) Initialize logging details (log rate, log name, start log)
3) If log file exists, erase details
4) Wait until log file exists
5) Send command to screen session
6) Read log file until output code is read
7) Stop logging
8) Delete Log File
9) End Screen Session


Sending Stop VSM:

1) Initialize session object
2) Initialize logging details (log rate, log name, start log)
3) If log file exists, erase details
4) Wait until log file exists
5) SSHintoVehicle()
6) SendCommand(id -un) == seegird
7) SendEnvVariables


"""


def CheckForCompletion(strSessionName, TimeoutSec):

    startTime_sec = time.time()
    pass


# text_out = open("out.log", "w")
# text_out.write(strOut)

# for i in range(10):
#     strOut = getLogOutput("s3.log")
#     strOut = remove_control_characters(strOut)
#     print(strOut)
#     time.sleep(0.5)

"""

set log file name
screen -S screenName -X colon 'logfile logFileName.log ^M'

screen -S s3 -X colon 'logfile logFileName.log ^M'

set update rate
screen -S screenName -X colon "logfile flush int^M"
int is num in seconds, can be 0 for real time

start logging
screen -S screen -X log on

stop logging
screen -S screen -X log off 


"""
