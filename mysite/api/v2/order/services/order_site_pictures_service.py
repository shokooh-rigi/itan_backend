import os
import zipfile

from django.conf import settings
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from mysite.order.models import Order


class OrderSitePicturesService:
    def __init__(self, order_id, files):
        self.order = self.get_order(order_id)
        self.files = files
        # Use MEDIA_ROOT for the temp path
        self.temp_path = os.path.join(settings.MEDIA_ROOT, "uploads/order_site_pictures")

    def get_order(self, order_id):
        """
        Retrieves the order object or raises a 404 if not found.
        """
        return get_object_or_404(Order, id=order_id)

    def validate_files(self):
        """
        Validates the uploaded files (checks total size).
        """
        size_sum = sum(f.size for f in self.files)
        if size_sum > settings.MAX_UPLOAD_SIZE:
            raise ValidationError("Selected files exceeded maximum upload size!")

    def save_files(self):
        """
        Saves the uploaded files to the temp directory.
        """
        if not os.path.exists(self.temp_path):
            os.makedirs(self.temp_path)

        file_paths = []
        for f in self.files:
            file_path = os.path.join(self.temp_path, f.name)
            self.handle_uploaded_file(f, file_path)
            file_paths.append(file_path)
        return file_paths

    def create_zip(self, files):
        """
        Creates a zip file containing all the uploaded files.
        """
        project_clean_name = self.order.project_number.translate(str.maketrans('', '', ' !@#$%^&*/'))
        zip_file_name = f"{project_clean_name}-Site-Pictures.zip"
        self.create_zip_file(files, self.temp_path, zip_file_name)
        return zip_file_name

    def save_zip(self, zip_file_name):
        """
        Saves the created zip file to the order's `site_pictures` field.
        """
        zip_file_path = os.path.join(self.temp_path, zip_file_name)
        with open(zip_file_path, 'rb') as file:
            self.order.site_pictures.save(zip_file_name, file)

    def process_upload(self):
        """
        Processes the entire upload flow: validation, saving files, zipping, and saving the zip.
        """
        self.validate_files()
        files = self.save_files()
        zip_file_name = self.create_zip(files)
        self.save_zip(zip_file_name)
        return zip_file_name

    def create_zip_file(self, filenames, path, zip_file_name):
        """Create a zip file containing the provided files."""
        zip_filename = os.path.join(path, zip_file_name)
        try:
            with zipfile.ZipFile(zip_filename, "w") as zf:
                for file in filenames:
                    fdir, fname = os.path.split(file)
                    zf.write(file, fname)
                    os.remove(file)  # Remove the original files after zipping
        except Exception as e:
            # Log or raise an exception if creating zip fails
            raise ValidationError(f"Error creating zip file: {str(e)}")
        return zip_filename

    def handle_uploaded_file(self, file, file_path):
        """Save the uploaded file to the specified path."""
        try:
            with open(file_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
        except Exception as e:
            raise ValidationError(f"Error saving file: {str(e)}")

