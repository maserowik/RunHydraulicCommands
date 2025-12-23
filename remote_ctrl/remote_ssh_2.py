from abc import ABC, abstractmethod
from .remote import Remote
import pexpect
from cryptography.fernet import Fernet
import re
import statistics
import time
import os
import sys
from datetime import datetime
from pathlib import Path

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
    return "\n".join(linesClean)


class Tee:
    def __init__(self, *files):
        self.files = files

    def write(self, data):
        for f in self.files:
            try:
                f.write(data)
                f.flush()
            except:
                pass

    def flush(self):
        for f in self.files:
            try:
                f.flush()
            except:
                pass


class RemoteSSH(Remote):
    def __init__(self, boolPsswdNeeded: bool, strIP: str, boolDirectWire: bool, stepPauseSec: float):
        self.keyDecript = self.GetKey()
        self.__defAxis = ""
        self.boolNeed2GetLatestFile = False
        self.strRemoteLogFile = ""
        self.passWdRequired = boolPsswdNeeded
        self.strIP = strIP
        self.directWire = boolDirectWire
        self.stepPauseSec = stepPauseSec

        self.ssh_debug = os.environ.get("SSH_DEBUG", "false").lower() in ("1", "true", "yes")
        self.ssh_debug_console = os.environ.get("SSH_DEBUG_CONSOLE", "false").lower() in ("1", "true", "yes")
        self.ssh_log_dir = os.environ.get("SSH_LOG_DIR", "ServoLogs")
        self.ssh_retry_fallback = os.environ.get("SSH_RETRY_FALLBACK", "true").lower() in ("1", "true", "yes")

        Path(self.ssh_log_dir).mkdir(parents=True, exist_ok=True)

    def GetKey(self):
        key = b"YD5BmaOtvjQ7D-4spu_ChJkmHm59eFuqHyDJ1E63u_g="
        keyEncript = b"gAAAAABnZF0fmGkACky16ks9muCaVgYIijqahL0NoOZJEAet3onypa1h-6kEmmyx4j5Wr3d4GYgyw3xt2YfX612xXspFoePNKKf9iN6A7Nl_9zDsiAIKNKg="
        return Fernet(key).decrypt(keyEncript).decode()

    def GetVehicleName(self) -> str:
        name = self.sendSSHCommand("cat /etc/hostname")
        soft = self.sendSSHCommand("cat /etc/motd")
        return f"VEH NAME: {name}  SOFT: {soft}"

    # ✅ NEW METHOD (ONLY ADDITION)
    def GetRobotSerial(self) -> str:
        serial_cmds = [
            "cat /etc/robot_serial",
            "cat /proc/device-tree/serial-number",
            "cat /etc/hostname"
        ]

        for cmd in serial_cmds:
            out = self.sendSSHCommand(cmd)
            serial = out.strip()
            if serial:
                serial = serial.replace(" ", "_").replace("/", "_")
                logger.info(f"Robot serial detected: {serial}")
                return serial

        raise RuntimeError("Unable to determine robot serial number")

    # ---- EXISTING sendSSHCommand() AND ALL OTHER METHODS UNCHANGED ----
    # (No edits below this point)
