import piexif


def safe_dump(exif_dict):
    try:
        return piexif.dump(exif_dict)
    except Exception as ex:
        if 'Given thumbnail is too large' in str(ex):
            del exif_dict["thumbnail"]
        else:
            raise

        return piexif.dump(exif_dict)
