import subprocess
import os
import dropbox
from dropbox.exceptions import ApiError
import shutil
from datetime import datetime, timedelta

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

    def upload(self, file_name, file_size):
        if not self.check_folder_exists():
            self.create_folder()

        with open(f"{pwd}/{file_name}", 'rb') as f:
            upload_session_start_result = self.dbx.files_upload_session_start(f.read(self.CHUNK_SIZE))
            cursor = dropbox.files.UploadSessionCursor(session_id=upload_session_start_result.session_id, offset=f.tell())
            commit = dropbox.files.CommitInfo(path=f"{self.path}/{file_name}")

            while f.tell() < file_size:
                if ((file_size - f.tell()) <= self.CHUNK_SIZE):
                    self.dbx.files_upload_session_finish(f.read(self.CHUNK_SIZE), cursor, commit)
                else:
                    self.dbx.files_upload_session_append_v2(f.read(self.CHUNK_SIZE), cursor)
                    cursor.offset = f.tell()

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
        except ApiError as err:
            print(f"Failed to delete old files: {err}")

#Change those variables 
root_dir = '/path/to/the/root/dir'
site = 'site' # name of a Dropbox folder
database = 'dropbox'
days = 1 # delete files older than days

CHUNK_SIZE = 8 * 1024 * 1024 # 8MB
APP_KEY = ''
APP_SECRET = ''
#Get AUTHORIZATION_CODE https://www.dropbox.com/oauth2/authorize?client_id={APP_KEY}&response_type=code&token_access_type=offline
#Get permanent REFRESH_TOKEN https://api.dropboxapi.com/oauth2/token?code=AUTHORIZATION_CODE&grant_type=authorization_code&client_id=APP_KEY&client_secret=APP_SECRET
REFRESH_TOKEN = ''

dropbox_path = "/" + site
archive_name = site + '_' + datetime.now().strftime("%Y%m%d_%H%M%S")
database_dump_name = database + '_' + datetime.now().strftime("%Y%m%d_%H%M%S") + '.sql'
pwd = os.getcwd()

archive_path = shutil.make_archive(archive_name, 'tar', root_dir)
archive_name = os.path.basename(archive_path)

command = f"mysqldump -u root {database} > {database_dump_name}"
subprocess.run(command, shell=True)

archive_size = os.path.getsize(f"./{archive_name}")
database_dump_size = os.path.getsize(f"./{database_dump_name}")

uploader = DropboxUploader(CHUNK_SIZE, dropbox_path, days, APP_KEY, APP_SECRET, REFRESH_TOKEN)
uploader.upload(archive_name, archive_size)
uploader.upload(database_dump_name, database_dump_size)
uploader.delete_old_files()
