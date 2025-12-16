import os
from utils import PrCSV
from utils import flt2str

# from utils.config import *
import pprint

# from utils.utilLogProcess import *
import statistics


# Available columns in PD frame

# "Time"
# "SystemTime",
# "Command",
# "LastPosition",
# "InterpolatedPosition",
# "FiltVel",
# "TargetPosition",
# "TargeVelocity",
# "ErrPos",
# "ErrVel",
# "Mode",
# "None",


def GetMaxVelocityInst(CRV_obj: PrCSV, inputArgs):
    # Gets largest velocty error sustained for timeWindow_ms
    
    
    timeWindow_ms = inputArgs["timeWindow_ms"]

    Output = {
        "MaxVinst": "0",
        "MaxVinstStatus": "MetricNotFound",
        "MaxVinstSystemTime": flt2str(CRV_obj.GetVal("SystemTime", 0)),
    }

    timeWindow_s = timeWindow_ms * 0.001
    maxV = 0
    SysTime = 0

    MeanV = CRV_obj.Df["FiltVel"].mean().item()

    for i in range(CRV_obj.length):
        Time = CRV_obj.GetVal("Time", i)
        Vel = CRV_obj.GetVal("FiltVel", i)
        IndexStart = CRV_obj.GetIndexAtTime(Time - timeWindow_s)
        IndexEnd = i
        tempMinV = Vel

        # us this condition to get instant max speed for inividual sample
        if timeWindow_ms < 1:
            IndexStart = IndexEnd
        if MeanV > 0:
            for j in range(IndexStart, IndexEnd + 1):
                tempMinV = min(tempMinV, CRV_obj.GetVal("FiltVel", j))

            if tempMinV > maxV:
                maxV = tempMinV
                SysTime = Time
        else:
            for j in range(IndexStart, IndexEnd + 1):
                tempMinV = max(tempMinV, CRV_obj.GetVal("FiltVel", j))

            if tempMinV < maxV:
                maxV = tempMinV
                SysTime = Time

    # breakpoint()

    Output = {
        "MaxVinst": flt2str(maxV, 5),
        "MaxVinstStatus": "OK",
        "MaxVinstSystemTime": flt2str(SysTime),
    }

    return Output


def GetMaxVelocity(CRV_obj: PrCSV, inputArgs):
    MaxTargetV_mmpsec = inputArgs["MaxTargetV_mmpsec"]
    DelayStart_ms = inputArgs["DelayStart_ms"]

    # default output
    Output = {
        "MaxV": "0",
        "MaxVStatus": "MetricNotFound",
        "MaxVSystemTime": flt2str(CRV_obj.GetVal("SystemTime", 0), 2),
    }

    V_Max = []

    for i in range(CRV_obj.length):
        TargetV = CRV_obj.GetVal("TargetVelocity", i)
        Vel = CRV_obj.GetVal("FiltVel", i)
        Time = CRV_obj.GetVal("Time", i)

        TargetVDelayedIndex = CRV_obj.GetIndexAtTime((Time - 0.001 * DelayStart_ms), i)

        TargetVDelayed = CRV_obj.GetVal("TargetVelocity", TargetVDelayedIndex)
        if MaxTargetV_mmpsec > 0:
            if TargetV > MaxTargetV_mmpsec and TargetVDelayed > MaxTargetV_mmpsec:
                V_Max.append(Vel)
                T_Target = CRV_obj.GetVal("SystemTime", i)
        if MaxTargetV_mmpsec < 0:
            if TargetV < MaxTargetV_mmpsec and TargetVDelayed < MaxTargetV_mmpsec:
                # breakpoint()
                V_Max.append(Vel)
                T_Target = CRV_obj.GetVal("SystemTime", i)

    if len(V_Max) > 0:
        Output = {
            "MaxV": flt2str(statistics.mean(V_Max), 5),
            "MaxVStatus": "OK",
            "MaxVSystemTime": flt2str(T_Target),
        }
        return Output
    else:
        return Output


def GetStartOfMotionCommand(CRV_obj: PrCSV, inputArgs):
    # global R1
    VThresh = inputArgs["VThresh"]
    SystemDelay_ms = inputArgs["SystemDelay_ms"]

    # default output (must use strings)
    Output = {
        "Command": "0",
        "CommandDelayTime": "0",
        "CommandStatus": "MetricNotFound",
        "CommandSystemTime": flt2str(CRV_obj.GetVal("SystemTime", 0)),
    }

    def GetOutput():
        newIndex = CRV_obj.GetIndexAtTime(Time - SystemDelay_ms * 0.001)
        DelayTime = CRV_obj.GetVal("Time", newIndex)
        OutCommand = CRV_obj.GetVal("Command", newIndex)
        SystemTime = CRV_obj.GetVal("SystemTime", newIndex)
        Output = {
            "Command": flt2str(OutCommand),
            "CommandDelayTime": flt2str(DelayTime),
            "CommandStatus": "OK",
            "CommandSystemTime": flt2str(SystemTime, 0),
        }
        return Output

    for i in range(CRV_obj.length):
        Vel = CRV_obj.GetVal("FiltVel", i)
        Time = CRV_obj.GetVal("Time", i)
        Command = CRV_obj.GetVal("Command", i)

        if VThresh < 0:
            if Vel < VThresh:
                Output = GetOutput()
                break

        if VThresh > 0:
            if Vel > VThresh:
                Output = GetOutput()
                break

    return Output


def GetMaxVelocityError(CRV_obj: PrCSV, inputArgs):
    timeWindow_ms = inputArgs["timeWindow_ms"]

    Output = {
        "MaxVError": "0",
        "MaxVErrorStatus": "MetricNotFound",
        "MaxVErrorSystemTime": flt2str(CRV_obj.GetVal("SystemTime", 0)),
    }

    timeWindow_s = timeWindow_ms * 0.001
    maxV = 0
    SysTime = 0

    CmdAve = CRV_obj.Df["Command"].mean().item()

    for i in range(CRV_obj.length):
        Time = CRV_obj.GetVal("Time", i)
        Vel = CRV_obj.GetVal("ErrVel", i)
        IndexStart = CRV_obj.GetIndexAtTime(Time - timeWindow_s)
        IndexEnd = i
        tempMinV = Vel

        # us this condition to get instant max speed for inividual sample
        if timeWindow_ms < 1:
            IndexStart = IndexEnd
        if CmdAve > 0:
            for j in range(IndexStart, IndexEnd + 1):
                tempMinV = min(tempMinV, CRV_obj.GetVal("ErrVel", j))

            if tempMinV > maxV:
                maxV = tempMinV
                SysTime = Time
        else:
            for j in range(IndexStart, IndexEnd + 1):
                tempMinV = max(tempMinV, CRV_obj.GetVal("ErrVel", j))

            if tempMinV < maxV:
                maxV = tempMinV
                SysTime = Time

    Output = {
        "MaxVError": flt2str(maxV),
        "MaxVErrorStatus": "OK",
        "MaxVErrorSystemTime": flt2str(SysTime),
    }

    return Output
