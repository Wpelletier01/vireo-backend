from configparser import ConfigParser

_SECTIONS = {
    "DATABASE": [
        "address",
        "port",
        "username",
        "password",
        "name"
    ],
    "TOKEN": [
        "secret",
        "algorithm"
    ],

    "GENERAL": [
        "development"
    ],

    "DEVELOPMENT": [
        "db-dir"
    ],

    "PRODUCTION": [
        "db-dir"
    ]
}


def validate_config_file(config: ConfigParser):

    for section in _SECTIONS.keys():

        try:
            _ = config[section]

        except KeyError:
            raise Exception(f"Config file: missing section {section}")

        for parm in _SECTIONS[section]:

            if parm not in config[section].keys():
                raise Exception(f"Config file: missing parameter {parm} in section {section}")

