from rest_framework.generics import CreateAPIView, ListAPIView, UpdateAPIView, DestroyAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from mysite.api.v2.equipment.serializers import EquipmentSerializer
from mysite.equipments.models import Equipment


class EquipmentListView(ListAPIView):
    serializer_class = EquipmentSerializer
    pagination_class = PageNumberPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        ordering = self.request.query_params.get('ordering', 'created_on')
        return Equipment.objects.filter(is_deleted=False).order_by(ordering)


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


class EquipmentDetailView(ListAPIView):
    """
    API endpoint to retrieve a single Equipment object.
    """
    serializer_class = EquipmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        equipment_id = self.kwargs['pk']
        return Equipment.objects.filter(
            id=equipment_id,
            is_deleted=False,
        )
