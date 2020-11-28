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
from google_photos_manager.common import selenium
from google_photos_manager.common import latlng

from selenium.webdriver.common.keys import Keys


def _cru_out_path(downloads_path):
    if not exists(downloads_path):
        makedirs(downloads_path)


def _go_to_home(driver):
    driver.get(constants.STARTPAGE)


def _assert_logged_in(driver):
    if '/about/' in driver.current_url:
        print(f'Please login or use another profile. Closing in {constants.LOGIN_SECS} seconds')
        sleep(constants.LOGIN_SECS)
        raise Exception('Not logged in')


def _select_first_photo(driver):
    driver.find_element_by_xpath('//body').send_keys(Keys.ARROW_RIGHT)
    sleep(0.1)
    driver.switch_to.active_element.send_keys(Keys.ENTER)
    sleep(1)


def _open_info_window_if_needed(driver):
    if not list(filter(lambda element: element.text, driver.find_elements_by_xpath("//*[text() = 'Info']"))):
        driver.find_element_by_xpath('//body').send_keys('i')


def _download_media_if_needed(driver, infos):
    expected_path = join(config.OUT_PATH, infos['name'])

    if not exists(expected_path):
        driver.find_element_by_xpath('//body').send_keys(Keys.SHIFT, 'd')

        i = -1
        while not exists(expected_path):
            i += 1
            sleep(0.2)
            assert i < 100, f'A download was expected, but no file was found ({expected_path!r})'

        return expected_path, True

    return expected_path, False


def _get_media_information(driver):
    photo_key = driver.current_url.split('/')[-1]

    # Get information panel
    parent_container = driver.find_element_by_css_selector(f'c-wiz[jslog*="{photo_key}"]')

    # Name
    name_element = list(filter(lambda element: element.text, parent_container.find_elements_by_xpath("//div[starts-with(@aria-label,'Filename') and text()]")))[0]
    name = name_element.text.strip()
    assert name, f'No name found'

    # Description
    description_element = parent_container.find_element_by_tag_name('textarea')
    description = description_element.text.strip()

    # Location
    try:
        map_element = parent_container.find_element_by_css_selector('a[href*="/maps?q="]')
        res = re.findall(r'''([-]?\d+.\d+),([-]?\d+\.\d+)''', map_element.get_attribute('href'))
        latitude, longitude = res[0]
        latitude = Decimal(latitude)
        longitude = Decimal(longitude)
    except NoSuchElementException:
        longitude = latitude = None

    # Favorite
    try:
        driver.find_element_by_xpath(f'//div[contains(@class, "Wyu6lb")]')
        is_favorite = True
    except NoSuchElementException:
        is_favorite = False

    # Albums
    try:
        albums = [element.text for element in parent_container.find_elements_by_xpath('//div[@class="AJM7gb"]') if element.text]
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


def _patch_media_information(media_path, infos):
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


def _next_media(driver):
    element = driver.find_element_by_css_selector('div[aria-label="View next photo"]')

    if element:
        element.click()
        sleep(1)

        return True


def do_backup(config):
    album_handler = AlbumHandler(config.ALBUM_HANDLER_MODE, config.OUT_PATH)

    _cru_out_path(config.OUT_PATH)

    with selenium.driver_context(config.DRIVER, profile_path=config.PROFILE_PATH, downloads_path=config.OUT_PATH) as driver:
        print('Going to home...')
        _go_to_home(driver)

        print('Checking session...')
        _assert_logged_in(driver)

        print('Selecting the first media item...')
        _select_first_photo(driver)

        print('Opening the info window if needed...')
        _open_info_window_if_needed(driver)

        print('Start the loop...')
        while True:
            infos = _get_media_information(driver)
            print(infos['name'])

            media_path, just_downloaded = _download_media_if_needed(driver, infos)
            print('Downloaded')

            if just_downloaded:
                _patch_media_information(media_path, infos)
                print('Patched')

            album_handler.handle(media_path, infos)
            print('Handled albums')

            if not _next_media(driver):
                break


if __name__ == '__main__':
    from google_photos_manager import config

    do_backup(config)
