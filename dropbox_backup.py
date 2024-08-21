import subprocess
import os
import dropbox
from dropbox.exceptions import ApiError
import shutil
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText

class DropboxUploader:
    def __init__(self, CHUNK_SIZE, path, days, app_key, app_secret, refresh_token):
        self.CHUNK_SIZE = CHUNK_SIZE
        self.path = path
        self.days = days
        self.app_key = app_key
        self.app_secret = app_secret
        self.refresh_token = refresh_token
        self.dbx = dropbox.Dropbox(
            oauth2_refresh_token=refresh_token,
            app_key=app_key,
            app_secret=app_secret
        )

    def check_folder_exists(self):
        try:
            self.dbx.files_get_metadata(self.path)
            return True
        except ApiError as err:
            if isinstance(err.error, dropbox.files.GetMetadataError) and err.error.is_path() and err.error.get_path().is_not_found():
                return False
            else:
                raise

    def create_folder(self):
        self.dbx.files_create_folder_v2(self.path)

    def upload_file(self, file_name, file_size, max_retries=3, bitrix=False):
        retries = 0
        relative_path = os.path.basename(file_name)
        while retries < max_retries:
            try:
                if not self.check_folder_exists and not bitrix:
                    self.create_folder()
            
                with open(file_name, 'rb') as f:
                    upload_session_start_result = self.dbx.files_upload_session_start(f.read(self.CHUNK_SIZE))
                    cursor = dropbox.files.UploadSessionCursor(session_id=upload_session_start_result.session_id, offset=f.tell())
                    commit = dropbox.files.CommitInfo(path=f"{self.path}/{relative_path}")

                    while f.tell() < file_size:
                        if ((file_size - f.tell()) <= self.CHUNK_SIZE):
                            self.dbx.files_upload_session_finish(f.read(self.CHUNK_SIZE), cursor, commit)
                        else:
                            self.dbx.files_upload_session_append_v2(f.read(self.CHUNK_SIZE), cursor)
                            cursor.offset = f.tell()
                return True
            except Exception as api_err:
                retries += 1
                if retries == max_retries:
                    self.send_email(site, api_err)
                    return False

    def upload_folder(self, folder_path, bitrix=True):
        if bitrix and not self.check_folder_exists():
            self.create_folder()
        for root, dirs, files in os.walk(folder_path):
            for filename in files:
                file_path = os.path.join(root, filename)
                file_size = os.path.getsize(file_path)
                if not self.upload_file(file_path, file_size, bitrix=bitrix):
                    return False
        return True

    def send_email(self, site, api_err):
        # Email settings
        smtp_server = ''
        smtp_port = 587
        email_login = ''
        email_password = ''
        email_to = ''

        msg = MIMEText(f"The site {site} returned status code or error {api_err}.")
        msg['Subject'] = f"{site} - backup {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        msg['From'] = email_login
        msg['To'] = email_to

        s = smtplib.SMTP(smtp_server, smtp_port)
        s.starttls()
        s.login(email_login, email_password)
        s.send_message(msg)
        s.quit()

    def delete_old_files(self):
        try:
            files = self.dbx.files_list_folder(self.path).entries
            now = datetime.now()

            for file in files:
                # Dropbox uses UTC time for file metadata
                file_time = file.client_modified

                # Check if the file is older than `days` days
                if now - file_time > timedelta(days=self.days):
                    self.dbx.files_delete_v2(file.path_lower)
        except Exception as err:
            print(f"Failed to delete old files: {err}")

if __name__ == "__main__":

    #Change those variables 
    root_dir = '/path/to/'
    site = 'site' # name of a Dropbox folder
    database = 'db_name'
    days = 1 # delete Drpbox files older than days
    bitrix_framework = False

    CHUNK_SIZE = 8 * 1024 * 1024 # 8MB
    APP_KEY = ''
    APP_SECRET = ''
    #Get AUTHORIZATION_CODE https://www.dropbox.com/oauth2/authorize?client_id={APP_KEY}&response_type=code&token_access_type=offline
    #Get permanent REFRESH_TOKEN https://api.dropboxapi.com/oauth2/token?code=AUTHORIZATION_CODE&grant_type=authorization_code&client_id=APP_KEY&client_secret=APP_SECRET
    REFRESH_TOKEN = ''

    dropbox_path = "/" + site
    uploader = DropboxUploader(CHUNK_SIZE, dropbox_path, days, APP_KEY, APP_SECRET, REFRESH_TOKEN)
    archive_uploaded = False
    database_uploaded = False
    folder_uploaded = False

    if bitrix_framework:
        folder_uploaded = uploader.upload_folder(root_dir)
    else:
        archive_name = site + '_' + datetime.now().strftime("%Y%m%d_%H%M%S")
        database_dump_name = database + '_' + datetime.now().strftime("%Y%m%d_%H%M%S") + '.sql'
        archive_path = shutil.make_archive(archive_name, 'tar', root_dir)
        archive_name = os.path.basename(archive_path)
        command = f"mysqldump -u root {database} > {database_dump_name}"
        subprocess.run(command, shell=True)
        archive_size = os.path.getsize(f"./{archive_name}")
        database_dump_size = os.path.getsize(f"./{database_dump_name}")
        archive_uploaded = uploader.upload_file(archive_name, archive_size)
        database_uploaded = uploader.upload_file(database_dump_name, database_dump_size)
        os.remove(archive_name)
        os.remove(database_dump_name)

    if (archive_uploaded and database_uploaded) or folder_uploaded:
        uploader.delete_old_files()
