from os import makedirs
from os.path import exists, join
from shutil import copy

from google_photos_manager.common import files


class AlbumHandler:
    def __init__(self, mode, downloads_path):
        self.mode = mode
        self.downloads_path = downloads_path

    def handle(self, path, infos):
        getattr(self, f'_{self.mode.lower()}')(path, infos)

    def _copy(self, path, infos):
        for album in infos['albums']:
            album_path = join(self.downloads_path, album)
            files.cru_out_path(album_path)
            copy(path, join(album_path, infos['name']))
