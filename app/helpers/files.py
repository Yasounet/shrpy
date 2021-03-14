import os
import flask
import secrets
import itertools
from app import config
from werkzeug.security import safe_join
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

class File:
    def __init__(self, file_instance: FileStorage):
        """Class for uploaded files which takes the `werkzeug.datastructures.FileStorage` from `flask.Request.files` as first parameter."""
        if isinstance(file_instance, FileStorage) is False:
            raise Exception("file_instance should be instance of FileStorage from flask.Request.files")

        # Private FileStorage instance
        self.__file = file_instance

        self.custom_filename = None
        self.use_original_filename = False

        # Convert arbitrary filename to secure version
        self.filename = secure_filename(self.__file.filename.lower())

        # Split filename to tuple (filename, ext)
        self.__filename_tuple = os.path.splitext(self.filename)

        # Set original filename and extension
        self.original_filename = self.__filename_tuple[0]
        self.extension = self.__filename_tuple[1]

    def get_filename(self, nbytes=12) -> str:
        """Returns custom filename, generated using `secrets.token_urlsafe`."""
        if self.custom_filename is None:
            custom_filename = secrets.token_urlsafe(nbytes)
            if self.extension in config.TOKENIZED_EXTENSIONS:
                self.custom_filename = '{}{}'.format(custom_filename, self.extension)
            else:
                self.custom_filename = self.unique_filename()
        return self.custom_filename

    def unique_filename(self, save_directory = config.UPLOAD_DIR) -> str:
        unique_name = '{}{}'.format(self.original_filename, self.extension)
        filepath = safe_join(save_directory, unique_name)

        c = itertools.count()
        while os.path.exists(filepath):
            unique_name = '{}_{}{}'.format(self.original_filename, next(c), self.extension)
            filepath = safe_join(save_directory, unique_name)

        return unique_name

    def save(self, save_directory = config.UPLOAD_DIR) -> None:
        """Saves the file to `UPLOAD_DIR`."""
        if os.path.isdir(save_directory) is False:
            os.makedirs(save_directory)

        save_path = safe_join(save_directory, self.get_filename())
        self.__file.save(save_path)

    @staticmethod
    def delete(filename: str) -> bool:
        """Deletes the file from `config.UPLOAD_DIR`, if it exists."""
        file_path = safe_join(config.UPLOAD_DIR, filename)

        if os.path.isfile(file_path) is False:
            return False

        os.remove(file_path)

        return True

    @staticmethod
    def sharex_config() -> dict:
        """Returns the configuration for ShareX as dictionary."""
        cfg = {
            "Name": "{} (File uploader)".format(flask.request.host),
            "Version": "1.0.0",
            "DestinationType": "ImageUploader, FileUploader",
            "RequestMethod": "POST",
            "RequestURL": flask.url_for('api.upload', _external=True),
            "Body": "MultipartFormData",
            "FileFormName": "file",
            "URL": "$json:url$",
            "DeletionURL": "$json:delete_url$",
            "Headers": {
                "Authorization": "YOUR-UPLOAD-PASSWORD-HERE",
                "X-Use-Original-Filename": 1,
            },
            "ErrorMessage": "$json:status$"
        }

        return cfg