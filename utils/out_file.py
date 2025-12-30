import time
import os
from utils import logger


class OutFile:
    def __init__(self, strOutFile, strPostOutFIle):
        self.outputFile = strOutFile
        self.postOutputFile = strPostOutFIle
        self.postOutCalled = False

    def GetTaskCount(self, strTaskName):

        if os.path.exists(self.outputFile) == False:
            # breakpoint()
            return 0

        with open(self.outputFile, "r") as file:
            count = 0
            for line in file:
                if "[TASK: {}]".format(strTaskName) in line:
                    count = count + 1

        return count

    def Oprint(
        self, strTaskFileName: str, strOutName: str, strVal: str, usePostOut=False
    ):
        """Write's message to out file"""
        strMsg = "[TASK: {TaskFileName}][NAME: {OutName}][VAL:{val} ]".format(
            TaskFileName=strTaskFileName,
            OutName=strOutName,
            val=strVal,
        )

        epochTime = "[{:.3f}]".format(time.time())
        # CurrentDateTime = datetime.datetime.now()
        TimeStamp = "{}  ".format(epochTime)
        if usePostOut == False:
            with open(self.outputFile, "a") as file:
                logger.info("writing out msg: {}".format(strMsg))
                file.write(TimeStamp + strMsg)
                file.write("\n")
        else:
            if self.postOutCalled == False:
                # clear post_out file
                logger.info("Clearing contents of post_out.txt file")
                with open(self.postOutputFile, "w") as file:
                    file.write("")

                # copy contents of outfile to post_out.file
                logger.info("Copying contents of out.txt file to post_out.txt file")
                with open(self.outputFile, "r") as outFile, open(
                    self.postOutputFile, "a"
                ) as postOutFile:
                    for line in outFile:
                        postOutFile.write(line)

                self.postOutCalled = True

            with open(self.postOutputFile, "a") as file:
                logger.info("writing out msg: {}".format(strMsg))
                file.write(TimeStamp + strMsg)
                file.write("\n")
