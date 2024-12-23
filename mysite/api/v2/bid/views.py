import datetime
import os

from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from mysite import settings
from mysite.bidfilemgm.models import BidFile
from mysite.core.models import Person, Project
from mysite.s3_file_manager import S3
from .serializers import BidFileSerializer, BidFileCreateSerializer
from .services import BidFileService


class BidFileListView(APIView):
    """
    API view to retrieve a list of bid files with filtering and pagination options.

    - GET: Retrieves a list of bid files based on optional query parameters for search, date range, and ordering.
    """

    permission_classes = [IsAuthenticated]
    def get(self, request) -> Response:
        """
        Retrieve a list of bid files, optionally filtered by search term, date range, and ordering.

        Query Parameters:
            - search: Filter by project name or customer company name.
            - ordering: Order the results by a field (default is 'due_date').
            - fromDate: Start date for filtering bid files by due date (mm/dd/yyyy).
            - toDate: End date for filtering bid files by due date (mm/dd/yyyy).

        Returns:
            - A paginated list of bid files that match the filter criteria.
        """
        search = request.GET.get("search", "")
        ordering = request.GET.get("ordering", "due_date")
        from_date = request.GET.get("fromDate")
        to_date = request.GET.get("toDate")

        try:
            # Get the filtered query set based on the parameters
            object_list = self.get_filtered_query(search, from_date, to_date, ordering)

            # Pagination
            paginator = PageNumberPagination()
            paginator.page_size = (
                settings.PAGE_SIZE
            )  # Ensure PAGE_SIZE is set in settings
            result_page = paginator.paginate_queryset(object_list, request)

            # Serialize the results
            serializer = BidFileSerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)

        except ValueError:
            return Response(
                {"error": "Invalid date format. Use mm/dd/yyyy"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def get_filtered_query(search, from_date, to_date, ordering):
        """
        Helper method to build and return a filtered queryset for BidFiles based on the provided filters.

        Filters the BidFiles based on:
        - search: Filters by project name or customer company name.
        - from_date and to_date: Filters by the due date range.
        - ordering: Orders the results by the specified field.

        Args:
            search (str): The search term for filtering project names or customer company names.
            from_date (str): The start date for filtering by due date in mm/dd/yyyy format.
            to_date (str): The end date for filtering by due date in mm/dd/yyyy format.
            ordering (str): The field by which to order the results.

        Returns:
            QuerySet: A filtered and ordered queryset of BidFile instances.

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
        # Filter for non-archived bid files and apply the ordering
        return BidFile.objects.filter(query).filter(archive=False).order_by(ordering)


class BidFileUpdateView(APIView):
    """
    API view to retrieve and update a BidFile instance.
    - PUT: Retrieve or update a BidFile instance by its ID.
    """

    permission_classes = [IsAuthenticated]

    def put(self, request, bidfiles_id):
        """
        Retrieve or update a BidFile instance with the provided data.
        """
        try:
            bidfile = BidFile.objects.get(id=bidfiles_id)
        except BidFile.DoesNotExist:
            return Response(
                {"error": "BidFile not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if not request.data:
            # If no data is provided, return the current BidFile details
            serializer = BidFileSerializer(bidfile)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Attempt to update the BidFile instance with the new data
        serializer = BidFileSerializer(
            bidfile, data=request.data, partial=True
        )  # partial=True allows partial updates
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BidFileDuplicateView(APIView):
    """
    API view to duplicate an existing BidFile instance.
    - POST: Duplicate an existing BidFile by copying its fields and creating a new instance.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, bidfiles_id):
        """
        Duplicate an existing BidFile instance.
        """
        try:
            this_bidfile = BidFile.objects.get(id=bidfiles_id)
        except BidFile.DoesNotExist:
            return Response(
                {"error": "BidFile not found"}, status=status.HTTP_404_NOT_FOUND
            )

        customer_id = request.data.get("customer")
        if not customer_id:
            return Response(
                {"error": "Customer is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Call internal helper method to handle the duplication process
        duplicated_bidfile = self._duplicate_bidfile(
            this_bidfile, customer_id, request.user
        )

        # Return the new duplicated BidFile instance
        serializer = BidFileSerializer(duplicated_bidfile)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _duplicate_bidfile(self, this_bidfile, customer_id, created_by_user):
        """
        Internal helper function to duplicate a BidFile.
        - Duplicates the relevant fields, assigns a new customer, and returns the duplicated instance.
        """
        try:
            customer = Person.objects.get(id=customer_id)
        except Person.DoesNotExist:
            raise ValueError("Customer not found")

        # Create a new BidFile with the same attributes (excluding file, customer, and created_by)
        duplicated_bfm = BidFile.objects.create(
            project=this_bidfile.project,
            customer=customer,
            created_by=created_by_user,
            due_date=this_bidfile.due_date,
            note=this_bidfile.note,
            archive=this_bidfile.archive,  # If archive is required
            uploaded_file=None,  # Retain the uploaded file if needed
        )

        return duplicated_bfm


class BidFileArchiveView(APIView):
    """
    Archives a bid file if the user is authorized and confirms the action.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        bid_file = get_object_or_404(BidFile, id=id)

        # Check if the requesting user is the creator of the bid file
        if bid_file.created_by != request.user:
            return Response(
                {"error": "You are not authorized to archive this record."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Confirm archiving action
        if request.data.get("confirm"):
            bid_file.archive = True
            bid_file.save()
            return Response(
                {"message": "Bid file archived successfully"},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"error": "Confirmation not received for archiving."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class BidFileDeleteView(APIView):
    """
    API view to delete a BidFile instance.
    - DELETE: Deletes a BidFile instance by ID if the user is authorized.
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, bidfiles_id):
        """
        Delete a BidFile instance.
        """
        this_bidfile = get_object_or_404(BidFile, id=bidfiles_id)

        # Check if the user is authorized to delete the bid file
        if (
            this_bidfile.created_by != request.user
            and request.user.profile.user_type != 2
        ):
            return Response(
                {"error": "You are not authorized to delete this record."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Proceed to delete the file from S3 and then the BidFile
        s3 = S3()
        file_key = str(this_bidfile.uploaded_file)

        # Delete the file from S3
        try:
            s3.delete_file_from_bucket(key=settings.MEDIA_URL + file_key)
        except Exception as e:
            return Response(
                {"error": f"Error deleting file from S3: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        this_bidfile.soft_delete()

        return Response(
            {"message": "BidFile successfully deleted."},
            status=status.HTTP_204_NO_CONTENT,
        )


class BidFileCreateView(APIView):
    """
    Create a new bid file with uploaded files.
    This view processes the files, creates a zip, and uploads it to S3.
    """

    def post(self, request):
        form_data = request.data
        files_list = request.FILES.getlist("uploaded_file")
        customer_id = form_data.get("customer_id")
        project_id = form_data.get("project_id")
        due_date = form_data.get("due_date")

        # Validate required fields
        missing_fields = [
            field
            for field in ["customer_id", "project_id", "due_date"]
            if not form_data.get(field)
        ]
        if missing_fields:
            return Response(
                {"error": f"Missing required fields: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate file size
        if not self._is_valid_file_size(files_list):
            return Response(
                {"error": "Selected files exceeded maximum upload size!"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Handle file uploads and create zip
        temp_path = self._get_temp_path()
        file_paths = BidFileService.handle_uploaded_files(files_list, temp_path)
        zip_file_path = self._create_project_zip(project_id, file_paths, temp_path)

        # Save bid file to database and S3
        self._save_bidfile_to_db(customer_id, project_id, due_date, zip_file_path)

        return Response(
            {"message": "Bid file created successfully."},
            status=status.HTTP_201_CREATED,
        )

    @staticmethod
    def _is_valid_file_size(files_list):
        """
        Check if the total size of uploaded files is within the allowed limit.
        """
        total_size = sum([f.size for f in files_list])
        return total_size <= settings.MAX_UPLOAD_SIZE

    @staticmethod
    def _get_temp_path():
        """
        Generate or retrieve the temporary path for storing uploaded files.
        """
        temp_path = os.path.join(
            os.path.abspath(os.path.dirname("__file__")), "media/uploads/bidfiles"
        )
        os.makedirs(temp_path, exist_ok=True)
        return temp_path

    @staticmethod
    def _create_project_zip(project_id, file_paths, temp_path):
        """
        Clean the project name and create a zip file from the uploaded files.
        """
        project_clean_name = BidFileService.clean_project_name(
            Project.objects.get(id=project_id).name
        )
        return BidFileService.create_zip_file(file_paths, temp_path, project_clean_name)

    def _save_bidfile_to_db(self, customer_id, project_id, due_date, zip_file_path):
        """
        Save the bid file entry to the database and upload the zip to S3.
        """
        bidfile = BidFile.objects.create(
            customer_id=customer_id,
            project_id=project_id,
            due_date=due_date,
            created_by=self.request.user,
        )
        BidFileService.update_bidfile_with_zip(bidfile, zip_file_path)
        return bidfile


class BidFileAddFileView(APIView):
    """
    APIView for adding files to an existing BidFile.
    """

    permission_classes = [IsAuthenticated]


    def post(self, request, bidfile_id):
        """
        Handles POST request to add files to BidFile and update it with a compressed zip file.
        """
        this_bfm = self._get_bidfile(bidfile_id=bidfile_id)
        serializer = self._validate_request_data(
            request=request,
            instance=this_bfm,
        )

        temp_path = self._create_temp_path()
        files_list = request.FILES.getlist("uploaded_file")

        # Check file size limit
        if not self._validate_file_size(files_list):
            return Response(
                {"error": "Selected files exceeded maximum upload size!"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Process file uploads and create zip file
        files_paths = self._save_uploaded_files(
            files_list=files_list,
            temp_path=temp_path,
        )
        zip_file_path = self._create_zip_file(
            files_paths=files_paths,
            temp_path=temp_path,
            bidfile=this_bfm,
        )

        # Update the BidFile instance with the zip file
        self._update_bidfile_with_zip(
            bidfile=this_bfm,
            zip_file_path=zip_file_path,
        )

        return Response(
            {"detail": "File(s) uploaded and updated successfully."},
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _get_bidfile(bidfile_id):
        """
        Retrieves the BidFile instance or raises 404 error.
        """
        return get_object_or_404(BidFile, id=bidfile_id)

    @staticmethod
    def _validate_request_data(request, instance):
        """
        Validates incoming data with BidFileCreateSerializer.
        """
        serializer = BidFileCreateSerializer(
            instance=instance, data=request.data, partial=True
        )
        if not serializer.is_valid():
            raise serializers.ValidationError(serializer.errors)
        return serializer

    @staticmethod
    def _create_temp_path():
        """
        Creates and returns the temporary directory path for file uploads.
        """
        temp_path = os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/uploads/bidfiles")
        if not os.path.exists(temp_path):
            os.makedirs(temp_path)
        return temp_path

    @staticmethod
    def _validate_file_size(files_list):
        """
        Validates that total file size does not exceed maximum allowed size.
        """
        size_sum = sum(f.size for f in files_list)
        return size_sum <= settings.MAX_UPLOAD_SIZE

    @staticmethod
    def _save_uploaded_files(files_list, temp_path):
        """
        Saves each uploaded file in the temp path and returns list of file paths.
        """
        file_paths = BidFileService.handle_uploaded_files(
            files_list=files_list,
            temp_path=temp_path,
        )
        return file_paths

    @staticmethod
    def _create_zip_file(files_paths, temp_path, bidfile):
        """
        Creates a zip file from uploaded files and returns the path to the zip file.
        """
        project_clean_name = BidFileService.clean_project_name(
            project_name=bidfile.project.name
        )
        zip_filename = BidFileService.create_zip_file(
            filenames=files_paths,
            path=temp_path,
            project_name=f"{bidfile.pk}_{project_clean_name}"
        )
        return zip_filename

    @staticmethod
    def _update_bidfile_with_zip(bidfile, zip_file_path):
        """
        Updates the BidFile instance with the new zip file uploaded to S3.
        """
        BidFileService.update_bidfile_with_zip(
            bidfile=bidfile,
            zip_file_path=zip_file_path,
        )
