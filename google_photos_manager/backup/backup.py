import re
from copy import deepcopy
from decimal import Decimal
from glob import glob
from os.path import join, splitext
from time import sleep

import piexif
from PIL import Image
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys

import sys
sys.path.insert(0, '/Users/dennyweinberg/git-clones/manager-for-google-photos')

from google_photos_manager.backup.album_handler import AlbumHandler
from google_photos_manager.backup.helper import latlng_helper, session_helper, piexif_helper, selenium_helper,  files_helper


class Backup:
    def __init__(self, config):
        self.config = config
        self.album_handler = AlbumHandler(config.ALBUM_HANDLER_MODE, config.OUT_PATH)

        files_helper.cru_out_path(config.OUT_PATH)

        with selenium_helper.driver_context(config.DRIVER, config.OUT_PATH, profile_path=config.PROFILE_PATH) as self.driver:
            self.do_backup()

    def _go_to_start(self):
        page_to_restore = session_helper.restore_session_url(self.config.OUT_PATH)
        self.driver.get(page_to_restore or self.config.START)
        return page_to_restore

    def _assert_logged_in(self):
        if '/about/' in self.driver.current_url:
            input(f'Please login and hit enter:')

    def _select_first_media(self):
        self.driver.find_element_by_xpath('//body').send_keys(Keys.ARROW_RIGHT)
        sleep(0.1)
        self.driver.switch_to.active_element.send_keys(Keys.ENTER)
        sleep(1)

    def _ask_to_select_media(self):
        input('Please select your start media and hit enter:')

    def _open_info_window_if_needed(self):
        try:
            self.__get_information_panel()
        except NoSuchElementException:
            self.driver.find_element_by_xpath('//body').send_keys('i')

    def _download_media_if_needed(self, infos):
        expected_path = join(config.OUT_PATH, infos['name'])

        expected_path = expected_path.replace('~', '_')  # Downloaded file variation

        pattern = f'{splitext(expected_path)[0]}.*[!crdownload][!part]'  # Because the file name can end with .jpg, but the file is a .png

        files = list(glob(pattern))
        if not files:
            self.driver.find_element_by_xpath('//body').send_keys(Keys.SHIFT, 'd')

            i = -1
            while True:
                i += 1

                # Wait
                sleep(0.2)

                files = list(glob(pattern))
                if files:
                    # Wait for download to finish
                    sleep(0.5)
                    return files[0], True

                if i > 20:
                    raise Exception(f'File not found ({pattern!r})')

        return files[0], False

    def __get_information_panel(self, sleep_time=0.05):
        photo_key = self.driver.current_url.split('/')[-1]

        i = -1
        while True:
            i += 1
            sleep(sleep_time)
            if i > 50:
                raise NoSuchElementException(f'Warning: An information panel was expected, but wasnt found')

            try:
                return self.driver.find_element_by_xpath(f'//c-wiz[contains(@jslog, "{photo_key}")]')
            except NoSuchElementException:
                pass

    def __get_name_element_from_information_panel(self, information_panel=None):
        information_panel = information_panel or self.__get_information_panel()

        name_element_list = list(filter(lambda element: element.text, information_panel.find_elements_by_xpath("//div[starts-with(@aria-label,'Filename') and text()]")))
        if not name_element_list:
            raise NoSuchElementException()

        return name_element_list[0]

    def _get_media_information(self):
        # Get information panel
        information_panel = self.__get_information_panel()

        # Name
        name_element = self.__get_name_element_from_information_panel(information_panel=information_panel)
        name = name_element.text.strip()
        assert name, f'No name found'

        # Description
        description_element = information_panel.find_element_by_tag_name('textarea')
        description = description_element.text.strip()

        # Location
        while True:
            try:
                map_element = information_panel.find_element_by_css_selector('a[href*="/maps?q="]')
                res = re.findall(r'''([-]?\d+.\d+),([-]?\d+\.\d+)''', map_element.get_attribute('href'))
                latitude, longitude = res[0]
                latitude = Decimal(latitude)
                longitude = Decimal(longitude)
                break
            except NoSuchElementException:
                input(f'Please set a location and hit enter:')

        # Favorite
        try:
            self.driver.find_element_by_xpath(f'//div[contains(@class, "Wyu6lb")]')
            is_favorite = True
        except NoSuchElementException:
            is_favorite = False

        # Albums
        try:
            albums = [element.text for element in information_panel.find_elements_by_xpath('//div[@class="AJM7gb"]') if element.text]
        except NoSuchElementException:
            albums = []

        return {
            'name': name,
            'description': description,
            'latitude': latitude,
            'longitude': longitude,
            'is_favorite': is_favorite,
            'albums': albums,
        }

    def _patch_media_information(self, media_path, infos):
        if media_path.lower().endswith(('.mp4', '.png')):
            return False

        # Location
        if infos['latitude'] is not None and infos['longitude'] is not None:
            i = -1
            while i < 10:
                i += 1
                try:
                    img = Image.open(media_path)
                    break
                except PermissionError:
                    sleep(0.2)

            exif_dict = piexif.load(media_path)

            lat_deg = latlng_helper.to_deg(infos['latitude'], ['S', 'N'])
            lng_deg = latlng_helper.to_deg(infos['longitude'], ['W', 'E'])

            exiv_lat = (latlng_helper.change_to_rational(lat_deg[0]), latlng_helper.change_to_rational(lat_deg[1]), latlng_helper.change_to_rational(lat_deg[2]))
            exiv_lng = (latlng_helper.change_to_rational(lng_deg[0]), latlng_helper.change_to_rational(lng_deg[1]), latlng_helper.change_to_rational(lng_deg[2]))
            exif_dict['GPS'] = {
                piexif.GPSIFD.GPSVersionID: (2, 0, 0, 0),
                piexif.GPSIFD.GPSLatitude: exiv_lat, piexif.GPSIFD.GPSLatitudeRef: lat_deg[3],
                piexif.GPSIFD.GPSLongitude: exiv_lng, piexif.GPSIFD.GPSLongitudeRef: lng_deg[3]
            }

            exif_bytes = piexif_helper.safe_dump(exif_dict)
            if exif_bytes:
                img.save(media_path, exif=exif_bytes)

        # Rating
        img = Image.open(media_path)
        exif_dict = piexif.load(img.info['exif'])

        exif_dict['0th'][piexif.ImageIFD.Rating] = 5 if infos['is_favorite'] else 0

        exif_bytes = piexif_helper.safe_dump(exif_dict)
        if exif_bytes:
            img.save(media_path, exif=exif_bytes)

        return True

    def _next_media(self):
        element = self.driver.find_element_by_css_selector('div[aria-label="View next photo"]')

        if element:
            old_id = self.__get_information_panel().id

            element.click()

            i = -1
            while True:
                i += 1
                sleep(0.05)
                if i > 50:
                    print(f'Warning: An information panel was expected, but wasnt found')
                    self.driver.refresh()
                    i = 0

                try:
                    information_panel = self.__get_information_panel(sleep_time=0)
                    if old_id != information_panel.id:
                        self.__get_name_element_from_information_panel(information_panel=information_panel)
                        return True
                except NoSuchElementException:
                    pass

    def do_backup(self):
        album_handler = AlbumHandler(config.ALBUM_HANDLER_MODE, config.OUT_PATH)

        print('Going to home...')
        restored_page = self._go_to_start()

        print('Checking session...')
        self._assert_logged_in()

        if not restored_page:
            print('Asking to select a media item...')
            self._ask_to_select_media()

        print('Opening the info window if needed...')
        self._open_info_window_if_needed()

        print('Start the loop...')
        while True:
            session_helper.save_session_url(self.driver, config.OUT_PATH)

            infos = self._get_media_information()
            print(infos['name'])

            media_path, just_downloaded = self._download_media_if_needed(infos)
            print('Downloaded')

            # if just_downloaded:
            self._patch_media_information(media_path, infos)
            print('Patched')

            album_handler.handle(media_path, infos)
            print('Handled albums')

            if not self._next_media():
                break


if __name__ == '__main__':
    from google_photos_manager import config

    Backup(config).do_backup()
