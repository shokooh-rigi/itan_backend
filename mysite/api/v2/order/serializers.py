from rest_framework import serializers
from rest_framework.serializers import (
    Serializer,
    BooleanField,
    ListField,
    FileField,
    CharField,
)

from mysite.api.v2.core.serializers import PersonSerializer
from mysite.api.v2.proposal.serializers import ProposalSerializer
from mysite.order.models import (
    Order,
    TechLabel,
    ChangeOrderService,
    ChangeOrder,
    TechLabelExtraFields,
    ControlSystem,
    ControlSystemManufacturer,
)
from mysite.proposal.models import Proposal


class ControlSystemManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ControlSystemManufacturer
        fields = "__all__"


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
    documentation = serializers.FileField(required=False)

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

    def create(self, validated_data):
        # Pop the manufacturer_id and fetch the related object
        manufacturer_id = validated_data.pop("manufacturer_id")
        validated_data["manufacturer"] = ControlSystemManufacturer.objects.get(
            id=manufacturer_id
        )
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Pop the manufacturer_id and fetch the related object if provided
        manufacturer_id = validated_data.pop("manufacturer_id", None)
        if manufacturer_id:
            validated_data["manufacturer"] = ControlSystemManufacturer.objects.get(
                id=manufacturer_id
            )
            return super().update(instance, validated_data)
        else:
            # If manufacturer_id is not provided, just update the instance
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance


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
    change_orders_total = serializers.ReadOnlyField()
    predemo_total = serializers.SerializerMethodField(read_only=True)
    dalt_total = serializers.SerializerMethodField(read_only=True)
    final_total = serializers.SerializerMethodField(read_only=True)
    total = serializers.SerializerMethodField(read_only=True)
    has_invoice = serializers.BooleanField(read_only=True)

    class Meta:
        model = Order
        fields = "__all__"

    def create(self, validated_data):
        """Override create method to link proposal using proposal_id"""
        proposal_id = validated_data.pop("proposal_id", None)
        if not proposal_id:
            raise serializers.ValidationError(
                {"proposal_id": "This field is required."}
            )

        try:
            proposal = Proposal.objects.get(id=proposal_id)
        except Proposal.DoesNotExist:
            raise serializers.ValidationError({"proposal_id": "Invalid proposal_id."})

        validated_data["proposal"] = proposal
        return super().create(validated_data)

    def to_representation(self, instance):
        """Customize response for create requests"""
        representation = super().to_representation(instance)
        request = self.context.get("request")

        if request and request.method == "POST":
            return {
                "architect_name": representation.get("architect_name", ""),
                "po_number": representation.get("po_number"),
                "date_po_received": representation.get("date_po_received"),
                "final_offset": representation.get("final_offset"),
                "note": representation.get("note"),
                "estimated_date_of_project": representation.get(
                    "estimated_date_of_project"
                ),
                "proposal_id": instance.proposal.id if instance.proposal else None,
            }

        return representation

    def get_predemo_total(self, obj):
        return obj.predemo_total

    def get_dalt_total(self, obj):
        return obj.dalt_total

    def get_final_total(self, obj):
        return obj.final_total

    def get_total(self, obj):
        return obj.total

    def get_has_invoice(self, obj):
        """
        Check if the order has an associated invoice.
        """
        return obj.has_invoice


class ChangeOrderServiceSerializer(serializers.ModelSerializer):
    """
    Serializer for ChangeOrderService.
    """

    class Meta:
        model = ChangeOrderService
        exclude = ["change_order"]


class ChangeOrderSerializer(serializers.ModelSerializer):
    """
    Serializer for ChangeOrder with nested services.
    """

    services = ChangeOrderServiceSerializer(source="changeorderservice_set", many=True)

    class Meta:
        model = ChangeOrder
        exclude = ["order"]

    def create(self, validated_data):
        """
        Create a ChangeOrder along with associated services.
        """
        services_data = validated_data.pop("changeorderservice_set", [])
        change_order = ChangeOrder.objects.create(**validated_data)
        for service_data in services_data:
            ChangeOrderService.objects.create(change_order=change_order, **service_data)
        return change_order

    def update(self, instance, validated_data):
        """
        Update a ChangeOrder and its associated services.
        """
        services_data = validated_data.pop("changeorderservice_set", [])
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
        fields = ["id", "title", "content"]


class TechLabelSerializer(serializers.ModelSerializer):
    """
    Serializer for TechLabel model. Supports create or update based on order_id.
    """

    extra_fields = TechLabelExtraFieldsSerializer(
        many=True,
        required=False,
        source="techlabelextrafields_set",
    )
    order_id = serializers.IntegerField(write_only=True)
    order = OrderSerializer(read_only=True)

    class Meta:
        model = TechLabel
        fields = [
            "id",
            "order_id",
            "label_model",
            "detailed_drawing",
            "schedule_drawing",
            "mechanical_drawing",
            "tech_test_sheets",
            "point_of_contact_name",
            "point_of_contact_cell_phone",
            "point_of_contact_office_phone",
            "schedule_date",
            "tech_notes",
            "extra_fields",
            "created_on",
            "order",
        ]
        extra_kwargs = {
            "order": {"read_only": True},
        }

    def validate_order_id(self, value):
        """
        Ensure the order_id is valid and exists in the database.
        """
        if not Order.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid order_id: Order does not exist.")
        return value

    def create(self, validated_data):
        """
        Create a new TechLabel instance or update an existing one based on order_id.
        """
        extra_fields_data = validated_data.pop("techlabelextrafields_set", [])
        order = Order.objects.get(
            id=validated_data.pop("order_id")
        )  # Fetch order object

        # Check if TechLabel already exists for this order
        tech_label, created = TechLabel.objects.update_or_create(
            order=order, defaults=validated_data
        )

        # Delete old extra fields and add new ones
        tech_label.techlabelextrafields_set.all().delete()
        for extra_data in extra_fields_data:
            TechLabelExtraFields.objects.create(tech_label=tech_label, **extra_data)

        return tech_label


class OrderControlSystemSerializer(serializers.ModelSerializer):
    # Use this field to handle ForeignKey to ControlSystem
    control_system = serializers.PrimaryKeyRelatedField(
        queryset=ControlSystem.objects.all(),
        required=False
    )

    class Meta:
        model = Order
        fields = ["control_system"]


class EquipmentSubmittalSerializer(Serializer):
    """Serializer for equipment submittal file uploads"""

    equipment_submittal_clear = BooleanField(
        required=False, help_text="If true, clears the equipment submittal."
    )
    equipment_submittal = ListField(
        child=FileField(), required=False, help_text="List of uploaded files."
    )


class GeneralNotesSerializer(serializers.ModelSerializer):
    """Serializer for saving and finalizing general notes"""

    class Meta:
        model = Order
        fields = [
            "general_notes_and_comments",
            "general_notes_and_comments_finalize"
        ]



class FieldDrawingUploadSerializer(Serializer):
    colored_drawing = FileField(required=False, allow_null=True)
    report_colored_drawing = FileField(required=False, allow_null=True)
    colored_drawing_finalize = BooleanField()
