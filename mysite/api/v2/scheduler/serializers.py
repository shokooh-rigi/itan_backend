from rest_framework import serializers
from mysite.api.v2.order.serializers import OrderSerializer
from mysite.order.models import Order
from mysite.scheduler.models import Schedule, Maintenance, ScheduleTech


class ScheduleTechSerializer(serializers.ModelSerializer):
    """
    Serializer for the ScheduleTech model.
    """

    class Meta:
        model = ScheduleTech
        fields = "__all__"
        read_only_fields = [
            "created_on",
            "updated_at",
        ]


class ScheduleOrderSerializer(serializers.ModelSerializer):
    """
    Serializer for the ScheduleOrder model.
    """

    class Meta:
        model = Order
        fields = ["id", "project_number"]


class ScheduleSerializer(serializers.ModelSerializer):
    """
    Serializer for the Schedule model.
    """

    schedule_tech = ScheduleTechSerializer(read_only=True, many=True)
    order = ScheduleOrderSerializer(read_only=True)
    order_id = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all(),
        source="order",
        write_only=True,
    )

    class Meta:
        model = Schedule
        fields = "__all__"
        read_only_fields = ["created_by", "created_on"]


class MaintenanceSerializer(serializers.ModelSerializer):
    """
    Serializer for the Maintenance model.
    """

    class Meta:
        model = Maintenance
        fields = "__all__"
        read_only_fields = ["created_by", "created_on"]
