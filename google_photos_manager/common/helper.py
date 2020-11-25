from contextlib import contextmanager

from selenium import webdriver


@contextmanager
def driver_context(driver_name, profile_path=None, downloads_path=None):
    driver_ = None
    try:
        if driver_name.lower() == 'chrome':
            options = webdriver.ChromeOptions()

            if profile_path:
                options.add_argument(f'user-data-dir={profile_path}')

            if downloads_path:
                prefs = {'download.default_directory': downloads_path}
                options.add_experimental_option('prefs', prefs)

            driver_ = getattr(webdriver, 'Chrome')(options=options)

            yield driver_
        else:
            raise NotImplementedError(f'Driver not implemented: {driver_name!r}')
    finally:
        if driver_ is not None:
            driver_.close()
