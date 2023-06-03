
from ..database.client import DbClient,InsertAccountErrorType,InsertAccountErr
from ..database import container



def test_username_exist():

    info = container.UserInfo("durometer","1234", "reasd", None, "dsfs", "gvbfgbn@outlook.com", "2005-03-12")

    try:

        clt = DbClient() 
        clt.initiate_connection(True)
        clt.insertNewAccount(info)

        assert False

    except InsertAccountErr as e:

        if e.error_type is InsertAccountErrorType.UsernameAlreadyUsed:
 
            assert True 
        else:

            assert False

    

def test_email_exist():

    info =  container.UserInfo("test","1234", "reasd", None, "dsfs", "kcorcoran@outlook.com", "2005-03-12")


    try:

        clt = DbClient() 
        clt.initiate_connection(True)
        clt.insertNewAccount(info)

        assert False

    except InsertAccountErr as e:

        if e.error_type is InsertAccountErrorType.EmailAlreadyUsed:
 
            assert True 
        else:

            assert False

    



