from rest_framework import serializers

from mysite.api.v2.bid.serializers import BidSerializer
from mysite.api.v2.core.serializers import PersonSerializer, ProjectSerializer, ServiceSerializer, EquipmentSerializer
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


class EstimateEquipmentSerializer(serializers.ModelSerializer):
    equipment = EquipmentSerializer()
    class Meta:
        model = EstimateEquipment
        fields = ['equipment', 'quantity', 'price_override']

    def get_service_id(self, obj):
        # Ensure `obj.equipment` exists to avoid errors
        if obj.equipment and obj.equipment.service:
            return obj.equipment.service.id
        return None
    

class EstimateDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstimateDetails
        fields = "__all__"


class EstimateSerializer(serializers.ModelSerializer):
    """Serializer for the Estimate model."""
    estimate_id = serializers.SerializerMethodField()
    bfm = BidSerializer(read_only=True)
    customer = PersonSerializer()
    company_name = serializers.SerializerMethodField(read_only=True)
    project = ProjectSerializer()
    engineer = PersonSerializer()
    pre_demo = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    estimate_equipments = EstimateEquipmentSerializer(many=True, source='estimateequipment_set')
    estimate_details = EstimateDetailsSerializer(source='estimatedetails')
    sub_total = serializers.SerializerMethodField()
    control_system_calculated = serializers.SerializerMethodField()
    hours_calculated = serializers.SerializerMethodField()
    predemo_calculated = serializers.SerializerMethodField()
    dalt_calculated = serializers.SerializerMethodField()
    total_calculated = serializers.SerializerMethodField()

    class Meta:
        model = Estimate
        fields = "__all__"

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
    
    def get_estimate_id(self, obj):
        return obj.estimate_id

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
    
    def get_sub_total(self, obj):
        return obj.sub_total
    
    def get_control_system_calculated(self, obj):
        return obj.control_system_calculated
    
    def get_hours_calculated(self, obj):
        return obj.hours_calculated
    
    def get_predemo_calculated(self, obj):
        return obj.predemo_calculated
    
    def get_dalt_calculated(self, obj):
        return obj.dalt_calculated
    
    def get_total_calculated(self, obj):
        return obj.total_calculated

    def get_company_name(self, obj):
        if obj.customer and getattr(obj.customer, 'company', None):
            return obj.customer.company.name
        return None


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


class EstimateHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EstimateHistory
        fields = '__all__'

