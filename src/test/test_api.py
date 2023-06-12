import requests
import os
from requests.adapters import HTTPAdapter

API_ROOT = "http://127.0.0.1:8900"

# ================================================================================================ #
#                                                                                                  #
#                                           SIGN IN Request                                        #
#                                                                                                  #
# ================================================================================================ #
SIGN_IN = f"{API_ROOT}/signin"


def signin():
    data = {
        "username": "wpelletier",
        "password": "1234"
    }

    r = requests.post(SIGN_IN, json=data)

    return r.json()['response']['vtoken']


def test_valid_si_req():
    data = {
        "username": "wpelletier",
        "password": "1234"
    }

    r = requests.post(url=SIGN_IN, json=data)
    b = r.json()

    assert 'vtoken' in b['response'].keys()


def test_invalid_si_content_type():
    header = {
        "Content-Type": "application/xml"
    }
    data = {
        "username": "wpelletier",
        "password": "1234"
    }

    r = requests.post(url=SIGN_IN, json=data, headers=header)

    if r.status_code == 400:
        assert True
    else:
        assert False


def test_max_request_attempt():
    data = {
        "username": "wpelsfsdletier",
        "password": "1234"
    }

    for i in range(7):
        r = requests.post(url=SIGN_IN, json=data)

    if r.status_code == 403:
        assert True
    else:
        assert False


def test_malformed_request():
    data = {
        "usesdarname": "wpelletier",
        "password": "1234"
    }

    end_point = os.path.join(API_ROOT, "signin")

    r = requests.post(end_point, json=data)

    if r.status_code == 400:
        assert True
    else:
        assert False


# ================================================================================================ #
#                                                                                                  #
#                                           SIGN UP Request                                        #
#                                                                                                  #
# ================================================================================================ #
SIGNUP = os.path.join(API_ROOT, "signup")


def test_malformed_sign_up():
    data = {
        "fname": "Fsdf",
        "mname": "dsf",
        "lname": "sfd",
        "username": "atest123",
        "monsth": 10,
        "day": 23,
        "year": 1999,
        "email": "atest123@gmail.com",
        "password": "12sdadfgd"
    }

    r = requests.post(SIGNUP, json=data)

    if r.status_code == 400:
        assert True
    else:
        assert False


def test_good_su_request():
    data = {
        "fname": "Fsdf",
        "mname": "dsf",
        "lname": "sfd",
        "username": "atest123",
        "month": 10,
        "day": 23,
        "year": 1999,
        "email": "atest123@gmail.com",
        "password": "12sdadfgd"
    }

    r = requests.post(SIGNUP, json=data)

    if r.status_code == 200:
        assert True
    else:
        assert False


def test_username_already_exist():
    data = {
        "fname": "Fsdf",
        "mname": "dsf",
        "lname": "sfd",
        "username": "wpelletier",
        "month": 10,
        "day": 23,
        "year": 1999,
        "email": "atest123@gmail.com",
        "password": "12sdadfgd"
    }

    r = requests.post(SIGNUP, json=data)

    if r.status_code == 400:
        assert True
    else:
        assert False


def test_email_already_exist():
    data = {
        "fname": "Fsdf",
        "mname": "dsf",
        "lname": "sfd",
        "username": "dsfsads",
        "month": 10,
        "day": 23,
        "year": 1999,
        "email": "wpelletier.development@yahoo.com",
        "password": "12sdadfgd"
    }

    r = requests.post(SIGNUP, json=data)

    if r.status_code == 400:
        assert True
    else:
        assert False


# ================================================================================================ #
#                                                                                                  #
#                                           Upload info Request                                    #
#                                                                                                  #
# ================================================================================================ #
UPLOAD_INFO = f"{API_ROOT}/upload"


def test_no_token_upload():
    data = {
        "title": "a test",
        "description": "a request test"

    }

    r = requests.post(UPLOAD_INFO, json=data)

    if r.status_code == 400:
        assert True
    else:
        assert False


def test_missing_field_upload():
    t = signin()

    header = {'Authorization': t}

    data = {
        "title": "dadaasa",
        "desgdsg": "Fdsfsddf"
    }

    r = requests.post(UPLOAD_INFO, json=data, headers=header)

    if r.status_code == 400:
        assert True
    else:
        assert False


def test_valid_upload_info():
    t = signin()

    header = {'Authorization': t}

    data = {
        "title": "dadaasa",
        "description": "Fdsfsddf"
    }

    r = requests.post(UPLOAD_INFO, json=data, headers=header)

    if r.status_code == 200:
        assert True
    else:
        assert False


# ================================================================================================ #
#                                                                                                  #
#                                           Retrieve query Request                                 #
#                                                                                                  #
# ================================================================================================ #
RETRIEVE_INFO_ALL = f"{API_ROOT}/videos/all"
RETRIEVE_INFO_CHANNEL = f"{API_ROOT}/videos/channel"


def test_retrieve_all():
    r = requests.get(RETRIEVE_INFO_ALL)

    if r.status_code == 200:
        assert True
    else:
        assert False


def test_retrieve_bad_channel():
    r = requests.get(f"{RETRIEVE_INFO_CHANNEL}/sadfsaf")

    if r.status_code == 400:
        assert True

    else:
        assert False


def test_good_channel():
    r = requests.get(f"{RETRIEVE_INFO_CHANNEL}/wpelletier")

    if r.status_code == 200:
        assert True

    else:
        assert False


# ================================================================================================ #
#                                                                                                  #
#                                           Search query Request                                   #
#                                                                                                  #
# ================================================================================================ #
SEARCH_ALL = f"{API_ROOT}/search/all/film"
SEARCH_CHANNEL = f"{API_ROOT}/search/channel/film"
SEARCH_BAD = f"{API_ROOT}/search/dsfds/film"


def test_bad_search():
    r = requests.get(SEARCH_BAD)

    if r.status_code == 400:
        assert True
    else:
        assert False


def test_search_all():
    r = requests.get(SEARCH_ALL)

    if r.status_code == 200:
        assert True
    else:
        assert False



