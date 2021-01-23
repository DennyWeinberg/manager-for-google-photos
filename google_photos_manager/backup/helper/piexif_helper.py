import piexif


def safe_dump(exif_dict):
    try:
        try:
            if isinstance(exif_dict['Exif'][42034], bytes):
                del exif_dict['Exif'][42034]
        except:
            pass

        return piexif.dump(exif_dict)
    except Exception as ex:
        if 'Given thumbnail is too large' in str(ex):
            del exif_dict["thumbnail"]
        else:
            raise

        return piexif.dump(exif_dict)
