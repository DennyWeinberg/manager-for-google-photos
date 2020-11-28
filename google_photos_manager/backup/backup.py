import re
from decimal import Decimal
from os import makedirs
from os.path import exists, join
from time import sleep

import piexif
from PIL import Image

from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from google_photos_manager import constants
from google_photos_manager.backup.album_handler import AlbumHandler
from google_photos_manager.common import selenium, files
from google_photos_manager.common import latlng

from selenium.webdriver.common.keys import Keys


class Backup:
    def __init__(self, config):
        self.config = config
        self.album_handler = AlbumHandler(config.ALBUM_HANDLER_MODE, config.OUT_PATH)

        files.cru_out_path(config.OUT_PATH)

        with selenium.driver_context(config.DRIVER, profile_path=config.PROFILE_PATH, downloads_path=config.OUT_PATH) as self.driver:
            self.do_backup()

    def _go_to_home(self):
        self.driver.get(constants.STARTPAGE)

    def _assert_logged_in(self):
        if '/about/' in self.driver.current_url:
            print(f'Please login or use another profile. Closing in {constants.LOGIN_SECS} seconds')
            sleep(constants.LOGIN_SECS)
            raise Exception('Not logged in')

    def _select_first_photo(self):
        self.driver.find_element_by_xpath('//body').send_keys(Keys.ARROW_RIGHT)
        sleep(0.1)
        self.driver.switch_to.active_element.send_keys(Keys.ENTER)
        sleep(1)

    def _open_info_window_if_needed(self):
        if not list(filter(lambda element: element.text, self.driver.find_elements_by_xpath("//*[text() = 'Info']"))):
            self.driver.find_element_by_xpath('//body').send_keys('i')

    def _download_media_if_needed(self, infos):
        expected_path = join(config.OUT_PATH, infos['name'])

        if not exists(expected_path):
            self.driver.find_element_by_xpath('//body').send_keys(Keys.SHIFT, 'd')

            i = -1
            while not exists(expected_path):
                i += 1
                sleep(0.2)
                if i > 10:
                    print(f'A download was expected, but no file was found ({expected_path!r})')
                    self.driver.refresh()
                    i = 0

            return expected_path, True

        return expected_path, False

    def __get_information_panel(self):
        photo_key = self.driver.current_url.split('/')[-1]

        return self.driver.find_element_by_css_selector(f'c-wiz[jslog*="{photo_key}"]')

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
        try:
            map_element = information_panel.find_element_by_css_selector('a[href*="/maps?q="]')
            res = re.findall(r'''([-]?\d+.\d+),([-]?\d+\.\d+)''', map_element.get_attribute('href'))
            latitude, longitude = res[0]
            latitude = Decimal(latitude)
            longitude = Decimal(longitude)
        except NoSuchElementException:
            longitude = latitude = None

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
        # Location
        if infos['latitude'] is not None and infos['longitude'] is not None:
            img = Image.open(media_path)

            exif_dict = piexif.load(media_path)

            lat_deg = latlng.to_deg(infos['latitude'], ['S', 'N'])
            lng_deg = latlng.to_deg(infos['longitude'], ['W', 'E'])

            exiv_lat = (latlng.change_to_rational(lat_deg[0]), latlng.change_to_rational(lat_deg[1]), latlng.change_to_rational(lat_deg[2]))
            exiv_lng = (latlng.change_to_rational(lng_deg[0]), latlng.change_to_rational(lng_deg[1]), latlng.change_to_rational(lng_deg[2]))
            exif_dict['GPS'] = {
                piexif.GPSIFD.GPSVersionID: (2, 0, 0, 0),
                piexif.GPSIFD.GPSLatitude: exiv_lat, piexif.GPSIFD.GPSLatitudeRef: lat_deg[3],
                piexif.GPSIFD.GPSLongitude: exiv_lng, piexif.GPSIFD.GPSLongitudeRef: lng_deg[3]
            }

            exif_bytes = piexif.dump(exif_dict)
            img.save(media_path, exif=exif_bytes)

        # Rating
        img = Image.open(media_path)
        exif_dict = piexif.load(img.info['exif'])

        exif_dict['0th'][piexif.ImageIFD.Rating] = 5 if infos['is_favorite'] else 0

        exif_bytes = piexif.dump(exif_dict)
        img.save(media_path, exif=exif_bytes)

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
                    information_panel = self.__get_information_panel()
                    if old_id != information_panel.id:
                        self.__get_name_element_from_information_panel(information_panel=information_panel)
                        return True
                except NoSuchElementException:
                    pass

    def do_backup(self):
        album_handler = AlbumHandler(config.ALBUM_HANDLER_MODE, config.OUT_PATH)

        print('Going to home...')
        self._go_to_home()

        print('Checking session...')
        self._assert_logged_in()

        print('Selecting the first media item...')
        self._select_first_photo()

        print('Opening the info window if needed...')
        self._open_info_window_if_needed()

        print('Start the loop...')
        while True:
            infos = self._get_media_information()
            print(infos['name'])

            media_path, just_downloaded = self._download_media_if_needed(infos)
            print('Downloaded')

            if just_downloaded:
                self._patch_media_information(media_path, infos)
                print('Patched')

            album_handler.handle(media_path, infos)
            print('Handled albums')

            if not self._next_media():
                break


if __name__ == '__main__':
    from google_photos_manager import config

    Backup(config).do_backup()
