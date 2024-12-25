import datetime
import logging

from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from mysite import settings
from mysite.order.models import Order
from mysite.scheduler.models import Schedule
from .serializers import ScheduleSerializer

logger = logging.getLogger(__name__)


class ScheduleListView(APIView):
    """
    API view to retrieve a list of schedules with filtering and pagination options.
    """

    permission_classes = [IsAuthenticated]

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
            return Response({"error": "Invalid date format. Use mm/dd/yyyy"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return Response({"error": "An error occurred while processing the request."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    def get_filtered_query(search, from_date, to_date, ordering):
        """
        Helper method to filter schedules based on search, date range, and ordering.
        """
        query = Q()
        if search:
            query = Q(order__project_number__icontains=search) | \
                    Q(assigned_to_contractor__name__icontains=search) | \
                    Q(assigned_to_contractor__company__name__icontains=search)

        if from_date and to_date:
            try:
                from_date_obj = datetime.datetime.strptime(from_date, "%m/%d/%Y")
                to_date_obj = datetime.datetime.strptime(to_date, "%m/%d/%Y") + datetime.timedelta(days=1)
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
            return Response(
                {"message": "Update canceled."}, status=status.HTTP_200_OK
            )

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

    def get(self, request):
        """
        Retrieve available orders that are not yet scheduled.
        """
        orders = Order.objects.filter(archive=False).exclude(
            id__in=Schedule.objects.all().values_list('order_id', flat=True)
        ).order_by('-created_on')

        # You may serialize the data if required, e.g., for a React frontend
        serialized_orders = [{"id": order.id, "name": order.name} for order in orders]
        return Response(serialized_orders, status=status.HTTP_200_OK)

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
                {"message": "Schedule created successfully.", "schedule": serializer.data},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ScheduleArchiveView(APIView):
    """
    Archives a schedule if the user is authorized.
    """

    permission_classes = [IsAuthenticated]

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
