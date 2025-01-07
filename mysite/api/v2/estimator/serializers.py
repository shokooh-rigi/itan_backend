from rest_framework import serializers

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
    service = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Service.objects.all()
    )  # Allow passing a list of service IDs
    customer_name = serializers.SerializerMethodField()
    project_name = serializers.SerializerMethodField()

    class Meta:
        model = Estimate
        fields = [
            'id',
            'bfm',
            'customer',
            'customer_name',
            'project',
            'project_name'
            'engineer',
            'service',
            'note',
            'due_date',
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

    def to_representation(self, instance):
        """Customize the serialized output."""
        representation = super().to_representation(instance)

        # Remove customer_name and project_name for non-GET requests
        request = self.context.get('request')
        if request and request.method not in ['GET']:
            representation.pop('customer_name', None)
            representation.pop('project_name', None)

        return representation


class EstimateDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstimateDetails
        fields = '__all__'


class EstimateEquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstimateEquipment
        fields = ['equipment', 'quantity', 'price_override']


class EstimateHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EstimateHistory
        fields = '__all__'

