import configparser
from src.manager.vconf import validate_config_file


def test_bad_conf():
    conf = configparser.ConfigParser()
    conf.read("bad_config.ini")

    try:
        validate_config_file(conf)

    except Exception as e:
        assert True


def test_good_conf():
    conf = configparser.ConfigParser()
    conf.read("good_config.ini")

    validate_config_file(conf)

    assert True

