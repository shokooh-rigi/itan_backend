import os
import zipfile

from django.core.exceptions import ValidationError

from mysite import settings


class OrderFieldDrawingService:
    @staticmethod
    def process_field_drawing_files(order, files):
        if not files:
            return

        temp_path = os.path.join(settings.MEDIA_ROOT, "uploads/field_draw")
        os.makedirs(temp_path, exist_ok=True)

        size_sum = sum([file.size for file in files])
        if size_sum > settings.MAX_UPLOAD_SIZE:
            raise ValidationError("Selected files exceeded maximum upload size!")

        saved_files = []
        for file in files:
            file_path = os.path.join(temp_path, file.name)
            OrderFieldDrawingService.save_uploaded_file(file, file_path)
            saved_files.append(file_path)

        project_clean_name = "".join(c for c in order.project_number if c.isalnum() or c == "_")
        zip_file_name = f"{project_clean_name}-Field-Drawing.zip"

        zip_path = OrderFieldDrawingService.create_zip_file(saved_files, temp_path, zip_file_name)

        with open(zip_path, 'rb') as f:
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
