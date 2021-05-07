from contextlib import contextmanager

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


@contextmanager
def driver_context(driver_name, out_path, profile_path=None):
    driver_ = None
    try:
        if driver_name.lower() == 'chrome':
            from chromedriver_py import binary_path
            
            options = webdriver.ChromeOptions()

            if profile_path:
                options.add_argument(f'user-data-dir={profile_path}')

            options.add_argument("window-size=1024,768")

            if out_path:
                prefs = {'download.default_directory': out_path}
                options.add_experimental_option('prefs', prefs)

            driver_ = webdriver.Chrome(executable_path=binary_path, options=options)
            driver_.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})");

            yield driver_
        elif driver_name.lower() == 'firefox':
            import geckodriver_autoinstaller

            geckodriver_autoinstaller.install()

            assert profile_path, 'Profile path needed for firefox'
            profile = webdriver.FirefoxProfile(profile_path)

            profile.set_preference('dom.webdriver.enabled', False)
            profile.set_preference('useAutomationExtension', False)

            profile.set_preference("browser.download.folderList", 2)
            profile.set_preference("browser.download.manager.showWhenStarting", False)
            profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "image/jpeg")
            profile.set_preference("browser.helperApps.alwaysAsk.force", False)

            if out_path:
                profile.set_preference("browser.download.dir", out_path)
            
            profile.update_preferences()
            desired = DesiredCapabilities.FIREFOX

            driver_ = webdriver.Firefox(firefox_profile=profile, desired_capabilities=desired)

            driver_.set_window_size(1024, 768)

            yield driver_
        else:
            raise NotImplementedError(f'Driver not implemented: {driver_name!r}')
    finally:
        if driver_ is not None:
            driver_.close()
