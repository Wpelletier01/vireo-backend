
from dataclasses import dataclass
from typing import Union



@dataclass
class UserInfo:

    username:   str
    password:   str 
    fname:      str 
    mname:      Union[str,None]
    lname:      str 
    email:      str 
    birthday:   str


    def to_insert_id_query(self,id:int):
        
        return f"""
             
            INSERT INTO accountIds (
                id,
	            username,
                password
            )
            VALUES 
            ( {id},'{self.username}',"{self.password}")
        
        """

    def to_insert_info_query(self,id:int):

        middle_name = "NULL"

        if self.mname is not None:

            middle_name = f"'{self.mname}'"
        
        return f"""
            INSERT INTO accountInfo (
		        id,
	            fname,
                mname,
                lname,
                email,
                birth
            )   
            VALUES
            ({id},'{self.fname}',{middle_name},'{self.lname}','{self.email}',Date('{self.birthday}'));
        """
