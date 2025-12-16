import time

from remote_ctrl import Remote
from utils import logger, YmlManager, OutFile, PrCSV, CreateDictFromString


from utils import (
    GetMaxVelocityInst,
    GetMaxVelocity,
    GetStartOfMotionCommand,
    GetMaxVelocityError,
)

import os, sys


class Task:
    def __init__(
        self,
        remoteObj: Remote,
        intIterAmount: int,
        strTaskFileName: str,
        OutFileObj: OutFile,
        logFileLocation: str,
    ):
        """Creates Task Object

        Args:
            remoteObj (Remote): Remote object
            intIterAmount (int): Amount of iterations
            strTaskFileName (str): Task File
        """
        self.rO: Remote = remoteObj
        self.intIterAmout: int = intIterAmount
        self.strTaskFileName: str = strTaskFileName
        self.OutFile: OutFile = OutFileObj
        self.logFileLocation = logFileLocation
        self.dictTask: dict = {}
        self.__defAxis = ""
        self.STATE: dict = {}
        # self.STATE["defAxis"] = ""
        self.strWorkingPath = os.getcwd()
        self.RunTask()

    def GetDefAxis(self):
        return self.__defAxis

    def SetDefAxis(self, strAxis):
        self.__defAxis = strAxis
        self.rO.SetDefAxis(strAxis)

    def GetNumVal(self, dictObjt, strKey):
        """returns the value dictObjt specified by strKey string.
        if value is a string, we return velue in the application state defined by
        vals[strKey].  Otherwise we the value is numeric and we get it directly fron the dictObj
        object.

        Args:
            dictObjt (_type_): task object
            strKey (_type_): name ot taskObject parameter

        Returns:
            _type_: _description_
        """
        keyVal = dictObjt[strKey]
        if isinstance(keyVal, str):
            outVal = self.GetSTATE(keyVal)
        else:
            outVal = dictObjt[strKey]

        return outVal

    def GetSTATE(self, strIndexName: str):
        return self.STATE[strIndexName]

    def SetSTATE(self, strIndexName, val):
        self.STATE[strIndexName] = val
        logger.info("[STATE:{} <-- {}]".format(strIndexName, str(val)))

    def ClearSTATE(self):
        self.STATE = {}

    def GetVehicleDetailsFun(self, operation):
        self.rO.GetVehicleName()
        # SetDefAxis(operation["Axis"])

    def SetDefAxisFun(self, operation):
        # global R1
        self.SetDefAxis(operation["Axis"])

        # self.SetSTATE("defAxis", operation["Axis"])
        return True

    def GetCurrentPosFun(self, operation):
        # global R1
        bStatus, Out = self.rO.GetCurrentPosition(self.GetDefAxis())
        self.SetSTATE(operation["OutName"], Out)
        # breakpoint()
        return bStatus

    def GetLineNumberFun(self, operation):
        logger.info(
            "Getting current line number for {} servo file".format(
                self.GetDefAxis(), "start"
            )
        )

        _, lineNumber = self.rO.GetLineCount()
        self.SetSTATE(operation["OutName"], lineNumber)

    def HydCommandFun(self, operation):
        # global R1
        targetPos = self.GetNumVal(operation, "TargetPos")
        logger.info(
            "[HYD_COMMAND] axis: {} --> {}".format(self.GetDefAxis(), str(targetPos))
        )

        if "Start" in operation:
            if operation["Start"] == True:
                self.rO.RunHydrCommand(self.GetDefAxis(), targetPos, start=True)
            else:
                self.rO.RunHydrCommand(self.GetDefAxis(), targetPos)
        else:
            self.rO.RunHydrCommand(self.GetDefAxis(), targetPos)

        # breakpoint()

    def OutputResultFun(self, operation):
        # breakpoint()
        try:
            OutVal = self.GetSTATE(operation["Input"])
        except:
            breakpoint()
        TaskFile = os.path.basename(self.strTaskFileName)
        # COUNT = str(self.GetSTATE("RepeatCounter"))

        if self.GetDefAxis() == "tilt":
            valStr = "{:.5f}".format(OutVal)

        else:
            valStr = "{:.2f}".format(OutVal)

        self.OutFile.Oprint(TaskFile, operation["Output"], valStr)

    def MathOperationFun(self, Operation):

        Input1 = self.GetNumVal(Operation, "Input1")
        Input2 = self.GetNumVal(Operation, "Input2")
        Out = eval("Input1 {} Input2".format(Operation["Operation"]))
        self.SetSTATE(Operation["Output"], Out)

    def OutputLogFileFun(self, Operation):
        # Creating log file for servo file based on start and end line numbers
        logger.info("Writing Results CSV file for {}".format(Operation["Name"]))
        # StartLineNumber = self.GetNumVal(Operation, "StartLineNumber")
        # EndLineNumber = self.GetNumVal(Operation, "EndLineNumber")
        # logger.info(
        #     "Will read from line {} to line {}".format(StartLineNumber, EndLineNumber)
        # )
        
        time.sleep(1)
        _, lastFile = self.rO.GetLogFileAtMachine()
        
            
            
        logger.info("Will read from {}".format(lastFile))

        _, strOut = self.rO.GetLogFileOutput()

        # self.L1.log("strOut", type="process")

        intCountr = 0
        while True:
            logFileName = Operation["Name"].replace("[COUNTER]", str(intCountr))

            if (
                os.path.exists(os.path.join(self.strWorkingPath, self.logFileLocation))
                == False
            ):
                os.makedirs(os.path.join(self.strWorkingPath, self.logFileLocation))

            logFileNameFullPath = (
                os.path.join(self.strWorkingPath, self.logFileLocation, logFileName)
                + ".csv"
            )
            if os.path.exists(logFileNameFullPath) == False:
                break
            else:
                intCountr = intCountr + 1
            if intCountr > 100:
                logger.critical(
                    "FOUND MORE THAN 100 {} files!!!".format(logFileNameFullPath)
                )
                sys.exit(1)

        with open(logFileNameFullPath, "w") as f:
            f.write(strOut)

            logger.info("Output written to {}".format(strOut))

    def TaskFunction(self, operation, Func) -> bool:

        logger.info("Starting Task: {}".format(operation["Type"]))
        return Func(operation)

    def MultiProcessLogFilesFun(self, task):
        # nonlocal iteration
        # global R1

        PostPCounter = 0
        LogFileNameExists = True

        while LogFileNameExists == True:
            # breakpoint()
            logFileName = task["LogName"].replace("[COUNTER]", str(PostPCounter))
            logFileNameFullPath = (
                os.path.join(self.strWorkingPath, self.logFileLocation, logFileName)
                + ".csv"
            )

            if os.path.exists(logFileNameFullPath):

                for LogTask in task["ProcessFunctions"]:
                    FunName = LogTask["Name"]
                    logger.info(
                        "Will apply {} to the following file: \n {}".format(
                            FunName, logFileNameFullPath
                        )
                    )
                    
                    CSVObj = PrCSV(logFileNameFullPath)

                    ArgObj = CreateDictFromString(LogTask["Args"])

                    # aa = globals()[FunName](CSVObj)
                    EvalString = "{}(CSVObj, ArgObj)".format(FunName)

                    try:
                        aa = eval(EvalString)
                    except:
                        breakpoint()
                    Label = LogTask["Label"]
                    TaskFile = os.path.basename(self.strTaskFileName)
                    COUNT = str(PostPCounter)
                    for key in aa:
                        OutName = key
                        OutVal = aa[key]
                        strLogFile = "[TASK: {TaskFileName}][NAME: {LabelName}_{OutName}][COUNT: {Count}][VAL:{val}]".format(
                            TaskFileName=TaskFile,
                            LabelName=Label,
                            OutName=OutName,
                            Count=str(PostPCounter),
                            val=str(OutVal),
                        )
                        logger.info(strLogFile)
                        self.OutFile.Oprint(
                            TaskFile,
                            "{}_{}_{}".format(Label, OutName, str(PostPCounter)),
                            str(OutVal),
                            usePostOut=True,
                        )

                PostPCounter = PostPCounter + 1
            else:
                LogFileNameExists = False

    def RunTask(self):
        logger.info("Running task {}".format(os.path.basename(self.strTaskFileName)))

        myYml = YmlManager(self.strTaskFileName)
        self.dictTask = myYml.Convert2Dictionary()

        logger.info(
            "Will run task {} for {} times".format(
                os.path.basename(self.strTaskFileName), str(self.intIterAmout)
            )
        )
        # for i in range(self.intIterAmout):
        self.ClearSTATE()
        if "Operations" in self.dictTask:
            for operation in self.dictTask["Operations"]:

                if operation["Type"] == "SetDefAxis":
                    self.TaskFunction(operation, self.SetDefAxisFun)
                elif operation["Type"] == "GetVehicleDetails":
                    self.TaskFunction(operation, self.GetVehicleDetailsFun)
                elif operation["Type"] == "GetCurrentPos":
                    self.TaskFunction(operation, self.GetCurrentPosFun)

                elif operation["Type"] == "GetLineNumber":
                    self.TaskFunction(operation, self.GetLineNumberFun)

                elif operation["Type"] == "HydCommand":
                    self.TaskFunction(operation, self.HydCommandFun)

                elif operation["Type"] == "OutputResult":
                    self.TaskFunction(operation, self.OutputResultFun)

                elif operation["Type"] == "ModVal":
                    self.TaskFunction(operation, self.ModValFun)

                elif operation["Type"] == "MathOperation":
                    self.TaskFunction(operation, self.MathOperationFun)

                elif operation["Type"] == "OutputLogFile":
                    self.TaskFunction(operation, self.OutputLogFileFun)

                else:
                    logger.critical(
                        "========{} not found =====".format(operation["Type"])
                    )
        if "PostOperations" in self.dictTask:
            if "PostOperations" in self.dictTask:
                for operation in self.dictTask["PostOperations"]:

                    if operation["Type"] == "MultiProcessLogFiles":
                        self.TaskFunction(operation, self.MultiProcessLogFilesFun)

                    elif operation["Type"] == "OutProcess":
                        self.TaskFunction(operation, self.OutProcessFun)

                    else:
                        logger.critical(
                            "========{} not found =====".format(operation["Type"])
                        )
