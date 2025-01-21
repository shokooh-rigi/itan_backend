import datetime
import os
import zipfile

from django.db.models import Q

from mysite.bid.models import Bid
from mysite.s3_file_manager import S3


class BidService:
    @staticmethod
    def handle_uploaded_files(files_list, temp_path):
        """
        Saves each uploaded file to the specified temporary path and returns a list of their paths.
        """
        file_paths = []
        for f in files_list:
            file_path = os.path.join(temp_path, f.name)
            with open(file_path, 'wb+') as destination:
                for chunk in f.chunks():
                    destination.write(chunk)
            file_paths.append(file_path)
        return file_paths

    @staticmethod
    def create_zip_file(filenames, path, project_name):
        """
        Creates a zip file from the provided file paths and returns the zip file path.
        """
        # Ensure the zip filename has a .zip extension
        zip_filename = os.path.join(path, f"{project_name}.zip")
        
        # Create a new zip file
        with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in filenames:
                fdir, fname = os.path.split(file)
                zf.write(file, fname)  # Store the file in the zip
                os.remove(file)  # Remove the original file after adding it to the zip

        return zip_filename

    @staticmethod
    def clean_project_name(project_name):
        """
        Cleans special characters from project names for safe file naming.
        """
        return project_name.replace(' ', '_') \
            .replace('!', '').replace('@', '').replace('#', '').replace('$', '') \
            .replace('%', '').replace('^', '').replace('&', '').replace('*', '').replace("/", '')

    @staticmethod
    def update_bid_with_zip(bid, zip_file_path):
        print(zip_file_path)
        """
        Uploads the zip file to S3 and updates the bid record with the file path.
        """
        s3 = S3()
        with open(zip_file_path, 'rb') as file:
            bid.uploaded_file.save(os.path.basename(zip_file_path), file)
        os.remove(zip_file_path)  # Cleanup zip file after upload

    @staticmethod
    def get_filtered_query(
            search,
            from_date,
            to_date,
            ordering,
    ):
        """
        Helper method to build and return a filtered queryset for Bids based on the provided filters.

        Filters the Bids based on:
        - search: Filters by project name or customer company name.
        - from_date and to_date: Filters by the due date range.
        - ordering: Orders the results by the specified field.

        Args:
            search (str): The search term for filtering project names or customer company names.
            from_date (str): The start date for filtering by due date in mm/dd/yyyy format.
            to_date (str): The end date for filtering by due date in mm/dd/yyyy format.
            ordering (str): The field by which to order the results.

        Returns:
            QuerySet: A filtered and ordered queryset of Bid instances.

        Raises:
            ValueError: If the date format is invalid.
        """
        # Build the initial query for filtering by search term
        query = Q()
        if search:
            query = Q(project__name__icontains=search) | Q(
                customer__company__name__icontains=search
            )

        # Handle the fromDate and toDate filtering
        if from_date and to_date:
            try:
                from_date_obj = datetime.datetime.strptime(from_date, "%m/%d/%Y")
                to_date_obj = datetime.datetime.strptime(
                    to_date, "%m/%d/%Y"
                ) + datetime.timedelta(days=1)
                query &= Q(due_date__range=(from_date_obj, to_date_obj))
            except ValueError:
                raise ValueError("Invalid date format. Use mm/dd/yyyy")
        # Filter for non-archived bid and apply the ordering
        response = Bid.objects.filter(query).filter(
            archive=False,
            is_deleted=False
        ).order_by(ordering)
        return response

