from os.path import join, dirname, abspath


def __get_session_file(out_path):
    return join(out_path, 'session.txt')


def save_session_url(driver, out_path):
    with open(__get_session_file(out_path), 'w', encoding='utf8') as file:
        file.write(driver.current_url)


def restore_session_url(out_path):
    try:
        with open(__get_session_file(out_path), 'r', encoding='utf8') as file:
            return file.read()
    except FileNotFoundError:
        pass
