import os
from rest_framework.parsers import MultiPartParser
from django.conf import settings
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers
from rest_framework import status
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    RetrieveAPIView,
)
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from mysite import settings
from mysite.bidfilemgm.models import BidFile, BidAttachment
from mysite.core.models import Person, Project
from mysite.s3_file_manager import S3
from .serializers import BidSerializer, BidCreateSerializer, BidAttachmentSerializer
from .services import BidService


class BidDetailListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve a Bid ",
        description="Retrieve a specific bid  by its ID if it exists and is not deleted or archived.",
        parameters=[
            OpenApiParameter(
                name="id", description="The ID of the bid file", required=True, type=int
            ),
        ],
        responses={
            200: BidSerializer,
            404: dict,
        },
    )
    def get(self, request, id: int) -> Response:
        """
        Retrieve a bid by bid ID.

        Args:
            id (int): The ID of the bid .

        Returns:
            - 200: Bid  data if found.
            - 404: Error message if the bid  is not found.
        """
        try:
            bid_file = BidFile.objects.filter(
                id=id,
                is_deleted=False,
                archive=False,
            )
        except BidFile.DoesNotExist:
            return Response(
                {"error": "Bid not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        # Serialize the retrieved object
        serializer = BidSerializer(bid_file, many=True)
        paginator = PageNumberPagination()
        paginator.page_size = int(request.GET.get("page_size", settings.PAGE_SIZE))
        result_page = paginator.paginate_queryset(bid_file, request)
        serializer = BidSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)


class BidListView(APIView):
    """
    API view to retrieve a list of bids with filtering and pagination options.

    - GET: Retrieves a list of bids based on optional query parameters for search, date range, and ordering.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "search",
                openapi.IN_QUERY,
                description="Filter by project name or customer company name",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "ordering",
                openapi.IN_QUERY,
                description="Order the results by a field (default is 'due_date')",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "fromDate",
                openapi.IN_QUERY,
                description="Start date for filtering bids by due date (mm/dd/yyyy)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "toDate",
                openapi.IN_QUERY,
                description="End date for filtering bids by due date (mm/dd/yyyy)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "page",
                openapi.IN_QUERY,
                description="Page number for pagination",
                type=openapi.TYPE_INTEGER,
                required=False,
            ),
            openapi.Parameter(
                "page_size",
                openapi.IN_QUERY,
                description="Number of items per page",
                type=openapi.TYPE_INTEGER,
                required=False,
            ),
        ],
        responses={
            200: openapi.Response(
                "A paginated list of bids",
                BidSerializer(many=True),
            ),
            400: "Invalid date format or other error",
        },
    )
    def get(self, request) -> Response:
        """
        Retrieve a list of bids, optionally filtered by search term, date range, and ordering.

        Query Parameters:
            - search: Filter by project name or customer company name.
            - ordering: Order the results by a field (default is 'due_date').
            - fromDate: Start date for filtering bids by due date (mm/dd/yyyy).
            - toDate: End date for filtering bids by due date (mm/dd/yyyy).
            - page: Page number for pagination.
            - page_size: Number of items per page.

        Returns:
            - A paginated list of bids that match the filter criteria.
        """
        search = request.GET.get("search", "")
        ordering = request.GET.get("ordering", "due_date")
        from_date = request.GET.get("fromDate")
        to_date = request.GET.get("toDate")

        try:
            bid_service = BidService()
            object_list = bid_service.get_filtered_query(
                search=search,
                from_date=from_date,
                to_date=to_date,
                ordering=ordering,
            )
            paginator = PageNumberPagination()
            paginator.page_size = int(request.GET.get("page_size", settings.PAGE_SIZE))
            result_page = paginator.paginate_queryset(object_list, request)
            serializer = BidSerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)

        except ValueError:
            return Response(
                {"error": "Invalid date format. Use mm/dd/yyyy"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BidUpdateView(APIView):
    """
    API view to retrieve and update a Bid instance.
    - PUT: Retrieve or update a Bid instance by its ID.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve or update a Bid instance by its ID.",
        request_body=BidSerializer,  # Input schema
        responses={
            200: openapi.Response(
                "Successfully updated the Bid instance", BidSerializer
            ),
            400: "Validation error in input data",
            404: "Bid not found",
        },
    )
    def put(self, request, bid_id):
        """
        Retrieve or update a Bid instance with the provided data.
        """
        try:
            bid = BidFile.objects.get(id=bid_id)
        except BidFile.DoesNotExist:
            return Response(
                {"error": "Bid not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Attempt to update the Bid instance with the new data
        serializer = BidSerializer(
            bid, data=request.data, partial=True
        )  # partial=True allows partial updates
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BidDuplicateView(APIView):
    """
    API view to duplicate an existing Bid instance.
    - POST: Duplicate an existing Bid by copying its fields and creating a new instance.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Duplicate an existing Bid instance by copying its fields and creating a new instance.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "customer_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="ID of the new customer to assign the duplicated Bid",
                ),
            },
            required=["customer_id"],
        ),
        responses={
            201: openapi.Response(
                description="The duplicated Bid instance",
                schema=BidSerializer(),
            ),
            400: openapi.Response(description="Invalid input"),
            404: openapi.Response(description="Bid or Customer not found"),
        },
    )
    def post(self, request, bid_id):
        """
        Duplicate an existing Bid instance.
        """
        try:
            this_bid = BidFile.objects.get(id=bid_id)
        except BidFile.DoesNotExist:
            return Response(
                {"error": "Bid not found"}, status=status.HTTP_404_NOT_FOUND
            )

        customer_id = request.data.get("customer_id")
        if not customer_id:
            return Response(
                {"error": "Customer is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        # Call internal helper method to handle the duplication process
        duplicated_bid = self._duplicate_bid(
            this_bid=this_bid,
            customer_id=int(customer_id),
            created_by_user=request.user,
        )

        # Return the new duplicated Bid instance
        serializer = BidSerializer(duplicated_bid)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @staticmethod
    def _duplicate_bid(
        this_bid: BidFile,
        customer_id: int,
        created_by_user,
    ):
        """
        Internal helper function to duplicate a Bid.
        - Duplicates the relevant fields, assigns a new customer, and returns the duplicated instance.
        """
        try:
            customer = Person.objects.get(id=customer_id)
        except Person.DoesNotExist:
            raise ValueError("Customer not found")

        # Create a new Bid with the same attributes (excluding file, customer, and created_by)
        duplicated_bfm = BidFile.objects.create(
            project=this_bid.project,
            customer=customer,
            created_by=created_by_user,
            due_date=this_bid.due_date,
            note=this_bid.note,
            archive=this_bid.archive,  # If archive is required
        )

        # for each attachment in the original bid, create a new attachment for the duplicated bid
        for attachment in BidAttachment.objects.filter(bid=this_bid):
            BidAttachment.objects.create(
                bid=duplicated_bfm,
                uploaded_file=attachment.uploaded_file,
                created_by=created_by_user,
            )

        return duplicated_bfm


class BidArchiveView(APIView):
    """
    Archives a bid if the user is authorized
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Archives a Bid if the user is authorized and confirms the action.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
        ),
        responses={
            200: openapi.Response(
                "Successfully archived the bid file",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"message": openapi.Schema(type=openapi.TYPE_STRING)},
                ),
            ),
            403: "User is not authorized to archive this record.",
            404: "Bid not found.",
        },
    )
    def post(self, request, bid_id):
        bid = get_object_or_404(
            BidFile,
            id=bid_id,
            is_deleted=False,
        )

        # Check if the requesting user is the creator of the bid file
        if bid.created_by != request.user:
            return Response(
                {"error": "You are not authorized to archive this record."},
                status=status.HTTP_403_FORBIDDEN,
            )

        bid.archive = True
        bid.save()
        return Response(
            {"message": "Bid archived successfully"},
            status=status.HTTP_200_OK,
        )


class BidDeleteView(APIView):
    """
    API view to delete a Bid instance.
    - DELETE: Deletes a Bid instance by ID if the user is authorized.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Deletes a Bid instance if the user is authorized.",
        responses={
            200: openapi.Response(
                "Successfully deleted the Bid",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"message": openapi.Schema(type=openapi.TYPE_STRING)},
                ),
            ),
            403: "User is not authorized to delete this record.",
            404: "Bid not found.",
            500: "Error deleting file from S3.",
        },
    )
    def delete(self, request, bid_id):
        """
        Delete a Bid instance and all related BidAttachment instances.
        """
        this_bid = get_object_or_404(
            BidFile,
            id=bid_id,
            is_deleted=False,
        )

        # Check if the user is authorized to delete the bid
        if this_bid.created_by != request.user and request.user.profile.user_type != 2:
            return Response(
                {"error": "You are not authorized to delete this record."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Delete related BidAttachment files from S3
        related_attachments = BidAttachment.objects.filter(bid=this_bid)
        for attachment in related_attachments:
            # Delete the attachment record from the database
            attachment.delete()

        # Soft delete the Bid
        this_bid.soft_delete()

        return Response(
            {"message": "Bid and related attachments successfully deleted."},
            status=status.HTTP_200_OK,
        )


class BidCreateView(APIView):
    """
    Create a new bid file with uploaded files.
    This view processes the files, validates extensions, creates a zip, and uploads it to S3.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Creates a new Bid by uploading and processing files. The files are validated, zipped, and stored in S3.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "customer": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="ID of the customer"
                ),
                "project": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="ID of the project"
                ),
                "due_date": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Due date for the bid file"
                ),
                "uploaded_file": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_FILE),
                    description="List of uploaded files",
                ),
            },
            required=["customer", "project", "due_date", "uploaded_file"],
        ),
        responses={
            201: openapi.Response(
                "Bid file created successfully.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"message": openapi.Schema(type=openapi.TYPE_STRING)},
                ),
            ),
            400: openapi.Response(
                "Bad Request - Missing required fields, invalid file size or extension.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"error": openapi.Schema(type=openapi.TYPE_STRING)},
                ),
            ),
            500: openapi.Response(
                "Internal Server Error - Error during file upload or zip creation.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"error": openapi.Schema(type=openapi.TYPE_STRING)},
                ),
            ),
        },
    )
    def post(self, request):
        form_data = request.data
        files_list = request.FILES.getlist("uploaded_file")
        customer = form_data.get("customer")
        project = form_data.get("project")
        due_date = form_data.get("due_date")
        type = form_data.get("type")
        note = form_data.get("note")

        # Validate required fields
        missing_fields = [
            field
            for field in ["customer", "project", "due_date"]
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

        # Validate file extensions
        if not self._are_valid_extensions(files_list):
            return Response(
                {
                    "error": "Invalid file extension. Only zip, pdf, and docx are allowed."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # # Handle file uploads
        # temp_path = self._get_temp_path()
        # file_paths = BidService.handle_uploaded_files(files_list, temp_path)
        # zip_file_path = self._create_project_zip(project_id, file_paths, temp_path)

        # # Save bid file to database and S3
        # self._save_bid_to_db(customer_id, project_id, due_date, zip_file_path)

        # Create Bid instance
        bid = BidFile.objects.create(
            type=type if type else None,
            customer_id=customer,
            project_id=project,
            due_date=due_date,
            note=note,
            created_by=request.user,
        )

        # Create BidAttachment for each file
        for file in files_list:
            BidAttachment.objects.create(
                bid=bid,
                uploaded_file=file,
                created_by=request.user,
            )

        return Response(
            {"message": "Bid created successfully."},
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
    def _are_valid_extensions(files_list):
        """
        Check if all uploaded files have valid extensions.
        """
        allowed_extensions = {"zip", "pdf", "docx"}
        for file in files_list:
            file_extension = os.path.splitext(file.name)[-1].lower().strip(".")
            if file_extension not in allowed_extensions:
                return False
        return True


class BidAddFileView(APIView):
    """
    APIView for adding files to an existing Bid.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Handles POST request to add files to Bid and update it with a compressed zip file.",
        request_body=BidCreateSerializer,
        responses={
            200: "File(s) uploaded and updated successfully.",
            400: "Selected files exceeded maximum upload size!",
        },
    )
    def post(self, request, bid_id):
        """
        Handles POST request to add files to Bid and update it with a compressed zip file.
        """
        bid = self._get_bid(bid_id=bid_id)
        serializer = self._validate_request_data(
            request=request,
            instance=bid,
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
            bid=bid,
        )

        # Update the Bid instance with the zip file
        self._update_bid_with_zip(
            bid=bid,
            zip_file_path=zip_file_path,
        )

        return Response(
            {"detail": "File(s) uploaded and updated successfully."},
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _get_bid(bid_id):
        """
        Retrieves the Bid instance or raises 404 error.
        """
        return get_object_or_404(BidFile, id=bid_id, is_deleted=False)

    @staticmethod
    def _validate_request_data(request, instance):
        """
        Validates incoming data with BidCreateSerializer.
        """
        serializer = BidCreateSerializer(
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
        temp_path = os.path.join(
            os.path.abspath(os.path.dirname("__file__")), "media/uploads/bidfiles"
        )
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
        file_paths = BidService.handle_uploaded_files(
            files_list=files_list,
            temp_path=temp_path,
        )
        return file_paths

    @staticmethod
    def _create_zip_file(files_paths, temp_path, bid):
        """
        Creates a zip file from uploaded files and returns the path to the zip file.
        """
        project_clean_name = BidService.clean_project_name(
            project_name=bid.project.name
        )
        zip_filename = BidService.create_zip_file(
            filenames=files_paths,
            path=temp_path,
            project_name=f"{bid.pk}_{project_clean_name}",
        )
        return zip_filename

    @staticmethod
    def _update_bid_with_zip(bid, zip_file_path):
        """
        Updates the Bid instance with the new zip file uploaded to S3.
        """
        BidService.update_bid_with_zip(
            bid=bid,
            zip_file_path=zip_file_path,
        )


class BidAttachmentRetrieveView(RetrieveAPIView):
    """
    API view for retrieving a specific BidAttachment.
    """

    queryset = BidAttachment.objects.all()
    serializer_class = BidAttachmentSerializer

    @swagger_auto_schema(operation_description="Retrieve a specific BidAttachment")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class BidAttachmentListCreateView(ListCreateAPIView):
    """
    API view for listing all BidAttachments and creating a new one.
    """

    serializer_class = BidAttachmentSerializer
    parser_classes = [MultiPartParser]  # Support file uploads

    def get_queryset(self):
        bid_id = self.kwargs.get("bid_id")  # Get bid_id from URL
        return BidAttachment.objects.filter(bid=bid_id)

    @swagger_auto_schema(
        operation_description="List all BidAttachments and create a new one",
        parameters=[
            OpenApiParameter(
                name="bid_id", description="The ID of the bid", required=True, type=int
            ),
        ],
        request_body=BidAttachmentSerializer,
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class BidAttachmentRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, and deleting a specific BidAttachment.
    """

    queryset = BidAttachment.objects.all()
    serializer_class = BidAttachmentSerializer
    parser_classes = [MultiPartParser]  # Support file uploads

    @swagger_auto_schema(
        operation_description="Retrieve, update, or delete a specific BidAttachment",
        request_body=BidAttachmentSerializer,
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        file = request.FILES.get("file")

        if file:
            # Delete the old file from S3 if it exists
            s3 = S3()
            if instance.file_path:
                s3.delete_file_from_bucket(key=instance.file_path)

            # Upload the new file to S3
            new_file_path = s3.upload_file(file)
            request.data["file_path"] = new_file_path  # Set the new file path in DB

        # Perform the update
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_destroy(self, instance):
        # s3 = S3()
        # Delete file from S3 if it exists
        # if instance.file_path:
        #     s3.delete_file_from_bucket(key=instance.file_path)

        # Perform the actual deletion of the model instance
        instance.delete()

    @swagger_auto_schema(operation_description="Delete a specific BidAttachment")
    def destroy(self, request, *args, **kwargs):
        # Ensure the file is deleted from S3 before deleting the instance
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
