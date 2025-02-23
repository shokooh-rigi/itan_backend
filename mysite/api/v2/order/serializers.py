from rest_framework import serializers

from mysite.api.v2.core.serializers import PersonSerializer
from mysite.api.v2.proposal.serializers import ProposalSerializer
from mysite.order.models import Order, TechLabel, ChangeOrderService, ChangeOrder, TechLabelExtraFields, ControlSystem, \
    ControlSystemManufacturer
from mysite.proposal.models import Proposal


class ControlSystemManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ControlSystemManufacturer
        fields = '__all__'


class ControlSystemSerializer(serializers.ModelSerializer):
    """
    Serializer for the ControlSystem model.
    """
    manufacturer = ControlSystemManufacturerSerializer(read_only=True)
    manufacturer_id = serializers.PrimaryKeyRelatedField(
        queryset=ControlSystemManufacturer.objects.all(),
        write_only=True,
        required=True,
    )
    documentation = serializers.FileField(write_only=True)


    class Meta:
        model = ControlSystem
        fields = [
            "id",
            "version_number",
            "os",
            "release_date",
            "control_file_url",
            "documentation",
            "manufacturer_id",
            "manufacturer",
        ]

        extra_kwargs = {
            "manufacturer": {"required": False},
        }

    def create(self, validated_data):
        manufacturer = validated_data.pop("manufacturer_id")
        control_system = ControlSystem.objects.create(manufacturer=manufacturer, **validated_data)
        return control_system

    def to_representation(self, instance):
        """
        Ensures 'manufacturer' is only included in the response, not in requests.
        """
        data = super().to_representation(instance)
        request = self.context.get("request")
        if request and request.method in ["POST", "PUT", "PATCH"]:
            data.pop("manufacturer", None)
        return data

class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for handling Order creation and updates.

    - Validates and processes Order data.
    """
    proposal = ProposalSerializer(read_only=True)
    proposal_id = serializers.IntegerField(write_only=True)
    architect_name = PersonSerializer(read_only=True)
    control_system = ControlSystemSerializer(read_only=True)
    project_number = serializers.CharField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "proposal",
            "proposal_id",
            "architect_name",
            "id",
            "project_number",
            "po_number",
            "date_po_received",
            "final_offset",
            "note",
            "estimated_date_of_project",
            "completion_percentage",
            "fully_settled",
            "archive",
            "state",
            "start_date",
            "end_date",
            "created_on",
            "control_system",
        ]

    def create(self, validated_data):
        """Override create method to link proposal using proposal_id"""
        proposal_id = validated_data.pop("proposal_id", None)
        if not proposal_id:
            raise serializers.ValidationError({"proposal_id": "This field is required."})

        try:
            proposal = Proposal.objects.get(id=proposal_id)
        except Proposal.DoesNotExist:
            raise serializers.ValidationError({"proposal_id": "Invalid proposal_id."})

        validated_data["proposal"] = proposal
        return super().create(validated_data)

    def to_representation(self, instance):
        """Customize response for create requests"""
        representation = super().to_representation(instance)
        request = self.context.get('request')

        if request and request.method == 'POST':
            return {
                "architect_name": representation.get("architect_name", ''),
                "po_number": representation.get("po_number"),
                "date_po_received": representation.get("date_po_received"),
                "final_offset": representation.get("final_offset"),
                "note": representation.get("note"),
                "estimated_date_of_project": representation.get("estimated_date_of_project"),
                "proposal_id": instance.proposal.id if instance.proposal else None,
            }

        return representation


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
