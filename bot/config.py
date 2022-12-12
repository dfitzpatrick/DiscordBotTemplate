from typing import Tuple
import os


class MissingConfigurationException(Exception):
    pass


def assert_envs_exist(envs: Tuple[Tuple[str, str, type]]):

    for e in envs:
        ident = f"{e[0]}/{e[1]}"
        value = os.environ.get(e[0])
        if value is None:
            raise MissingConfigurationException(f"{ident} needs to be- defined")
        try:
            _ = e[2](value)
        except ValueError:
            raise MissingConfigurationException(f"{ident} is not the required type of {e[2]}")