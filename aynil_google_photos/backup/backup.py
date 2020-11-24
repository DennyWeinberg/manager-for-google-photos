from os import makedirs
from os.path import exists
from time import sleep

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from aynil_google_photos import constants
from aynil_google_photos.common import helper

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


def _open_info_window_if_needed(driver):
    try:
        WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH, "//*[text() = 'Info']")))
    except TimeoutException:
        driver.find_element_by_xpath('//body').send_keys('i')


def _download_photo(driver):
    driver.find_element_by_xpath('//body').send_keys(Keys.SHIFT, 'd')


def do_backup(config):
    _cru_out_path(config.OUT_PATH)

    with helper.driver_context(config.DRIVER, profile_path=config.PROFILE_PATH, downloads_path=config.OUT_PATH) as driver:
        _go_to_home(driver)

        _assert_logged_in(driver)

        _select_first_photo(driver)

        _open_info_window_if_needed(driver)

        _download_photo(driver)

        # TODO: Continue here
        sleep(9999)


if __name__ == '__main__':
    from aynil_google_photos import config

    do_backup(config)
