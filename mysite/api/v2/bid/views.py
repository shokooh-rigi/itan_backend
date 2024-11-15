import datetime

from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from mysite import settings
from mysite.bidfilemgm.models import BidFile
from mysite.core.models import Person
from mysite.s3_file_manager import S3
from .serializers import BidFileSerializer


class BidFileListView(APIView):
    """
    API view to retrieve a list of bid files with filtering and pagination options.

    - GET: Retrieves a list of bid files based on optional query parameters for search, date range, and ordering.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve a list of bid files with filtering options.",
        manual_parameters=[
            openapi.Parameter(
                'search',
                openapi.IN_QUERY,
                description="Search term to filter by project name or customer company name.",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'ordering',
                openapi.IN_QUERY,
                description="Field to order the results by. Defaults to 'due_date'.",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'fromDate',
                openapi.IN_QUERY,
                description="Start date in mm/dd/yyyy format for filtering bid files by due date.",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'toDate',
                openapi.IN_QUERY,
                description="End date in mm/dd/yyyy format for filtering bid files by due date.",
                type=openapi.TYPE_STRING
            ),
        ],
        responses={200: BidFileSerializer(many=True)}
    )
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
        search = request.GET.get('search', '')
        ordering = request.GET.get('ordering', 'due_date')
        from_date = request.GET.get('fromDate')
        to_date = request.GET.get('toDate')

        try:
            # Get the filtered query set based on the parameters
            object_list = self.get_filtered_query(search, from_date, to_date, ordering)

            # Pagination
            paginator = PageNumberPagination()
            paginator.page_size = settings.PAGE_SIZE  # Ensure PAGE_SIZE is set in settings
            result_page = paginator.paginate_queryset(object_list, request)

            # Serialize the results
            serializer = BidFileSerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)

        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use mm/dd/yyyy'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

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
        query = Q(project__name__icontains=search) | Q(customer__company__name__icontains=search)

        # Handle the fromDate and toDate filtering
        if from_date and to_date:
            try:
                from_date_obj = datetime.datetime.strptime(from_date, '%m/%d/%Y')
                to_date_obj = datetime.datetime.strptime(to_date, '%m/%d/%Y') + datetime.timedelta(days=1)
                query &= Q(due_date__range=(from_date_obj, to_date_obj))
            except ValueError:
                raise ValueError('Invalid date format. Use mm/dd/yyyy')

        # Filter for non-archived bid files and apply the ordering
        return BidFile.objects.filter(query).filter(archive=False).order_by(ordering)


class BidFileUpdateView(APIView):
    """
    API view to update a BidFile instance.
    - GET: Retrieve a BidFile's details by its ID.
    - POST: Update an existing BidFile instance with the provided data.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve a BidFile by ID.",
        responses={200: BidFileSerializer(), 404: 'BidFile not found'}
    )
    def get(self, request, bidfiles_id):
        """
        Retrieve a BidFile instance by its ID.
        """
        try:
            bidfile = BidFile.objects.get(id=bidfiles_id)
            serializer = BidFileSerializer(bidfile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except BidFile.DoesNotExist:
            return Response({"error": "BidFile not found"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="Update an existing BidFile instance.",
        request_body=BidFileSerializer(),
        responses={200: BidFileSerializer(), 400: 'Bad request'}
    )
    def post(self, request, bidfiles_id):
        """
        Update a BidFile instance with the provided data.
        """
        try:
            bidfile = BidFile.objects.get(id=bidfiles_id)
        except BidFile.DoesNotExist:
            return Response({"error": "BidFile not found"}, status=status.HTTP_404_NOT_FOUND)

        # Attempt to update the BidFile instance with the new data
        serializer = BidFileSerializer(bidfile, data=request.data, partial=True)  # partial=True allows partial updates
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

    @swagger_auto_schema(
        operation_description="Duplicate a BidFile by ID.",
        request_body=BidFileSerializer(),
        responses={201: BidFileSerializer(), 400: 'Bad request', 404: 'BidFile not found'}
    )
    def post(self, request, bidfiles_id):
        """
        Duplicate an existing BidFile instance.
        """
        try:
            this_bidfile = BidFile.objects.get(id=bidfiles_id)
        except BidFile.DoesNotExist:
            return Response({"error": "BidFile not found"}, status=status.HTTP_404_NOT_FOUND)

        customer_id = request.data.get('customer')
        if not customer_id:
            return Response({"error": "Customer is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Call internal helper method to handle the duplication process
        duplicated_bidfile = self._duplicate_bidfile(this_bidfile, customer_id, request.user)

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

        # Check if the requesting user is the creator or has user_type 2
        if bid_file.created_by == request.user or request.user.profile.user_type == 2:
            # Confirm archiving action
            if request.data.get("confirm"):
                bid_file.archive_record()
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
        if this_bidfile.created_by != request.user and request.user.profile.user_type != 2:
            return Response(
                {"error": "You are not authorized to delete this record."},
                status=status.HTTP_403_FORBIDDEN
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
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        this_bidfile.soft_delete()

        return Response(
            {"message": "BidFile successfully deleted."},
            status=status.HTTP_204_NO_CONTENT
        )
