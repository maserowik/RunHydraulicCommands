import yaml
import os
import sys
import pprint

from utils import logger


class YmlManager:
    def __init__(self, strFileYml):
        self.strFile: str = strFileYml
        """local task runner file
        """

    def CheckIfExists(self) -> bool:
        """check if local task file exists"""
        if os.path.exists(self.strFile):
            return True
        else:
            return False

    def Convert2Dictionary(self) -> dict:
        if self.CheckIfExists() == False:
            logger.critical("{} does not exist".format(self.strFile))
            sys.exit(1)
        with open(self.strFile) as file:
            try:
                dictYml = yaml.safe_load(file)
            except yaml.YAMLError as exc:
                if hasattr(exc, "problem_mark"):
                    mark = exc.problem_mark
                    logger.critical(
                        "Error position: (%s:%s)" % (mark.line + 1, mark.column + 1)
                    )
                    sys.exit(1)

        logger.debug("\n{}".format(pprint.pformat(dictYml)))
        return dictYml
