from rest_framework import serializers

from mysite.core.models import ContactInfo
from mysite.gi.models import AccountSummary

class AccountSummaryCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating Account Summaries.

    - Handles validation and dynamic default values for fields like `created_by` and `customer`.
    """
    customer = serializers.PrimaryKeyRelatedField(
        queryset=ContactInfo.objects.all(),
        required=False
    )
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())

    fields = [
        'customer',
        'attention',
        'created_by',
    ]

    def validate_customer(self, value):
        """
        Validate or fetch the customer based on custom logic.
        """
        if not value:
            return ContactInfo.objects.filter(company_type__name__iexact='mechanical contractor').first()
        return value

    class Meta:
        model = AccountSummary
        fields = [
            'customer',
            'attention',
            'created_by',
        ]


# Serializer for AccountSummary
class AccountSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountSummary
        fields = "__all__"
