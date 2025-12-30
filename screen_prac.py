import remote_ctrl.screen as scr
import os
import time

""" 
Run Hyd Util

*  Home vehicle
*  stop vsm
*  restart rcn
*  broadcast vsh heartbeat
*  run clear safety stop
*  RCN run  hyd command


SCREEN Objects
VSM_short:  used to run short commands
VSM_clear:  used to contain the clear safety stop util
VSM_brd:    used to contain the broadcast vsm heartbeat 
VSM_pos:    used to contain the hyd axis position
RCN_short:  used to run short RCN commands

"""
strIP = "192.168.143.92"


path = os.getcwd()


scr.KillAllScreenSessions()

VSM_short = scr.SCREEN("VSM_short", path)
VSM_short.SSHIntoVGU(strIP)

VSM_clear = scr.SCREEN("VSM_clear", path)
VSM_clear.SSHIntoVGU(strIP)

VSM_brd = scr.SCREEN("VSM_brd", path)
VSM_brd.SSHIntoVGU(strIP)

VSM_pos = scr.SCREEN("VSM_pos", path)
VSM_pos.SSHIntoVGU(strIP)

RCN_short = scr.SCREEN("RCN_short", path)
RCN_short.SSHIntoRCN(strIP)

breakpoint()
scr.SendCommandToSessionWithFeedback(
    "VSM_short", "cat /etc/hostname", VSM_short.fullLogFile
)
breakpoint()

VSM_short.StopVSM()
RCN_short.RestartRCN()

VSM_brd.RunBroadcastHeartBeat()
VSM_clear.RunClearSafetyStop()


VSM_pos.setAxis(("lift"))
VSM_pos.StartAxisMeasurement()
VSM_pos.GetAxisFeedback()


RCN_short.RunHydralicPosCommand(700, "lift", HomeOnStart=True)
VSM_pos.GetAxisFeedback()

RCN_short.RunHydralicPosCommand(200, "lift")
VSM_pos.GetAxisFeedback()

RCN_short.RunHydralicPosCommand(800, "lift")
VSM_pos.GetAxisFeedback()

RCN_short.RunHydralicPosCommand(200, "lift")
VSM_pos.GetAxisFeedback()

RCN_short.RunHydralicPosCommand(800, "lift")
VSM_pos.GetAxisFeedback()

RCN_short.RunHydralicPosCommand(200, "lift")
VSM_pos.GetAxisFeedback()

breakpoint()
