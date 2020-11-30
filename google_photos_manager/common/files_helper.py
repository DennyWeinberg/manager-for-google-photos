from os import makedirs
from os.path import exists


def cru_out_path(out_path):
    if not exists(out_path):
        makedirs(out_path)
