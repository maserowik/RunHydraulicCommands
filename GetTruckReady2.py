from remote_ctrl import RemoteTest, RemoteSSH, RemoteSCREEN
import remote_ctrl.screen as scr
from utils import logger, YmlManager, OutFile, OutProcess
import os

myYml = YmlManager(os.path.join(os.getcwd(), "project.yml"))
CallerPath = os.getcwd()
dictProject = myYml.Convert2Dictionary()
strIP = dictProject["IPAddress"]

scr.KillAllScreenSessions()

VSM_short = scr.SCREEN("VSM_short", CallerPath)
VSM_short.StartScreen()
VSM_short.SSHIntoVGU(strIP)


VSM_pos = scr.SCREEN("VSM_pos", CallerPath)
VSM_pos.StartScreen()
VSM_pos.SSHIntoVGU(strIP)

RCN_short = scr.SCREEN("RCN_short", CallerPath)
RCN_short.StartScreen()
RCN_short.SSHIntoRCN(strIP)


strExit = "N"

while strExit != "Y":
    strExit = input("Exit (Type: Y)?")
    if strExit == "Y":
        scr.KillAllScreenSessions()
