from enum import Enum



class SignInErrType(Enum):

    BadUtype            = 1
    MissingField        = 2
    EmailNotFound       = 3
    UsernameNotFound    = 4
    WrongPassword       = 5 

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
