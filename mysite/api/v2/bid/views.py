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

from mysite.ibfm.models import iBidFile
from .serializers import BidFileSerializer, BidFileUpdateSerializer


class BidFileListView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve a list of bid files with filtering options",
        manual_parameters=[
            openapi.Parameter(
                'search',
                openapi.IN_QUERY,
                description="Search term",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'ordering',
                openapi.IN_QUERY,
                description="Order by a field",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'fromDate',
                openapi.IN_QUERY,
                description="From date in mm/dd/yyyy",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'toDate',
                openapi.IN_QUERY,
                description="To date in mm/dd/yyyy",
                type=openapi.TYPE_STRING
            ),
        ],
        responses={200: BidFileSerializer(many=True)}
    )
    def get(self, request) -> Response:
        search: str = request.GET.get('search', '')
        ordering: str = request.GET.get('ordering', 'due_date')
        from_date: str = request.GET.get("fromDate")
        to_date: str = request.GET.get("toDate")

        try:
            if not from_date or not to_date:
                object_list = iBidFile.objects.filter(
                    Q(project__name__icontains=search) |
                    Q(customer__company__name__icontains=search)
                ).order_by(ordering)
            else:
                from_date_obj = datetime.datetime.strptime(from_date, '%m/%d/%Y')
                to_date_obj = datetime.datetime.strptime(to_date, '%m/%d/%Y') + datetime.timedelta(days=1)
                object_list = iBidFile.objects.filter(
                    Q(project__name__icontains=search) |
                    Q(customer__company__name__icontains=search)
                ).filter(due_date__range=(from_date_obj, to_date_obj)).order_by(ordering)
            paginator = PageNumberPagination()
            paginator.page_size = settings.PAGE_SIZE
            result_page = paginator.paginate_queryset(object_list, request)

            serializer = BidFileSerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use mm/dd/yyyy'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BidFileCreateView(APIView):
    """
    Create a new bid file entry.
    """
    permission_classes = [IsAuthenticated]

    @staticmethod
    def post(request):
        """
        POST method to create a new bid file.
        """
        serializer = BidFileSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BidFileUpdateView(APIView):
    """
    Edit an existing bid file entry.
    """
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get_object(id: int) -> iBidFile:
        """
        Retrieve a bid file by ID.
        """
        return get_object_or_404(iBidFile, id=id)

    @swagger_auto_schema(
        request_body=BidFileUpdateSerializer,
        operation_description="Update an existing bid file",
        responses={200: BidFileUpdateSerializer}
    )
    def put(self, request, id: int) -> Response:
        """
        PUT method to update an existing bid file.
        """
        try:
            bid_file = self.get_object(id)
            serializer = BidFileUpdateSerializer(bid_file, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # TODO: Add logic for saving or managing uploaded files if needed in the future.


class BidFileDeleteView(APIView):
    """
    Delete a bid file entry.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Delete an existing bid file",
        responses={204: 'No Content'}
    )
    def delete(self, request, id: int) -> Response:
        """
        DELETE method to remove a bid file.
        """
        try:
            bid_file = get_object_or_404(iBidFile, id=id)

            # Check if the user is authorized to delete the bid file
            if bid_file.created_by != request.user:
                return Response(
                    {'error': 'This record was created by another user, you are not authorized to delete this record.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Delete the uploaded file if needed
            # TODO: Consider the logic for deleting the file from its storage location.
            bid_file.uploaded_file.delete()  # Assuming you want to delete the associated file.
            bid_file.delete()
            return Response({'message': 'Bid file deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

#  Todo: PDF Analyzer views related to AddressExtractionRun model was here
#  todo : I do not put them here in this version they must go to their dir and page
