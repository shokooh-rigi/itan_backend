from rest_framework import serializers
from mysite.scheduler.models import Schedule, Maintenance, ScheduleTech


class ScheduleSerializer(serializers.ModelSerializer):
    """
    Serializer for the Schedule model.
    """

    class Meta:
        model = Schedule
        fields = '__all__'
        read_only_fields = ['created_by', 'created_on']


class MaintenanceSerializer(serializers.ModelSerializer):
    """
    Serializer for the Maintenance model.
    """

    class Meta:
        model = Maintenance
        fields = '__all__'
        read_only_fields = ['created_by', 'created_on']


class ScheduleTechSerializer(serializers.ModelSerializer):
    """
    Serializer for the ScheduleTech model.
    """

    class Meta:
        model = ScheduleTech
        fields = '__all__'
        read_only_fields = ['created_on']
