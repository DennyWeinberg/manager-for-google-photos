# manager-for-google-photos

Backup
------

The aim is to be able to have a proper backup mechanism of your personal Google Photos media library.
Why? Google Photos contains `edited` or `estimated` locations that can't be accessed via API and are not present when
downloading them. `Google Takout` neither does this, and doesn't give you a good way of backing up your albums. 

The `backup.py` script uses `selenium` to loop over all your Google Photos media items and does the following:
* Download the item
* Extract the `albums` in order to copy it into a speicic folder
* Extract the `location` information in order to update the exif information
* Checks if the item is a `favorite` in order to update the exif information (rating: 5 starts vs. 0)

The `config.py` gives you control about:
* The `driver` (chrome/...)
* The driver `profile path`
* The driver `download path`
* The `album handler`:

The `albums_handler.py` gives you control about what to do with the items that are present in albums.
The default implementation does a `copy`. Some of you might prefer the creation of symlinks.

The script stores the last url into session.txt, so we restart where we left during a possible previous exception.

# Credits

https://levionsoftware.com
