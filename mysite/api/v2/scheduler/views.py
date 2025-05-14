import datetime
import logging
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from mysite import settings
from mysite.core.models import Profile
from mysite.order.models import Order
from mysite.scheduler.models import Schedule, ScheduleTech
from .serializers import ScheduleSerializer, ScheduleTechSerializer
from ..core.serializers import ProfileSerializer
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)


class ScheduleListView(APIView):
    """
    API view to retrieve a list of schedules with filtering and pagination options.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Retrieve a list of schedules",
        operation_description="Retrieve a paginated list of schedules with optional filters such as search, date range, and ordering.",
        manual_parameters=[
            openapi.Parameter(
                "search",
                openapi.IN_QUERY,
                description="Search term to filter schedules by project number, contractor name, or company name.",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "ordering",
                openapi.IN_QUERY,
                description="Field to order the schedules by. Default is '-created_on'.",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "fromDate",
                openapi.IN_QUERY,
                description="Start date for filtering schedules (format: MM/DD/YYYY).",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "toDate",
                openapi.IN_QUERY,
                description="End date for filtering schedules (format: MM/DD/YYYY).",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "page_size",
                openapi.IN_QUERY,
                description="Number of schedules to display per page. Default is set in settings.PAGE_SIZE.",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "page",
                openapi.IN_QUERY,
                description="Page number to retrieve. Default is 1.",
                type=openapi.TYPE_INTEGER,
            ),
        ],
        responses={
            200: openapi.Response(
                description="Paginated list of schedules.",
                examples={
                    "application/json": {
                        "results": [
                            {
                                "id": 1,
                                "order": "Project 123",
                                "schedule_start": "2023-10-01T10:00:00Z",
                                "assigned_to": "Employer/Contractor A",
                            }
                        ],
                        "pagination": {
                            "total_rows": 100,
                            "total_pages": 10,
                            "current_page": 1,
                            "page_size": 10,
                        },
                    }
                },
            ),
            400: openapi.Response(
                description="Invalid input parameters.",
                examples={
                    "application/json": {"error": "Invalid date format. Use mm/dd/yyyy"}
                },
            ),
            500: openapi.Response(
                description="Server error.",
                examples={
                    "application/json": {
                        "error": "An error occurred while processing the request."
                    }
                },
            ),
        },
    )
    def get(self, request):
        """
        Handles GET requests to retrieve schedules based on the provided filters and pagination options.
        """
        search = request.GET.get("search", "")
        ordering = request.GET.get("ordering", "-created_on")
        from_date = request.GET.get("fromDate")
        to_date = request.GET.get("toDate")
        page_size = int(request.GET.get("page_size", settings.PAGE_SIZE))

        try:

            # Get filtered queryset
            object_list = self.get_filtered_query(search, from_date, to_date, ordering)

            # Paginate results
            paginator = PageNumberPagination()
            paginator.page_size = page_size
            result_page = paginator.paginate_queryset(object_list, request)

            # Serialize results
            serializer = ScheduleSerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)

        except ValueError as ve:
            logger.error(f"Date parsing error: {ve}")
            return Response(
                {"error": "Invalid date format. Use mm/dd/yyyy"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return Response(
                {"error": "An error occurred while processing the request."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @staticmethod
    def get_filtered_query(search, from_date, to_date, ordering):
        """
        Helper method to filter schedules based on search, date range, and ordering.
        """
        query = Q()
        if search:
            query = Q(order__project_number__icontains=search)

        if from_date and to_date:
            try:
                from_date_obj = datetime.datetime.strptime(from_date, "%m/%d/%Y")
                to_date_obj = datetime.datetime.strptime(
                    to_date, "%m/%d/%Y"
                ) + datetime.timedelta(days=1)
                query &= Q(schedule_start__range=(from_date_obj, to_date_obj))
            except ValueError as ve:
                raise ValueError("Invalid date format.")

        queryset = Schedule.objects.filter(query).order_by(ordering)
        return queryset


class ScheduleUpdateView(APIView):
    """
    API View to update a Schedule instance.
    - PUT: Update an existing Schedule instance with the provided data.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Update a Schedule instance",
        operation_description="Update an existing Schedule instance with the provided data.",
        manual_parameters=[
            openapi.Parameter(
                "schedule_id",
                openapi.IN_PATH,
                description="The ID of the Schedule to update.",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        request_body=ScheduleSerializer,
        responses={
            200: openapi.Response(
                description="Schedule updated successfully.",
                examples={
                    "application/json": {
                        "message": "Schedule updated successfully.",
                        "data": {
                            "id": 1,
                            "order": 1,
                            "schedule_start": "2023-10-01T10:00:00Z",
                            "created_by": 1,
                        },
                    }
                },
            ),
            400: openapi.Response(
                description="Invalid input data.",
                examples={"application/json": {"error": "Invalid data."}},
            ),
            404: openapi.Response(
                description="Schedule not found.",
                examples={"application/json": {"error": "Not found."}},
            ),
        },
    )
    def put(self, request, schedule_id):
        """
        Update the Schedule instance with the provided data.
        """
        # Retrieve the Schedule instance
        schedule = get_object_or_404(
            Schedule,
            id=schedule_id,
            is_deleted=False,
        )

        # Handle cancellation logic
        if request.data.get("cancel"):
            return Response({"message": "Update canceled."}, status=status.HTTP_200_OK)

        # Validate and update the Schedule instance
        serializer = ScheduleSerializer(schedule, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Schedule updated successfully.", "data": serializer.data},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ScheduleCreateView(APIView):
    """
    View to handle the creation of new Schedules.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Retrieve available orders",
        operation_description="Retrieve a list of orders that are not yet scheduled.",
        responses={
            200: openapi.Response(
                description="List of available orders.",
                examples={
                    "application/json": [
                        {"id": 1, "project_number": "1245 "},
                        {"id": 2, "project_number": "12567"},
                    ]
                },
            ),
        },
    )
    def get(self, request):
        """
        Retrieve available orders that are not yet scheduled.
        """
        orders = (
            Order.objects.filter(archive=False)
            .exclude(id__in=Schedule.objects.all().values_list("order_id", flat=True))
            .order_by("-created_on")
        )

        serialized_orders = [
            {"id": order.id, "project_number": order.project_number} for order in orders
        ]
        return Response(serialized_orders, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Create a new Schedule",
        operation_description="Create a new Schedule entry with the provided data.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["order_id"],
            properties={
                "order_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="The ID of the order to associate with the schedule.",
                ),
                "schedule_start": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_DATETIME,
                    description="The start date and time of the schedule.",
                ),
                "schedule_end": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_DATETIME,
                    description="The end date and time of the schedule.",
                ),
            },
        ),
        responses={
            201: openapi.Response(
                description="Schedule created successfully.",
                examples={
                    "application/json": {
                        "message": "Schedule created successfully.",
                        "schedule": {
                            "id": 1,
                            "order": 1,
                            "schedule_start": "2023-10-01T10:00:00Z",
                            "created_by": 1,
                        },
                    }
                },
            ),
            400: openapi.Response(
                description="Invalid input data.",
                examples={"application/json": {"error": "Invalid data."}},
            ),
        },
    )
    def post(self, request):
        """
        Create a new Schedule entry.
        """
        data = request.data
        serializer = ScheduleSerializer(data=data)

        # Add the current user to the request data for 'created_by'
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(
                {
                    "message": "Schedule created successfully.",
                    "schedule": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ScheduleArchiveView(APIView):
    """
    Archives a schedule if the user is authorized.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Archive a Schedule instance",
        operation_description="Archives a Schedule instance by ID if the user is authorized.",
        manual_parameters=[
            openapi.Parameter(
                "id",
                openapi.IN_PATH,
                description="The ID of the Schedule to archive.",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        responses={
            200: openapi.Response(
                description="Schedule successfully archived.",
                examples={
                    "application/json": {"message": "schedule archived successfully"}
                },
            ),
            403: openapi.Response(
                description="Unauthorized to archive the schedule.",
                examples={
                    "application/json": {
                        "error": "You are not authorized to archive this record."
                    }
                },
            ),
            404: openapi.Response(
                description="Schedule not found.",
                examples={"application/json": {"error": "Not found."}},
            ),
        },
    )
    def post(self, request, id):
        """
        Archive the schedule if authorized.
        """
        schedule = get_object_or_404(
            Schedule,
            id=id,
            is_deleted=False,
        )

        # Check if the requesting user is the creator of the schedule
        if schedule.created_by != request.user:
            return Response(
                {"error": "You are not authorized to archive this record."},
                status=status.HTTP_403_FORBIDDEN,
            )

        schedule.archive = True
        schedule.save()
        return Response(
            {"message": "schedule archived successfully"},
            status=status.HTTP_200_OK,
        )


class ScheduleDeleteView(APIView):
    """
    API view to delete a Schedule instance.
    - DELETE: Deletes a Schedule instance by ID if the user is authorized.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Delete a Schedule instance",
        operation_description="Deletes a Schedule instance by ID if the user is authorized.",
        manual_parameters=[
            openapi.Parameter(
                "schedule_id",
                openapi.IN_PATH,
                description="The ID of the Schedule to delete.",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        responses={
            204: openapi.Response(
                description="Schedule successfully deleted.",
                examples={
                    "application/json": {"message": "Schedule successfully deleted."}
                },
            ),
            403: openapi.Response(
                description="Unauthorized to delete the schedule.",
                examples={
                    "application/json": {
                        "error": "You are not authorized to delete this record."
                    }
                },
            ),
            404: openapi.Response(
                description="Schedule not found.",
                examples={"application/json": {"error": "Not found."}},
            ),
        },
    )
    def delete(self, request, schedule_id):
        """
        Delete a Schedule instance if the user is authorized.
        """
        this_schedule = get_object_or_404(
            Schedule,
            id=schedule_id,
            is_deleted=False,
        )

        # Check if the user is authorized to delete the schedule
        if this_schedule.created_by != request.user:
            return Response(
                {"error": "You are not authorized to delete this record."},
                status=status.HTTP_403_FORBIDDEN,
            )

        this_schedule.soft_delete()

        return Response(
            {"message": "Schedule successfully deleted."},
            status=status.HTTP_204_NO_CONTENT,
        )


class ScheduleTechListView(APIView):
    """
    API view to retrieve a list of all technicians.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Retrieve all technicians",
        operation_description="Retrieve a list of technicians.",
        responses={
            200: openapi.Response(
                description="Paginated list of technicians.",
            ),
            400: openapi.Response(
                description="Invalid input parameters.",
                examples={
                    "application/json": {"error": "Invalid date format. Use mm/dd/yyyy"}
                },
            ),
            500: openapi.Response(
                description="Server error.",
                examples={
                    "application/json": {
                        "error": "An error occurred while processing the request."
                    }
                },
            ),
        },
    )
    def get(self, request):
        """
        Retrieve all technicians
        """

        try:
            # Serialize results
            results = Profile.objects.filter(Q(user_type=1) | Q(user_type=3)).order_by(
                "-created_on"
            )
            serializer = ProfileSerializer(results, many=True)
            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return Response(
                {"error": "An error occurred while processing the request."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ScheduleTechDetailView(APIView):
    """
    API view to retrieve details of technician associated with a schedule.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Retrieve technician details for a schedule",
        operation_description="Retrieve details of technicians associated with a specific schedule.",
        manual_parameters=[
            openapi.Parameter(
                "schedule_id",
                openapi.IN_PATH,
                description="The ID of the schedule to retrieve technician details for.",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        responses={
            200: openapi.Response(
                description="Technician details.",
            ),
            404: openapi.Response(
                description="Technician not found.",
                examples={"application/json": {"error": "Not found."}},
            ),
        },
    )
    def get(self, request, schedule_id):
        """
        Retrieve details of technicians associated with the specified schedule.
        """
        schedule_techs = ScheduleTech.objects.filter(
            schedule_id=schedule_id,
            is_deleted=False,
            archive=False,
        )
        if not schedule_techs.exists():
            return Response(
                {"error": "Schedule Techs not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = ScheduleTechSerializer(schedule_techs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ScheduleTechUpdateView(APIView):
    """
    API view to update a specific technician associated with a schedule.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Update a technician for a schedule",
        operation_description="Update an existing technician associated with a specific schedule.",
        request_body=ScheduleTechSerializer,
        responses={
            200: openapi.Response(
                description="Technician updated successfully.",
            ),
            400: openapi.Response(
                description="Invalid input data.",
            ),
            404: openapi.Response(
                description="Technician not found.",
            ),
        },
    )
    def put(self, request, schedule_id, tech_id):
        """
        Update the technician associated with the specified schedule.
        """

        schedule_tech = get_object_or_404(
            ScheduleTech, assigned_to=tech_id, schedule_id=schedule_id
        )
        serializer = ScheduleTechSerializer(
            schedule_tech, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Schedule Tech updated successfully.",
                    "schedule_tech": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ScheduleTechDeleteView(APIView):
    """
    API view to delete a technician associated with a schedule.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Delete a technician for a schedule",
        operation_description="Delete a technician associated with a specific schedule.",
        manual_parameters=[
            openapi.Parameter(
                "schedule_id",
                openapi.IN_PATH,
                description="The ID of the schedule.",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
            openapi.Parameter(
                "tech_id",
                openapi.IN_PATH,
                description="The ID of the technician to delete.",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        responses={
            204: openapi.Response(
                description="Technician deleted from schedule successfully.",
            ),
            404: openapi.Response(
                description="Technician not found.",
            ),
        },
    )
    def delete(self, request, schedule_id, tech_id):
        """
        Delete the technician associated with the specified schedule.
        """
        schedule_tech = get_object_or_404(
            ScheduleTech, assigned_to=tech_id, schedule_id=schedule_id
        )

        schedule_tech.delete()
        return Response(
            {"message": "Technician deleted from schedule successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )
