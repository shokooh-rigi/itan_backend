from rest_framework import serializers

from mysite.api.v2.core.serializers import PersonSerializer
from mysite.api.v2.proposal.serializers import ProposalSerializer
from mysite.order.models import Order, TechLabel, ChangeOrderService, ChangeOrder, TechLabelExtraFields, ControlSystem, \
    ControlSystemManufacturer


class ControlSystemManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ControlSystemManufacturer
        fields = '__all__'


class ControlSystemSerializer(serializers.ModelSerializer):
    """
    Serializer for the ControlSystem model.
    """
    manufacturer = ControlSystemManufacturerSerializer(read_only=True)

    class Meta:
        model = ControlSystem
        fields = [
            "id",
            "version_number",
            "control_file_url",
            "documentation",
            "manufacturer",
        ]


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for handling Order creation and updates.

    - Validates and processes Order data.
    """
    proposal = ProposalSerializer(read_only=True)
    architect_name = PersonSerializer(read_only=True)
    control_system = ControlSystemSerializer(read_only=True)

    class Meta:
        model = Order

    fields = [
        "id",
        "project_number",
        "po_number",
        "date_po_received",
        "estimated_date_of_project",
        "completion_percentage",
        "fully_settled",
        "archive",
        "state",
        "start_date",
        "end_date",
        "created_on",
    ]


class ChangeOrderServiceSerializer(serializers.ModelSerializer):
    """
    Serializer for ChangeOrderService.
    """
    class Meta:
        model = ChangeOrderService
        fields = ['amount', 'description']


class ChangeOrderSerializer(serializers.ModelSerializer):
    """
    Serializer for ChangeOrder with nested services.
    """
    services = ChangeOrderServiceSerializer(many=True)

    class Meta:
        model = ChangeOrder
        fields = ['order', 'co_number', 'confirmed', 'date', 'services']

    def create(self, validated_data):
        """
        Create a ChangeOrder along with associated services.
        """
        services_data = validated_data.pop('services')
        change_order = ChangeOrder.objects.create(**validated_data)
        for service_data in services_data:
            ChangeOrderService.objects.create(change_order=change_order, **service_data)
        return change_order

    def update(self, instance, validated_data):
        """
        Update a ChangeOrder and its associated services.
        """
        services_data = validated_data.pop('services', [])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update or create related services
        instance.changeorderservice_set.all().delete()  # Delete old services
        for service_data in services_data:
            ChangeOrderService.objects.create(change_order=instance, **service_data)

        return instance


class TechLabelExtraFieldsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechLabelExtraFields
        fields = ['title', 'content']


class TechLabelSerializer(serializers.ModelSerializer):
    extra_fields = TechLabelExtraFieldsSerializer(many=True, required=False)

    class Meta:
        model = TechLabel
        fields = ['id', 'order', 'extra_fields']


class OrderControlSystemSerializer(serializers.ModelSerializer):
    # Use this field to handle ForeignKey to ControlSystem
    control_system = serializers.PrimaryKeyRelatedField(
        queryset=ControlSystem.objects.all(),
        required=True
    )

    class Meta:
        model = Order
        fields = ['control_system']
