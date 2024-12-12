import os
import zipfile

from django.core.exceptions import ValidationError

from mysite import settings


class OrderFieldDrawingService:
    @staticmethod
    def process_field_drawing_files(order, files):
        """Process the field drawing files: validate, save, and create a zip file."""
        # Set the directory for saving files
        temp_path = os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/uploads/field_draw")
        if not os.path.exists(temp_path):
            os.makedirs(temp_path)

        # Validate file sizes
        size_sum = sum([file.size for file in files])
        if size_sum > settings.MAX_UPLOAD_SIZE:
            raise ValidationError("Selected files exceeded maximum upload size!")

        # Save the files
        saved_files = []
        for file in files:
            file_path = os.path.join(temp_path, file.name)
            OrderFieldDrawingService.save_uploaded_file(file, file_path)
            saved_files.append(file_path)

        # Create zip file
        project_clean_name = order.project_number.replace(' ', '_').replace('!', '') \
            .replace('@', '').replace('#', '').replace('$', '').replace('%', '') \
            .replace('^', '').replace('&', '').replace('*', '').replace("/", '')
        zip_file_name = f"{project_clean_name}-Field-Drawing.zip"
        OrderFieldDrawingService.create_zip_file(saved_files, temp_path, zip_file_name)

        # Save zip file to the order
        with open(os.path.join(temp_path, zip_file_name), 'rb') as f:
            order.field_draw.save(zip_file_name, f)

    @staticmethod
    def create_zip_file(filenames, path, zip_file_name):
        """Create a zip file containing the provided files."""
        zip_filename = os.path.join(path, zip_file_name)
        with zipfile.ZipFile(zip_filename, "w") as zf:
            for file in filenames:
                fdir, fname = os.path.split(file)
                zf.write(file, fname)
                os.remove(file)
        return zip_filename

    @staticmethod
    def save_uploaded_file(file, file_path):
        """Save the uploaded file to the specified path."""
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
