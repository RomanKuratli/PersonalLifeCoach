from utils import logger
from os import listdir, path, remove

PICTURE_PATH_OS = path_name = path.join(path.dirname(path.abspath(__file__).replace("/utils", "")), "static", "diary_pictures")
PICTURE_PATH_SERVER = "/static/diary_pictures/"
ALLOWED_EXT = {"jpg", "png", "jpeg"}
LOGGER = logger.get_logger("diary_picture_manager")


def _get_file_extension(picture):
    return picture.filename.split(".", 1)[1].lower()


def _is_file_allowed(picture):
    filename = picture.filename
    return "." in filename and _get_file_extension(picture) in ALLOWED_EXT


def _get_file_name(diary_date, index=None):
    return f"{diary_date.year}_{diary_date.month}_{diary_date.day}_{index if index else ''}"


def _get_diary_files():
    return [f for f in listdir(PICTURE_PATH_OS) if path.isfile(path.join(PICTURE_PATH_OS, f))]


def _find_file(filename, files):
    for file in files:
        if filename in file:
            return True
    return False


def add_picture(diary_date, picture):
    LOGGER.debug(f"received picture to store: date={diary_date}, picture={picture}")
    if not _is_file_allowed(picture):
        LOGGER.warning(f"file with name '{picture.filename}' is not allowed")
        return False
    extension = _get_file_extension(picture)
    file_idx = 1
    filename = _get_file_name(diary_date, file_idx)
    files = _get_diary_files()
    while _find_file(filename, files):
        file_idx += 1
        filename = _get_file_name(diary_date, file_idx)
    filename += f".{extension}"
    picture.save(path.join(PICTURE_PATH_OS, filename))
    LOGGER.debug(f"saving picture with name {filename}")
    return True


def delete_picture(filename):
    if _find_file(filename, _get_diary_files()):
        remove(path.join(PICTURE_PATH_OS, filename))
        return True
    return False


def get_pictures_for_entry(entry_date):
    search_name = _get_file_name(entry_date)
    pics = sorted([PICTURE_PATH_SERVER + f for f in listdir(PICTURE_PATH_OS) if search_name in f])
    LOGGER.debug(f"Pictures for entry {entry_date}: {pics}")
    return pics
