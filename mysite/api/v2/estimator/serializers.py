from rest_framework import serializers

from mysite.bidfilemgm.models import BidFile
from mysite.estimator.models import Estimate, EstimateDetails


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
    class Meta:
        model = Estimate
        fields = '__all__'


class EstimateDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstimateDetails
        fields = '__all__'


class BidFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BidFile
        fields = '__all__'
