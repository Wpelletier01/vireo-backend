# vireo-backend


## Description
This project is a robust back-end server service
designed to handle API requests for a video sharing and social media website.
The service is implemented in Python using the popular micro web framework call Flask.

The primary responsibilities of the server service include:
- Ensuring that the incoming requests are correctly formed and adhering to the required specifications.
- Executing queries on the MariaDB database to retrieve relevant information about users or videos.
- Facilitating the seamless transmission of video or image files stored locally.
- Implementing secure processing of JWT tokens for authentication and authorization purposes.
- Plus, various other essential tasks to ensure smooth operation.



### How it works
TODO: Finish it

The database stores metadata on the user and videos.
The video file and his thumbnails, and user profile picture 
is stored locally on the machine that runs the service in a common folder.
The server query info on the database and send the information back to the requester.
When the requester wants a file like a video, he goes grab it in the common directory. 
The thumbnails and the video file are named with their hash path that has been generated when uploaded.
For now, the user can't choose a thumbnails.
The server selected a random frame in the video and created an image
with it that served has thumbnails.


### Motivation
The motivation behind undertaking this project was to gain a deeper understanding of the functionality,
purpose, and significance of back-end servers.
By developing a server from scratch, I aimed to explore the intricacies involved in building a robust back-end system.
Flask was chosen as the framework of choice due to its minimalist approach,
allowing me to focus on essential aspects and gain comprehensive knowledge in server development.

## Installation

TODO

## Api Call 

All the api calls return a body with the key "response" Either empty or with data,
except for sending file like a video or an image. 

the universal return value when request info on channels or videos is formed like this:

    "type": "either video or channel", 
    "channel": "channel username",
    "title": "the title",
    "thumbnail": "the hashed path of a video",
    "nb_count": "count of videos a channel have",
    "description": "description of a video",
    "upload": "the date of upload"
note that some keys can return empty depending on the type of request e.g., when ask for info on a video, the key 
nb_count since it is reserved for request on channel info.
I might add more in the future

### POST <u>/sign_in </u>
parameter: 
- username: string
- password: string

return:
- 200 -> Jwt token generated with the parameter passed as payload that expires in 3 hours
- 400 -> missing field in the body
- 402 -> either the username or password is wrong (number of attempts left before being blocked)
- 403 -> blocked for too many attempts (with the time left before unblock)

_*Note that some functionality of the login manager has not been tested_

### POST <u>/sign_up</u>
parameter:
- fname (first name) : string
- mname (Middle name, it can be empty) : string
- lname (last name) : string
- username : string
- email : string 
- password : string 
- day  (birth) : int
- month (birth) : int 
- year (birth): int 

return:
- 200 if creation succeeds
- 400 
    - Missing field in the body
    - A channel with the username pass already exists
    - A channel with the email pass already exists
  
_*Note that the verification of the input should be made on the client side for now_


### POST <u>/upload</u>
*require token

upload info on a video to the database

parameter:
- title
- description
return:
- 200 -> a hash path of the video
- 400
    - missing field in the body
    - no token in the header
    - somehow the payload of the token has been altered
- 401 -> if token expire


### POST <u>/upload/v/</u>*hashpath*
upload a video with a hashed path as id from the url

parameter:
- hashed path in the url
- a raw data video

return:
- 200 -> empty
- 400
    - no token in the header
    - somehow the payload of the token has been altered
- 401 -> if token expire

_*Note that it has been only tested for mp4 format file for now_
_*Also not tested when no data is passed

### GET <u>/v/</u>*hashpath*
retrieve info of a specific video

parameter:
- the hash path in the url

return:
- 200 -> A universal return body
- 404 -> The hash path doesn't exist 

### GET <u>/video/d/</u>*hashpath*
get a video file

parameter:
- The hash path in the url

return:
- 200 -> the video
- 400 -> if no video exists with the hash path passed

### GET <u>/videos/all</u> or <u>/videos/channel/</u>*channel_name*
Return all the video we have or all the video of a specific channel

parameter:
- The channel name if not all videos

return:
- 200 -> List of universal return body
- 404 -> if channel dont exist

### GET <u>/thumbnails/</u>*hashpath*
Return the thumbnails of a specific video

parameter:
- The hash path in the url

return:
- 200 -> The image
- 404 -> if video doesn't exist

### GET <u>/search/</u>*stype*/*squery*
perform a query in the database either by channel name or video name

parameter:
- search type in the url, either all or channel
- the query in the url

return: 
- 200 -> List of universal return body
- 400 -> Bad search type


### GET <u>/channel/picture/</u>*channel_name*
return the profile picture of the channel

parameter:
- channel name in the url

return:
- 200 -> An image file
- 404 -> No Channel found

_*Note that it's not stable for now._


## Database 

The database is created with Mariadb. For the moment, it contains 3 tables:

### Channels table
it stores basic login information.

| ChannelID   | Username    | Password    |
|-------------|-------------|-------------|
| Primary Key | Varchar(25) | Varchar(60) |

- the password is stored has a hashed password with the function bcrypt.

### ChannelDetails
it stores relevant user information

| ChannelID | Fname | Mname | Lname | Email      | Birth |
| ----------|-------|-------|-------|------------|-------|
| ForeignKey | varchar(25) | varchar(25) | varchar(25) | PrimaryKey | date |

- The primary key is email because we want them to be unique

### Videos
it stores information about a video uploaded by a user

| VideoID | PathHash | ChannelID | Title   | Description | Upload   | Like  | Dislike |
|---------|----------|-----------|---------|-------------|----------|-------|---------|
| Primary Key | varchar(7) | Foreign Key | varchar(255) | mediumtext | int(12) | int(12) |

- PathHash is a random string generated by the server to help identified a video (like Youtube).
-  ChannelId identify his uploader





## TODO

- [ ] validate the input parameter before creating an account
  - [ ] validate that the birthday date is valid when creating
  - [ ] other ..
- [ ] Api call for deleting video
- [ ] Api call for deleting channel 
    
- [ ] sending email
  - [ ] forgot password
  - [ ] notification