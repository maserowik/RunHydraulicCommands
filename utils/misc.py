from datetime import date

from icecream import ic
import time
import datetime
from .log import logger


def GetYearMonthDate() -> tuple[str, str, str]:
    """Returns year, month and date in string,
    ex: ('2024', '12', '10')
    """
    strYear = date.today().strftime("%Y")
    strMonth = date.today().strftime("%m")
    strDate = date.today().strftime("%d")

    logger.debug(ic.format(strYear, strMonth, strDate))
    return strYear, strMonth, strDate


def GetEpochTime(strTime, strTimeFromat="%a %b %d %H:%M:%S.%f %Y"):

    return time.mktime(datetime.datetime.strptime(strTime, strTimeFromat).timetuple())


def flt2str(val, dec=2):
    if dec == 0:
        return "{:.0f}".format(val)
    elif dec == 1:
        return "{:.1f}".format(val)
    elif dec == 2:
        return "{:.2f}".format(val)
    elif dec == 3:
        return "{:.3f}".format(val)
    elif dec == 4:
        return "{:.4f}".format(val)
    elif dec == 5:
        return "{:.6f}".format(val)
    elif dec == 6:
        return "{:.6f}".format(val)


def ReduceStringSize(strRaw: str, maxRows=50):
    lstLines = strRaw.splitlines()
    intSizeLines = len(lstLines)

    if intSizeLines > maxRows:
        TopHalf = lstLines[: int(maxRows / 2)]
        BottomHalf = lstLines[-int(maxRows / 2) :]
        resList = TopHalf + ["..........", "..........", ".........."] + BottomHalf
        resStr = "\n".join(resList)
        return resStr

    return strRaw


def CreateDictFromString(strInput: str) -> dict:
    """Returns a dictionary object from a string such as:
    "Arg1: 10, Arg2: 20"
    """
    dictObject = {}
    strList = strInput.split(",")
    for item in strList:
        keyANDval = item.split()
        if "." in keyANDval[1]:
            val = float(keyANDval[1])
        else:
            val = int(keyANDval[1])

        keyName = keyANDval[0]
        keyName = keyName.replace(":", "")
        dictObject[keyName] = val

    return dictObject
