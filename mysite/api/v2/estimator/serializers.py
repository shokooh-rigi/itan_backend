from rest_framework import serializers

from mysite.api.v2.bid.serializers import BidFileSerializer
from mysite.core.models import Service
from mysite.equipments.models import Equipment
from mysite.estimator.models import Estimate, EstimateDetails, EstimateEquipment, EstimateHistory


class EmailSerializer(serializers.Serializer):
    """Serializer for validating email-related data for sending emails.

    This serializer is used to validate and serialize the data required
    for sending emails, including recipient details and email content.

    Attributes:
        to_email (List[str]): A list of recipient email addresses. Must contain valid emails.
        cc (List[str]): A list of CC email addresses. Optional, defaults to an empty list.
        email_id (int): The ID of the email record. This is used for tracking or referencing the email.
        subject (str): The subject line of the email, with a maximum length of 255 characters.

    Raises:
        ValidationError: If any of the email addresses are invalid or if the required fields are missing.
    """

    to_email = serializers.ListField(
        child=serializers.EmailField(),  # Validates each email
        allow_empty=False
    )
    cc = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        default=[]
    )
    email_id = serializers.IntegerField()
    subject = serializers.CharField(max_length=255)


class EstimateSerializer(serializers.ModelSerializer):
    """Serializer for the Estimate model."""
    bfm = BidFileSerializer(read_only=True)
    service = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Service.objects.all()
    )  # Allow passing a list of service IDs
    customer_name = serializers.SerializerMethodField()
    project_name = serializers.SerializerMethodField()
    engineer_name= serializers.SerializerMethodField(read_only=True)
    service_names = serializers.SerializerMethodField(read_only=True)
    pre_demo = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Estimate
        fields = [
            'id',
            'bfm',
            'customer',
            'customer_name',
            'project',
            'project_name',
            'engineer',
            'engineer_name',
            'service',
            'service_names',
            'note',
            'due_date',
            'pre_demo',
            'total_amount',
            'drawing_date',
        ]

    def create(self, validated_data):
        services = validated_data.pop('service', [])
        estimate = Estimate.objects.create(**validated_data)
        estimate.service.set(services)  # Associate services with the estimate
        return estimate

    def update(self, instance, validated_data):
        services = validated_data.pop('service', [])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.service.set(services)  # Update associated services
        instance.save()
        return instance

    def get_customer_name(self, obj):
        """Get the name of the customer."""
        return obj.customer.name if obj.customer else None

    def get_project_name(self, obj):
        """Get the name of the project."""
        return obj.project.name if obj.project else None

    def get_engineer_name(self, obj):
        """Get the name of the engineer."""
        return obj.engineer.name if obj.engineer else None

    def get_service_names(self, obj):
        """Get name about associated services."""
        return [{"id": service.id, "name": service.name} for service in obj.service.all()]

    def get_pre_demo(self, obj):
        """Get pre_demo from the related EstimateDetail."""
        estimate_detail = getattr(obj, 'estimatedetails', None)
        return estimate_detail.pre_demo if estimate_detail else None

    def get_total_amount(self, obj):
        """Calculate the total amount based on related EstimateEquipment."""
        estimate_equipments = EstimateEquipment.objects.filter(estimate=obj, flag=True)
        total = sum(
            float(estimate_equipment.price_override or estimate_equipment.equipment.price) * estimate_equipment.quantity
            for estimate_equipment in estimate_equipments
        )
        return total


    def to_representation(self, instance):
        """Customize the serialized output."""
        representation = super().to_representation(instance)

        # Remove customer_name and project_name and engineer_name for non-GET requests
        request = self.context.get('request')
        if request and request.method not in ['GET']:
            representation.pop('customer_name', None)
            representation.pop('project_name', None)
            representation.pop('engineer_name', None)
            representation.pop('service_names', None)
            representation.pop('pre_demo', None)
            representation.pop('total_amount', None)

        return representation


class EstimateDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstimateDetails
        fields = '__all__'


class EstimateEquipmentSerializer(serializers.ModelSerializer):
    service_id = serializers.SerializerMethodField()
    class Meta:
        model = EstimateEquipment
        fields = ['equipment', 'quantity', 'price_override', 'service_id']

    def get_service_id(self, obj):
        # Ensure `obj.equipment` exists to avoid errors
        if obj.equipment and obj.equipment.service:
            return obj.equipment.service.id
        return None


class EstimateHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EstimateHistory
        fields = '__all__'

