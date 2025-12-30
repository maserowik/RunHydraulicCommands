from .remote import Remote
from utils import logger


class RemoteTest(Remote):
    def __init__(self):
        self.logFile = ""

    # def GetLogFile(self):
    #     return (True, self.logFile)

    def GetLogFileAtMachine(self):

        return (True, "some_file")

    def GetLineCount(self):

        return (True, 1)

    def RunHydrCommand(self, strAxis, tgPosition, start=False):
        return (True,)

    def GetCurrentPosition(self, strAxis):
        return (True, 3.3)

    def GetLogFileOutput(self, intStartRow, intEndRow):
        strMsg = "asdfasdfasdf"
        return (True, strMsg)

    def GetDefAxis(self) -> str:
        return "lift"

    def SetDefAxis(self, strAxis):
        pass
