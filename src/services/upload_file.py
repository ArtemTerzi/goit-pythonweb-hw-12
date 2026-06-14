"""File upload services module.

Provides services for uploading files (primarily user avatars) to Cloudinary
and retrieving optimized, secure image URLs.
"""

import cloudinary
import cloudinary.uploader


class UploadFileService:
    """Service for handling file uploads using the Cloudinary API.

    Responsible for initializing Cloudinary authentication credentials and uploading
    images with specific transformation configurations.
    """

    def __init__(self, cloud_name, api_key, api_secret):
        """Initializes the UploadFileService and configures the Cloudinary credentials.

        Args:
            cloud_name (str): The Cloudinary cloud name namespace.
            api_key (str): The Cloudinary integration API key.
            api_secret (str): The Cloudinary integration API secret.
        """
        self.cloud_name = cloud_name
        self.api_key = api_key
        self.api_secret = api_secret
        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True,
        )

    @staticmethod
    def upload_file(file, username) -> str:
        """Uploads an image file to Cloudinary and returns a secure, transformed URL.

        Saves the file using a targeted folder path structure based on the username,
        overwrites any existing file under that same public ID, and applies a square
        crop transformation (250x250 pixels, fill crop) before generating the URL.

        Args:
            file (UploadFile): The raw image file object to upload (FastAPI UploadFile).
            username (str): The username of the user, used to construct the unique public ID.

        Returns:
            str: A secure, transformed HTTPS URL pointing to the uploaded image.
        """
        public_id = f"RestApp/{username}"
        r = cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)
        src_url = cloudinary.CloudinaryImage(public_id).build_url(
            width=250, height=250, crop="fill", version=r.get("version")
        )
        return src_url
