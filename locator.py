import datetime
import json
from os import EX_CONFIG
import time
from bisect import bisect_left
from fractions import Fraction
from glob import glob
from os.path import join, isfile, splitext, basename, dirname

import piexif
from PIL import Image


class Location(object):
    def __init__(self, d=None):
        for key in d or {}:
            if key == 'timestampMs':
                self.timestamp = int(d[key]) / 1000
            elif key == 'timestamp':
                try:
                    self.timestamp = int(time.mktime(datetime.datetime.strptime(d[key], "%Y-%m-%dT%H:%M:%S.%fZ").timetuple()))
                except ValueError:
                    self.timestamp = int(time.mktime(datetime.datetime.strptime(d[key], "%Y-%m-%dT%H:%M:%SZ").timetuple()))
            elif key == 'latitudeE7':
                self.latitude = d[key]
            elif key == 'longitudeE7':
                self.longitude = d[key]

    def __eq__(self, other):
        return self.timestamp == other.timestamp

    def __lt__(self, other):
        return self.timestamp < other.timestamp

    def __le__(self, other):
        return self.timestamp <= other.timestamp

    def __gt__(self, other):
        return self.timestamp > other.timestamp

    def __ge__(self, other):
        return self.timestamp >= other.timestamp

    def __ne__(self, other):
        return self.timestamp != other.timestamp


def find_closest_in_time(locations, a_location):
    pos = bisect_left(locations, a_location)
    if pos == 0:
        return locations[0]
    if pos == len(locations):
        return locations[-1]

    before = locations[pos - 1]
    after = locations[pos]
    if after.timestamp - a_location.timestamp < a_location.timestamp - before.timestamp:
        return after
    else:
        return before


def to_deg(value, loc):
    if value < 0:
        loc_value = loc[0]
    elif value > 0:
        loc_value = loc[1]
    else:
        loc_value = ""
    abs_value = abs(value)
    deg = int(abs_value)
    t1 = (abs_value - deg) * 60
    min = int(t1)
    sec = round((t1 - min) * 60, 5)

    return deg, min, sec, loc_value


def change_to_rational(number):
    """convert a number to rantional
    Keyword arguments: number
    return: tuple like (1, 2), (numerator, denominator)
    """
    f = Fraction(str(number))
    return f.numerator, f.denominator


class LocationFixer:
    INCLUDED_EXTENSIONS = ['.jpg', '.JPG', '.jpeg', '.JPEG']
    HOURS_THRESHOLD = 3

    def __init__(self, photos_folder_path, locations_file_path):
        self.photos_folder_path = photos_folder_path
        self.locations_file_path = locations_file_path

        self.locations = []
        self.photos = []
        self.photos_without_location = []
        self.photos_fixable = []

    def run(self):
        self.state_00_load_location_history_file()
        self.state_01_get_photos()
        self.state_02_get_photos_with_missing_location()
        self.state_03_collect_fixable_photos()
        self.state_04_fix_photos()

    def state_00_load_location_history_file(self):
        print('Loading locations...')
        with open(self.locations_file_path) as f:
            location_data = json.load(f)
            location_array = location_data['locations']

            for location in location_array:
                location = Location(location)
                if location.timestamp:
                    self.locations.append(location)
                else:
                    print('Location missing timestamp')

        print(f' Locations: {len(self.locations)}')

    def state_01_get_photos(self):
        print('Loading photos...')
        for file in glob(join(self.photos_folder_path, '**'), recursive=True):
            if isfile(file):
                file_name = basename(file)
                file_containing_folder_path = dirname(file)
                file_name_without_extension, ext = splitext(file_name)
                if ext in self.INCLUDED_EXTENSIONS:
                    self.photos.append((file, file_containing_folder_path, file_name_without_extension, ext))

        print(f' Photos: {len(self.photos)}')

    def state_02_get_photos_with_missing_location(self):
        print('Filtering photos by missing location...')
        for file, file_containing_folder_path, file_name_without_extension, ext in self.photos:
            image = Image.open(file)
            exif = image._getexif()
            if not exif:
                print('Photo missing EXIF data:',file)
            else:
                location = exif.get(34853)
                if not location:
                    self.photos_without_location.append(
                        (file, file_containing_folder_path, file_name_without_extension, ext, exif))

        print(f' Photos without location: {len(self.photos_without_location)}')

    def state_03_collect_fixable_photos(self):
        print('Filtering photos by fixable locations...')
        for file, file_containing_folder_path, file_name_without_extension, ext, exif in self.photos_without_location:
            time_exif = exif.get(36867)
            if time_exif:
                time_exif = time_exif.rstrip('\x00')
                try:
                    time_jpeg_unix = time.mktime(datetime.datetime.strptime(time_exif, "%Y:%m:%d %H:%M:%S").timetuple())
                except ValueError:
                    try:
                        time_jpeg_unix = time.mktime(datetime.datetime.strptime(time_exif, "%Y/%m/%d %H:%M:%S").timetuple())
                    except ValueError:
                        time_jpeg_unix = time.mktime(datetime.datetime.strptime(time_exif, "%Y:%m:%d %H:%M:%S.%f").timetuple())

                curr_loc = Location()
                curr_loc.timestamp = int(time_jpeg_unix)

                approx_location = find_closest_in_time(self.locations, curr_loc)
                lat_f = float(approx_location.latitude) / 10000000.0
                lon_f = float(approx_location.longitude) / 10000000.0

                hours_away = abs(approx_location.timestamp - time_jpeg_unix) / 3600
                in_threshold = hours_away < self.HOURS_THRESHOLD

                print(f'  Found location for photos {file}. Hours away: {hours_away}. In threshold: {in_threshold}')

                if in_threshold:
                    self.photos_fixable.append(
                        (file, file_containing_folder_path, file_name_without_extension, ext, lat_f, lon_f))

        print(f' Photos to fix: {len(self.photos_fixable)}')

    def state_04_fix_photos(self):
        print(f' Fixing...')
        for file, file_containing_folder_path, file_name_without_extension, ext, lat_f, lon_f in self.photos_fixable:
            img = Image.open(file)
            exif_dict = piexif.load(img.info['exif'])

            lat_deg = to_deg(lat_f, ["S", "N"])
            lng_deg = to_deg(lon_f, ["W", "E"])

            exiv_lat = (change_to_rational(lat_deg[0]), change_to_rational(lat_deg[1]), change_to_rational(lat_deg[2]))
            exiv_lng = (change_to_rational(lng_deg[0]), change_to_rational(lng_deg[1]), change_to_rational(lng_deg[2]))
            exif_dict['GPS'] = {
                piexif.GPSIFD.GPSVersionID: (2, 0, 0, 0),
                piexif.GPSIFD.GPSLatitude: exiv_lat, piexif.GPSIFD.GPSLatitudeRef: lat_deg[3],
                piexif.GPSIFD.GPSLongitude: exiv_lng, piexif.GPSIFD.GPSLongitudeRef: lng_deg[3]
            }

            try:
                exif_bytes = piexif.dump(exif_dict)
            except ValueError:
                #https://github.com/hMatoba/Piexif/issues/95
                #Probably should check the field id before wiping...
                exif_dict['Exif'][41729] = b'1'
                exif_bytes = piexif.dump(exif_dict)

            try:
                img.save(file, exif=exif_bytes)
            except (OSError, PermissionError) as error:
                print('Save fail!',file)

        print(f' Done')


if __name__ == '__main__':
    import sys

    LocationFixer(sys.argv[1], sys.argv[2]).run()
