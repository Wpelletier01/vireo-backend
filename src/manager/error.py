from enum import Enum



class SignInErrType(Enum):

    BadUtype            = 1
    MissingField        = 2
    EmailNotFound       = 3
    UsernameNotFound    = 4
    WrongPassword       = 5
    TokenExpire         = 6

class SignInError(Exception):

    def __init__(self,etype:SignInErrType,opt_arg=None):

        self.etype = etype
        self.msg = ""

        match self.etype:
            case SignInErrType.BadUtype:
                self.msg = "invalid 'utype' value"
            case SignInErrType.MissingField:
                self.msg = f"sign in request is missing a field: '{opt_arg}'"
            case SignInErrType.EmailNotFound:
                self.msg = "email not found"
            case SignInErrType.UsernameNotFound:
                self.msg = "username not found"
            case SignInErrType.WrongPassword:
                self.msg = "wrong password"
            case SignInErrType.TokenExpire:
                self.msg = "token expire"

            
    def __str__(self):
        return self.msg




class SignUpErrType(Enum):

    MissingField    = 1
    UsernameExist   = 2
    EmailExist      = 3


class SignUpError(Exception):

    def __init__(self,etype:SignUpErrType,opt_arg=None):
        
        self.etype = etype
        self.msg = ""

        match self.etype:

            case SignUpErrType.UsernameExist:
                self.msg = "Username already exist"
            
            case SignUpErrType.EmailExist:
                self.msg = "Email already use by another account"

            case SignUpErrType.MissingField:
                self.msg = f"sign in request is missing a field: '{opt_arg}'"   

        super().__init__("Invalid Json body")

    def __str_(self):
        return self.msg 



class UploadErrType(Enum):

    BufferIndex     = 1
    MissingField    = 2

class UploadErr(Exception):
    def __init__(self,etype:UploadErrType,option=None):
        
        self.msg = ""
        self.etype = etype
        match etype:

            case UploadErrType.BufferIndex:
                self.msg = "No video at the current index in the buffer"
            case UploadErrType.MissingField:
                self.msg = f"Missing key for json request: {option}"


    def __str__(self):
        return self.msg




########################
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
