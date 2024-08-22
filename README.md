# Site Checker and Dropbox Backup

## hosting.py

This script verifies the availability of websites listed in `site.txt`, which must be located in the same directory as `hosting.py`. Users can customize email notifications within the script settings.

## dropbox.py

The `dropbox.py` script automates the creation of `.sql` database dumps and `.tar` archives, storing them in Dropbox. It also deletes files older than  the `days` variable. 
For uploading the `/home/bitrix/www/bitrix/backup` folder set the `bitrix_framework` to `True`.

### async 

From documentation:  
> There are a couple of constraints with concurrent sessions to make them work. You can not send data with meth:`files_upload_session_start` or meth:`files_upload_session_finish`.

Concurrent upload is not critical right now, but there is room for improvement.
