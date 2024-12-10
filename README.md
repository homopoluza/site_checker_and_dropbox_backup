# Site Checker and Dropbox Backup

## hosting.py

This script verifies the availability of websites listed in `site.txt`, which must be located in the same directory as `hosting.py`. Users can customize email notifications within the script settings.

## dropbox_backup.py

The `dropbox_backup.py` script automates the creation of `.sql` <b> MySQL || MariaDB </b> database dumps and `.tar` archives, storing them in Dropbox.

### Installation
`pip3 install python-dotenv`  
`pip3 install dropbox`  

Populate `.env` file.  
Store you mysql credantials in `.my.cnf` file within the script folder. If you use passwordless`root@localhost` accout, change this string in the script `command = f"mysqldump --defaults-file=$PWD/.my.cnf {database} > {database_dump_name}"` to `command = f"mysqldump -u root {database} > {database_dump_name}"`  
For Bitrix backups, set `BITRIX=True`
