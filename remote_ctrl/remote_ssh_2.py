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
    textClean = "\n".join(linesClean)
    return textClean


class Tee:
    """
    Simple tee writer that writes to multiple file-like objects.
    Used to write session bytes to both a file and stdout.
    """

    def __init__(self, *files):
        self.files = files

    def write(self, data):
        # pexpect gives str when encoding set; ensure bytes -> str conversions handled.
        for f in self.files:
            try:
                f.write(data)
                f.flush()
            except Exception:
                # ignore errors to avoid stopping session logging
                pass

    def flush(self):
        for f in self.files:
            try:
                f.flush()
            except Exception:
                pass


class RemoteSSH(Remote):
    def __init__(self, boolPsswdNeeded: bool, strIP: str, boolDirectWire: bool, stepPauseSec: float):
        self.hi = "asdf"
        self.keyDecript = self.GetKey()
        self.__defAxis = ""
        self.boolNeed2GetLatestFile = False
        self.strRemoteLogFile: str = ""
        self.passWdRequired = boolPsswdNeeded
        self.strIP = strIP
        self.directWire = boolDirectWire
        self.stepPauseSec = stepPauseSec

        # --- runtime config toggles (can be overridden by env vars or caller) ---
        # Enable verbose SSH debug logging (True/False)
        self.ssh_debug = os.environ.get("SSH_DEBUG", "false").lower() in ("1", "true", "yes")
        # Show live SSH session on console
        self.ssh_debug_console = os.environ.get("SSH_DEBUG_CONSOLE", "false").lower() in ("1", "true", "yes")
        # Directory to write SSH session logs
        self.ssh_log_dir = os.environ.get("SSH_LOG_DIR", "ServoLogs")
        # Enable retry fallback strategy
        self.ssh_retry_fallback = os.environ.get("SSH_RETRY_FALLBACK", "true").lower() in ("1", "true", "yes")

        # Ensure log directory exists
        try:
            Path(self.ssh_log_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create SSH log dir {self.ssh_log_dir}: {e}")

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

        strCmd = "cat /etc/motd"
        strOutSoft = self.sendSSHCommand(strCmd)

        strOutString = f"VEH NAME: {strOutName}  SOFT: {strOutSoft}"
        logger.info(strOutString)
        return strOutString

    # ----------------------------------------------------------------------
    # Enhanced sendSSHCommand with:
    #  - known_hosts clearing
    #  - session logging
    #  - live console tee
    #  - fallback retries
    #  - smart password detection
    # ----------------------------------------------------------------------
    def sendSSHCommand(self, strCmd, withJump=False):
        keyWord = "END"

        # Helper to create logfile path
        def _make_logfile_path(ip):
            now = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            safe_ip = ip.replace(".", "_")
            fname = f"ssh_{safe_ip}_{now}.log"
            return os.path.join(self.ssh_log_dir, fname)

        # Attempt sequence of different connection options (primary then fallbacks)
        attempts = []

        # Primary attempt: host-key checking disabled (recommended for lab)
        attempts.append({"directWire": self.directWire, "withJump": withJump, "bypassHostKey": True})

        # If retry fallback enabled, add fallback permutations
        if self.ssh_retry_fallback:
            # Try clearing known_hosts then connecting without strict bypass (some environments prefer this)
            attempts.append({"directWire": self.directWire, "withJump": withJump, "bypassHostKey": False, "clear_known_host_before": True})
            # Try alternate direct-wire IPs if original directWire fails (useful when switching robots)
            if self.directWire:
                attempts.append({"directWire": True, "withJump": withJump, "bypassHostKey": True, "force_ip": "10.0.0.2"})
                attempts.append({"directWire": True, "withJump": withJump, "bypassHostKey": True, "force_ip": "10.0.0.9"})

        last_exception = None

        # try each attempt sequentially
        for attempt_idx, attempt in enumerate(attempts):
            try:
                # allow override of ip
                target_ip = attempt.get("force_ip", self.strIP)

                # Optionally clear known_hosts for this ip
                if attempt.get("clear_known_host_before", False):
                    try:
                        os.system(f"ssh-keygen -R {target_ip} >/dev/null 2>&1")
                        logger.info(f"DEBUG: Cleared known_hosts for {target_ip} (pre-attempt)")
                    except Exception as e:
                        logger.error(f"DEBUG: Failed to clear known_hosts pre-attempt: {e}")

                # Also always remove old key for target ip to avoid host-key changed popups
                try:
                    os.system(f"ssh-keygen -R {target_ip} >/dev/null 2>&1")
                except:
                    pass

                bypass = attempt.get("bypassHostKey", True)
                use_directwire = attempt.get("directWire", self.directWire)
                use_withJump = attempt.get("withJump", withJump)

                if bypass:
                    host_opts = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
                else:
                    host_opts = ""

                if use_directwire is False:
                    if use_withJump is False:
                        cmd = rf'ssh {host_opts} seegrid@{target_ip} "{strCmd};echo {keyWord}"'
                    else:
                        # when using jump, keep bypass options applied to outer ssh
                        cmd = rf'ssh -J seegrid@{target_ip} seegrid@rcn {host_opts} "{strCmd};echo {keyWord}"'
                else:
                    # direct-wire fixed IPs — respect force_ip if provided
                    dw_ip = attempt.get("force_ip", "10.0.0.2" if not use_withJump else "10.0.0.9")
                    cmd = rf'ssh {host_opts} seegrid@{dw_ip} "{strCmd};echo {keyWord}"'

                # Normalize whitespace in command (when host_opts empty)
                cmd = " ".join(cmd.split())

                # Prepare logging / console streaming
                logfile_path = _make_logfile_path(target_ip)
                try:
                    log_fh = open(logfile_path, "a", encoding="utf-8", errors="replace")
                except Exception as e:
                    logger.error(f"Failed to open ssh logfile {logfile_path}: {e}")
                    log_fh = None

                # If console streaming requested, tee to both console and file
                if self.ssh_debug_console and log_fh is not None:
                    tee_writer = Tee(sys.stdout, log_fh)
                    spawn_log_target = tee_writer
                elif self.ssh_debug_console and log_fh is None:
                    spawn_log_target = sys.stdout
                elif log_fh is not None:
                    spawn_log_target = log_fh
                else:
                    spawn_log_target = None

                # Clear known_hosts for target before spawning (again, safe)
                try:
                    os.system(f"ssh-keygen -R {target_ip} >/dev/null 2>&1")
                except:
                    pass

                # Debug info
                logger.info(f"DEBUG: Attempt #{attempt_idx+1} connecting to {target_ip} (directWire={use_directwire}, withJump={use_withJump}, bypassHostKey={bypass})")
                if self.ssh_debug:
                    logger.info(f"DEBUG: SSH command: {cmd}")
                    logger.info(f"DEBUG: SSH logfile: {logfile_path if log_fh else '<none>'}")
                    logger.info(f"DEBUG: SSH console streaming: {self.ssh_debug_console}")

                # Smart Expect spawn function for this attempt
                def ExpectSpawn(cmd_local):
                    child = pexpect.spawn(cmd_local, timeout=120, encoding="utf-8", codec_errors="replace")
                    if spawn_log_target is not None:
                        # pexpect expects a file-like object; Tee implements write/flush
                        child.logfile = spawn_log_target

                    logger.info(f"DEBUG: Spawned PID={child.pid} for {target_ip}")

                    # initial small sleep to capture banners
                    time.sleep(0.2)
                    if child.before:
                        logger.info("DEBUG: Initial output:\n" + (child.before or ""))

                    # Patterns: 0=password prompt, 1=END, 2=EOF, 3=TIMEOUT
                    patterns = [r"password:", keyWord, pexpect.EOF, pexpect.TIMEOUT]

                    try:
                        i = child.expect(patterns, timeout=10)
                    except Exception as e:
                        # no match within timeout
                        logger.error(f"DEBUG: Exception waiting for patterns: {e}")
                        # ensure we collect what we can
                        out = child.before or ""
                        return out

                    if i == 0:
                        logger.info("DEBUG: password prompt detected; sending password.")
                        child.sendline(self.keyDecript)
                        # wait for END or EOF/TIMEOUT
                        try:
                            i2 = child.expect([keyWord, pexpect.EOF, pexpect.TIMEOUT], timeout=20)
                            if i2 == 0:
                                logger.info("DEBUG: END detected after password.")
                            elif i2 == 1:
                                logger.error("DEBUG: EOF after password.")
                            else:
                                logger.error("DEBUG: TIMEOUT after password.")
                        except Exception as e:
                            logger.error(f"DEBUG: Exception after sending password: {e}")

                    elif i == 1:
                        logger.info("DEBUG: END detected immediately (no password prompt).")
                    elif i == 2:
                        logger.error("DEBUG: EOF encountered while waiting for password/END.")
                        logger.error("DEBUG: Output before EOF:\n" + (child.before or ""))
                    else:
                        logger.error("DEBUG: TIMEOUT while waiting for password/END.")
                        logger.error("DEBUG: Output before TIMEOUT:\n" + (child.before or ""))

                    # Collect remaining output (child.before holds text up to match)
                    final_out = child.before or ""
                    # ensure logfile flushed if used
                    if log_fh is not None:
                        try:
                            log_fh.flush()
                        except:
                            pass
                    return final_out

                # Run ExpectSpawn
                result = ExpectSpawn(cmd)

                # Close logfile handle if opened
                if log_fh is not None:
                    try:
                        log_fh.close()
                    except:
                        pass

                # If it returned something, consider success
                if result is not None:
                    # Log success metadata
                    logger.info(f"DEBUG: SSH attempt #{attempt_idx+1} successful (log: {logfile_path})")
                    return result
                else:
                    # continue to next fallback
                    logger.error(f"DEBUG: SSH attempt #{attempt_idx+1} returned no output, trying next fallback.")
            except Exception as e:
                last_exception = e
                logger.error(f"DEBUG: Exception on ssh attempt #{attempt_idx+1}: {e}")
                # try next fallback
                continue

        # If we exit loop without returning, raise or return what we have
        if last_exception:
            logger.error(f"All SSH attempts failed. Last exception: {last_exception}")
            raise last_exception
        else:
            logger.error("All SSH attempts returned no output.")
            return ""  # graceful fallback

    # ----------------------------------------------------------------------
    # Remaining functions (unchanged other than possible minor logging)
    # ----------------------------------------------------------------------

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
        if self.stepPauseSec > 1:
            logger.info(f"Waiting {self.stepPauseSec} seconds for hydraulic cool down")
            time.sleep(self.stepPauseSec)

        if self.boolNeed2GetLatestFile is True:
            logger.info("Identifying latest log file")
            _, self.strRemoteLogFile = self.GetLogFileAtMachine()
            self.boolNeed2GetLatestFile = False

        return (True,)

    def GetLogFileAtMachine(self):
        strLogLocation = "/home/seegrid/Logs"
        strYear, strMonth, strDate = GetYearMonthDate()
        strLogLocationToday = f"{strLogLocation}/{strYear}/{strMonth}/{strDate}"

        logger.info("Log file location: " + strLogLocationToday)

        strFindCommand = rf'find {strLogLocationToday} -name "*servo-axis-{self.GetDefAxis()}*"'
        logger.info("Submit command for file find: \n" + strFindCommand)

        stdout: str = self.sendSSHCommand(strFindCommand)
        lstFiles = stdout.splitlines()

        strMatchPattern = "^.+/(\\d+)_(\\d+)_(\\d+)-hydraulic-control-tuner"

        listFilesAndDates = []
        for i in lstFiles:
            if re.search(strMatchPattern, i):
                hr = re.search(strMatchPattern, i).group(1)
                min = re.search(strMatchPattern, i).group(2)
                sec = re.search(strMatchPattern, i).group(3)

                strTimeStamp = f"{strYear} {strMonth} {strDate} {hr}:{min}:{sec}"
                intEpochTime = GetEpochTime(strTimeStamp, strTimeFromat="%Y %m %d %H:%M:%S")
                listFilesAndDates.append([i, intEpochTime])

        if len(listFilesAndDates) == 0:
            self.strRemoteLogFile = "noFileFound"
            return (True, "noFileFound")

        def getThird(e):
            return e[1]

        listFilesAndDates.sort(key=getThird, reverse=True)
        outFile = listFilesAndDates[0][0]
        logger.info("Found file: " + outFile)
        self.strRemoteLogFile = outFile
        return (True, outFile)

    def GetLogFileOutput(self):
        strFileName = self.strRemoteLogFile
        strCmd = rf"cat {strFileName}"

        strOut = self.sendSSHCommand(strCmd)
        strOut = CleanTextFileTimeColumn(strOut)

        logger.info("Log file output: \n {}".format(ReduceStringSize(strOut)))
        return (True, strOut)

    def GetCurrentPosition(self, strAxis):
        strCmd = "~/trunk/util/misc/print-hydraulic-positions.py -a {}".format(strAxis)
        strCmd = "timeout 2s {}".format(strCmd)
        logger.info("Getting current position for " + strAxis + ":")
        logger.info("Running command \n" + strCmd)

        stdout: str = self.sendSSHCommand(strCmd)
        lstLines = stdout.splitlines(True)

        strMatchPattern = "^{}:\\s+([-]?\\d+\\.\\d+)".format(strAxis)
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

        return (True, outMean)

    def GetLineCount(self):
        return (True, 1)
