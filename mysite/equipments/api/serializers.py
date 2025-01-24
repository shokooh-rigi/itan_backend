from rest_framework import serializers

from ..models import Equipment
from mysite.sheetcreator.models import DataSheet

class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = '__all__'  # This will serialize all fields


class DataSheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSheet
        fields = '__all__'
