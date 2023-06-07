
from dataclasses import dataclass
from typing import Union



@dataclass
class Channel:
    cid:        int 
    username:   str
    password:   str
    fname:      str 
    mname:      Union[str,None]
    lname:      str 
    email:      str 
    birthday:   str


    def insert_to_channels(self):
        
        return f"""
            INSERT INTO Channels (
                ChannelID,
	            Username,
                Password
            )
            VALUES 
            ( '{self.cid}','{self.username}','{self.password}')
        """

    def insert_to_channeslDetails(self):

        middle_name = "NULL"

        if self.mname is not None:

            middle_name = f"'{self.mname}'"
        
        return f"""
            INSERT INTO ChannelDetails (
                ChannelId,
	            Fname,
                Mname,
                Lname,
                Email,
                Birth
            )   
            VALUES
            (
                {self.cid},
                '{self.fname}',
                {middle_name},
                '{self.lname}',
                '{self.email}',
                Date('{self.birthday}')
            );
        """


