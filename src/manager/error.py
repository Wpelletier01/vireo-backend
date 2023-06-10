from enum import Enum
import werkzeug.exceptions as ex

class ErrorType(Enum):
    DbConnection =      1
    DbExecution =       2
    DbInsertion =       3
    DbNotConnected =    4


class VireoError(Exception):

    def __init__(self, etype: ErrorType, arg: str | None = None):
        self._etype = etype
        self._msg = ""

        match etype:

            case ErrorType.DbConnection:
                self._msg = f"Database Connection: {arg}"

            case ErrorType.DbExecution:
                self._msg = f"Database execution: {arg}"

            case ErrorType.DbInsertion:
                self._msg = f"Database data insertion: {arg}"

            case ErrorType.DbNotConnected:
                self._msg = f"Try to interact with database but not connected"

    def __str__(self):
        return self._msg



