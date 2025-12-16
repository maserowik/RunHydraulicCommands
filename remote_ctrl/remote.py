from abc import ABC, abstractmethod


class Remote(ABC):

    # @abstractmethod
    # def GetLogFile(self) -> tuple[bool, str]:
    #     """Returns value of log file"""

    @abstractmethod
    def GetDefAxis(self) -> str:
        pass

    @abstractmethod
    def SetDefAxis(self, strAxis):
        pass

    @abstractmethod
    def GetLogFileAtMachine(self) -> tuple[bool, str]:
        """Identify log file at machine with pertinant CSV data

        Returns:
            str: absolute path of log file at machine
        """
        pass

    @abstractmethod
    def GetVehicleName(self) -> str:
        pass

    @abstractmethod
    def GetCurrentPosition(self, strAxis: str) -> tuple[bool, float]:
        """Gets current axis position"""
        pass

    @abstractmethod
    def GetLineCount(self) -> tuple[bool, int]:
        """Get number of rows at log file
        note:  remeber to get last modified file.

        Args:
            strFile (str): global path in at target server (mostlikely VGU)
        """
        pass

    @abstractmethod
    def RunHydrCommand(
        self, strAxis: str, tgPosition: float, start: bool
    ) -> tuple[bool]:
        """Run hydraulic command"""
        pass

    @abstractmethod
    def GetLogFileOutput(self, intStartRow: int, intEndRow: int) -> tuple[bool, str]:
        """Gets output of log file that is pertinant to CSV output

        Args:
            intStartRow (int): start row
            intEndRow (int): end row

        Returns:
            str: output csv as string
        """
        pass
