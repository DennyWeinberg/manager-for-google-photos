from os.path import join
from shutil import copy, move

from google_photos_manager.backup.helper import files_helper


class AlbumHandler:
    def __init__(self, mode, out_path):
        self.mode = mode
        self.out_path = out_path

    def handle(self, path, infos):
        getattr(self, f'_{self.mode.lower()}')(path, infos)

    def _copy(self, path, infos):
        for album in infos['albums']:
            album_path = join(self.out_path, album)
            files_helper.cru_out_path(album_path)
            copy(path, join(album_path, infos['name']))

    def _move(self, path, infos):
        for idx, album in enumerate(infos['albums']):
            album_path = join(self.out_path, album)
            files_helper.cru_out_path(album_path)
            if idx == 0:
                move(path, join(album_path, infos['name']))
                path = join(album_path, infos['name'])
            else:
                copy(path, join(album_path, infos['name']))
