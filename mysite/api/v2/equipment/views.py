from rest_framework.generics import CreateAPIView, ListAPIView, UpdateAPIView, DestroyAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from mysite.dbmanagement.models import Equipment
from mysite.equipments.api.serializers import EquipmentSerializer


class EquipmentListView(ListAPIView):
    """
    API endpoint to list Equipment objects with pagination.
    """
    serializer_class = EquipmentSerializer
    queryset = Equipment.objects.filter(is_deleted=False)
    pagination_class = PageNumberPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        ordering = self.request.query_params.get('ordering', 'created_on')
        return self.queryset.order_by(ordering)


class EquipmentCreateView(CreateAPIView):
    serializer_class = EquipmentSerializer
    queryset = Equipment.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated]


class EquipmentUpdateView(UpdateAPIView):
    """
    API endpoint to update a Equipment object.
    """
    serializer_class = EquipmentSerializer
    queryset = Equipment.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated]


class EquipmentDeleteView(DestroyAPIView):
    queryset = Equipment.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated]

    def perform_destroy(self, instance):
        instance.soft_delete()
