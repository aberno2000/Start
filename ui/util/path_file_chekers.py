from os.path import exists, isfile


def is_file_valid(path: str):
    if not exists(path) or not isfile(path) or not path:
        return False
    return True


def is_path_accessable(path):
    try:
        with open(path) as _:
            pass
        return True
    except IOError as _:
        return False
