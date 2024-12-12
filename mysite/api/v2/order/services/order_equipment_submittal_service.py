import os
import zipfile

from django.core.exceptions import ValidationError

from mysite import settings
from mysite.order.models import Order


class OrderEquipmentSubmittalService:
    """
    Service class to handle operations related to order equipment submittals.
    - Clear equipment submittal
    - Handle file uploads
    - Create and save a zip file containing the equipment submittal
    """

    @staticmethod
    def clear_equipment_submittal(order_id):
        """
        Clears the equipment submittal for the given order.
        """
        Order.objects.filter(id=order_id).update(equipment_submittal=None)

    @staticmethod
    def handle_files(order, files):
        """
        Handle the uploaded files: validate, save, and create a zip file.

        Args:
            order (Order): The order instance to update.
            files (list): A list of uploaded files.

        Raises:
            ValidationError: If uploaded files exceed the maximum allowed size.
        """
        temp_path = os.path.join(os.path.abspath(os.path.dirname("__file__")),
                                 "media/uploads/order_equipment_submittal")

        # Ensure the temp directory exists
        if not os.path.exists(temp_path):
            os.makedirs(temp_path)

        # Validate the total file size
        size_sum = sum([file.size for file in files])
        if size_sum > settings.MAX_UPLOAD_SIZE:
            raise ValidationError("Selected files exceeded maximum upload size!")

        # Save the files to the server
        saved_files = []
        for file in files:
            file_path = os.path.join(temp_path, file.name)
            OrderEquipmentSubmittalService.handle_uploaded_file(file, file_path)
            saved_files.append(file_path)

        # Create and save the zip file
        project_clean_name = order.project_number.translate(str.maketrans('', '', ' !@#$%^&*/'))
        zip_file_name = f"{project_clean_name}-Equipment-Submittal.zip"
        OrderEquipmentSubmittalService.create_zip_file(
            filenames=saved_files,
            path=temp_path,
            project_name=zip_file_name,
        )

        # Save the zip file to the order model
        with open(os.path.join(temp_path, f"/{zip_file_name}"), 'rb') as f:
            order.equipment_submittal.save(zip_file_name, f)

    @staticmethod
    def create_zip_file(filenames, path, project_name):
        """
        Create a zip file from the provided list of file paths and save it.

        Args:
            filenames (list): List of file paths to be zipped.
            path (str): Directory path to save the zip file.
            project_name (str): The name of the zip file to create.

        Returns:
            zipfile.ZipFile: The created ZipFile object.
        """
        zip_filename = os.path.join(path, project_name)
        with zipfile.ZipFile(zip_filename, "w") as zf:
            for file in filenames:
                fdir, fname = os.path.split(file)
                zf.write(file, fname)
                os.remove(file)
        return zf

    @staticmethod
    def handle_uploaded_file(f, file_path):
        """
        Handle the process of saving an uploaded file.

        Args:
            f: The uploaded file object.
            file_path (str): Path where the file will be saved.
        """
        with open(file_path, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)

    @staticmethod
    def update_order_with_equipment_submittal(order, files):
        """
        Main logic to process the equipment submittal, including clearing and uploading files.

        Args:
            order (Order): The order instance to update.
            files (list): The list of uploaded files.

        Returns:
            order (Order): The updated order instance.
        """
        # Clear equipment submittal if clear flag is set
        if 'equipment_submittal-clear' in files:
            OrderEquipmentSubmittalService.clear_equipment_submittal(order.id)
        else:
            # Otherwise, handle the files
            OrderEquipmentSubmittalService.handle_files(order, files)
        return order
