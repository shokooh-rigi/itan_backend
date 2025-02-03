from django.db.models import Q
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from mysite import settings
from mysite.scheduler.models import ScheduleTech
from mysite.settlement.models import Settlement
from .serializers import SettlementSerializer


class SettlementPagination(PageNumberPagination):
    """
    Custom pagination for Settlement API.
    """
    page_size = settings.PAGE_SIZE
    page_size_query_param = 'paginate_by'
    max_page_size = 100


class SettlementListView(ListAPIView):
    """
    API endpoint to list settlements with search, pagination, and ordering.
    """
    serializer_class = SettlementSerializer
    queryset = Settlement.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = SettlementPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['contractor__first_name', 'contractor__last_name']
    ordering = ['-created_on']

    def get_queryset(self):
        search_query = self.request.query_params.get("search", "")
        queryset = Settlement.objects.filter(
            Q(contractor__first_name__icontains=search_query) |
            Q(contractor__last_name__icontains=search_query)
        ).order_by(self.request.query_params.get("ordering", "-created_on"))

        return queryset


class SettlementCreateView(CreateAPIView):
    """
    API endpoint to create a new Settlement object.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = SettlementSerializer
    queryset = Settlement.objects.all()


class SettlementDeleteView(APIView):
    """
    API endpoint to soft delete a settlement by marking it as deleted and updating related objects.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            settlement = Settlement.objects.get(pk=pk)
        except Settlement.DoesNotExist:
            raise NotFound("Settlement not found")

        for settled_schedule in settlement.settledschedule_set.all():
            settled_schedule.schedule.order.fully_settled = False
            settled_schedule.schedule.order.save()
            try:
                schedule_tech = ScheduleTech.objects.get(
                    schedule=settled_schedule.schedule,
                    assigned_to_contractor=settlement.contractor,
                )
                schedule_tech.settlement = False
                schedule_tech.save()
            except ScheduleTech.DoesNotExist:
                continue
        for settled_maintenance in settlement.settledmaintenances_set.all():
            settled_maintenance.maintenance.settlement = False
            settled_maintenance.maintenance.save()

        settlement.soft_delete()
        return Response(
            {"detail": "Settlement successfully deleted"},
            status=status.HTTP_204_NO_CONTENT
        )


