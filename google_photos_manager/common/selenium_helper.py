from contextlib import contextmanager

from selenium import webdriver

from google_photos_manager.common import session_helper


@contextmanager
def driver_context(driver_name, out_path, profile_path=None):
    driver_ = None
    try:
        if driver_name.lower() == 'chrome':
            options = webdriver.ChromeOptions()

            if profile_path:
                options.add_argument(f'user-data-dir={profile_path}')

            if profile_path:
                options.add_argument("window-size=1000,800")

            if out_path:
                prefs = {'download.default_directory': out_path}
                options.add_experimental_option('prefs', prefs)

            driver_ = getattr(webdriver, 'Chrome')(options=options)

            yield driver_
        else:
            raise NotImplementedError(f'Driver not implemented: {driver_name!r}')
    finally:
        if driver_ is not None:
            try:
                session_helper.save_session_url(driver_, out_path)
            finally:
                driver_.close()
