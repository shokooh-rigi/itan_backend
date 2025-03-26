from rest_framework import serializers

from mysite.api.v2.core.serializers import (
    AddressSerializer,
    ContactInfoSerializer,
    PersonSerializer,
)
from mysite.core.models import Company, ContactInfo
from mysite.gi.models import AccountSummary, Invoice


class AccountSummaryCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating Account Summaries.

    - Handles validation and dynamic default values for fields like `created_by` and `customer`.
    """

    customer = serializers.PrimaryKeyRelatedField(
        queryset=ContactInfo.objects.all(), required=False
    )
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())

    fields = [
        "customer",
        "attention",
        "created_by",
    ]

    def validate_customer(self, value):
        """
        Validate or fetch the customer based on custom logic.
        """
        if not value:
            return ContactInfo.objects.filter(
                company_type__name__iexact="mechanical contractor"
            ).first()
        return value

    class Meta:
        model = AccountSummary
        fields = [
            "customer",
            "attention",
            "created_by",
        ]


class AccountSummarySerializer(serializers.ModelSerializer):
    address = AddressSerializer()
    contact_info = ContactInfoSerializer()
    invoices = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = [
            "name",
            "company_type",
            "address",
            "contact_info",
            "invoices",
        ]

    def get_invoices(self, company):
        invoices = Invoice.objects.filter(
            order__proposal__estimate__customer__company=company
        )

        return [
            {
                "id": invoice.id,
                "order_id": invoice.order_id,
                "invoice_number": invoice.invoice_number,  # Access @property directly
                "created_on": invoice.created_on,
                "po_number": invoice.order.po_number,  # Adjust if necessary
                "project_name": invoice.order.proposal.estimate.project.name,  # Adjust if necessary
                "total_invoiced": invoice.total_invoiced,  # Access @property directly
                "amount_due": invoice.amount_due,  # Access @property directly
            }
            for invoice in invoices
        ]
