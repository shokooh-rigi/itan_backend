from rest_framework import serializers

from mysite.equipments.models import Equipment


class EquipmentSerializer(serializers.ModelSerializer):
    service_name = serializers.SerializerMethodField()

    def get_service_name(self, obj):
        return obj.service.name if obj.service else None

    class Meta:
        model = Equipment
        fields = "__all__"
