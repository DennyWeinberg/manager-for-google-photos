# manager-for-google-photos

Backup
------

Source: https://github.com/gilesknap/gphotos-sync

1. Get your google photos client id
https://docs.google.com/document/d/1ck1679H8ifmZ_4eVbDeD_-jezIcZ-j6MlaNaeQiz7y0/edit

2. Start the process
gphotos-sync "$HOME/Pictures/Google Photos Favorites Backup" --favourites-only --use-flat-path --omit-album-date --skip-shared-albums --secret "$HOME/Downloads/client_secret_116551376886-3tuib1pgd69v4ovju7m7e2p839luluer.apps.googleusercontent.com.json"

Location Fixer Script
---------------------

Sources: https://gist.github.com/chuckleplant/84b48f5c2cb743013462b6cb5f598f01, https://gist.github.com/c060604/8a51f8999be12fc2be498e9ca56adc72

1. Download your location history
https://levionsoftware.com/help-photo-map-for-google-photos/

2. Start the process
python3 locator.py "$HOME/Pictures/Google Photos Favorites Backup/photos" "$HOME/Downloads/Takeout/Location History/Location History.json"

# Credits

https://levionsoftware.com
