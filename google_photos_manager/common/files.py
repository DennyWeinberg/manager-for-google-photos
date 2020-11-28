from os import makedirs
from os.path import exists


def cru_out_path(downloads_path):
    if not exists(downloads_path):
        makedirs(downloads_path)
