from rest_framework import serializers

from mysite.core.models import ContactInfo
from mysite.gi.models import Invoice, InvoiceHistory, AccountSummary


class InvoiceSerializer(serializers.ModelSerializer):
    """
    Serializer for handling Invoice creation and updates.

    - Validates and processes invoice data.
    - Integrates with the service layer to handle related business logic.
    """
    class Meta:
        model = Invoice
        fields = [
            'order',
            'date_started',
            'date_completed',
            'terms',
            'description',
            'percent_of_performance_completed',
            'attention',
            'edited_on',
            'created_by',
        ]


class InvoiceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceHistory
        fields = [
            'total_invoiced',
            'total_paid',
            'balance_due',
            'pdf_filename',
        ]


class EmailSerializer(serializers.Serializer):
    invoice_id = serializers.IntegerField()
    to_email = serializers.EmailField()
    cc = serializers.CharField(required=False)
    subject = serializers.CharField(max_length=255)

    def validate(self, data):
        if not data.get('to_email'):
            raise serializers.ValidationError("Recipient email is required.")
        return data


class InvoicePaymentSerializer(serializers.Serializer):
    """
    Serializer to validate and serialize invoice payment data.

    Fields:
        - created_by (HiddenField): The user who created the payment record
          (auto-assigned to the current user).
        - invoice (PrimaryKeyRelatedField): Reference to the invoice being paid.
        - amount_paid (DecimalField): The amount paid for the invoice.
        - payment_method (ChoiceField): The method of payment (Credit Card,
          Cash, Bank Transfer).
        - fields (list): List of required fields for the serializer.

    Example Usage:
        serializer = InvoicePaymentSerializer(data=request.data)
        if serializer.is_valid():
            # Process the data
    """
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    invoice = serializers.PrimaryKeyRelatedField(queryset=Invoice.objects.all())
    amount_paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_method = serializers.ChoiceField(choices=['Credit Card', 'Cash', 'Bank Transfer'])
    fields = [
        'invoice',
        'amount',
        'payment_date',
        'payment_no',
        'created_by',
    ]


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
