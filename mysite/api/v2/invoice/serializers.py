from rest_framework import serializers

from mysite.api.v2.order.serializers import OrderSerializer
from mysite.gi.models import Invoice, InvoiceHistory, AccountSummary, InvoiceTransaction
from mysite.order.models import Order
from django.shortcuts import get_object_or_404


class InvoiceSerializer(serializers.ModelSerializer):
    """
    Serializer for handling Invoice creation and updates.

    - Validates and processes invoice data.
    - Integrates with the service layer to handle related business logic.
    """
    order = OrderSerializer(read_only=True)
    order_id = serializers.IntegerField(write_only=True)
    invoice_number = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id',
            'order',
            'order_id',
            'invoice_type',
            'date_started',
            'date_completed',
            'terms',
            'description',
            'percent_of_performance_completed',
            'attention',
            'edited_on',
            'created_by',
            'invoice_number',
        ]
        read_only_fields = ["invoice_number"]

    def create(self, validated_data):
        """Override create method to link order using order_id"""
        order_id = validated_data.pop("order_id", None)
        if not order_id:
            raise serializers.ValidationError({"order_id": "This field is required."})

        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            raise serializers.ValidationError({"order_id": "Invalid order_id."})

        validated_data["order"] = order
        return super().create(validated_data)

    def get_invoice_number(self, obj):
        """
        Retrieves the formatted invoice number for the given invoice object.

        Args:
            obj (Invoice): The invoice instance.

        Returns:
            str: The formatted invoice number.
        """
        return obj.invoice_number


class InvoiceHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for Invoice History.
    - Requires `invoice_id` to create a history record.
    """
    invoice_id = serializers.IntegerField(write_only=True, required=True)
    invoice = InvoiceSerializer(read_only=True)

    class Meta:
        model = InvoiceHistory
        fields = [
            'invoice',
            'invoice_id',
            'total_invoiced',
            'total_paid',
            'balance_due',
            'pdf_filename',
        ]

    def create(self, validated_data):
        """
        Create InvoiceHistory entry and attach it to the Invoice.
        """
        invoice_id = validated_data.pop("invoice_id")
        invoice = get_object_or_404(Invoice, id=invoice_id)
        validated_data["invoice"] = invoice
        return super().create(validated_data)


class EmailSerializer(serializers.Serializer):
    invoice_id = serializers.IntegerField()
    to_email = serializers.EmailField()
    cc = serializers.CharField(required=False)
    subject = serializers.CharField(max_length=255)

    def validate(self, data):
        if not data.get('to_email'):
            raise serializers.ValidationError("Recipient email is required.")
        return data


class InvoiceTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for InvoiceTransaction.
    - `invoice_id` is required only for creation, not updates.
    - Validates invoice existence before attaching it.
    """
    invoice_id = serializers.IntegerField(write_only=True, required=False)
    invoice = InvoiceSerializer(read_only=True)

    class Meta:
        model = InvoiceTransaction
        fields = [
            'id',
            'invoice',
            'invoice_id',
            'payment_date',
            'amount',
            'payment_no',
            'created_by',
            'created_on',
            'updated_at',
        ]

    def validate_invoice_id(self, value):
        """
        Validate that the invoice exists and is not deleted.
        """
        invoice = get_object_or_404(Invoice, id=value, is_deleted=False)
        return invoice.id

    def create(self, validated_data):
        """
        Create an InvoiceTransaction and attach it to the provided invoice.
        """
        invoice_id = validated_data.pop("invoice_id", None)
        invoice = get_object_or_404(Invoice, id=invoice_id, is_deleted=False) if invoice_id else None

        validated_data["invoice"] = invoice
        validated_data["created_by"] = self.context["request"].user

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Update an InvoiceTransaction, ensuring only valid fields are modified.
        """
        invoice_id = validated_data.pop("invoice_id", None)

        # Prevent invoice_id updates but allow other changes
        if invoice_id:
            raise serializers.ValidationError({"invoice_id": "Updating invoice_id is not allowed."})

        return super().update(instance, validated_data)
