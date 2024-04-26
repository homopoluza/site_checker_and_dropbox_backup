# Site Checker and Dropbox Backup

## hosting.py

This script verifies the availability of websites listed in `site.txt`, which must be located in the same directory as `hosting.py`. Users can customize email notifications within the script settings.

## dropbox.py

The `dropbox.py` script automates the creation of `.sql` database dumps and `.tar` archives, storing them in Dropbox. It also deletes files older than  the `days` variable. 
