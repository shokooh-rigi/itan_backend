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
    invoice_number = serializers.SerializerMethodField(read_only=True)
    revision_date = serializers.SerializerMethodField(read_only=True)
    amount = serializers.SerializerMethodField(read_only=True)
    sub_total = serializers.SerializerMethodField(read_only=True)
    total_paid = serializers.SerializerMethodField(read_only=True)
    total_invoiced = serializers.SerializerMethodField(read_only=True)
    remaining_due = serializers.SerializerMethodField(read_only=True)
    amount_due = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id',
            'invoice_type',
            'date_started',
            'date_completed',
            'terms',
            'description',
            'percent_of_performance_completed',
            'attention',
            'edited_on',
            'created_by',
            'created_on',
            'invoice_number',
            'revision_date',
            'order',
            'amount',
            'sub_total',
            'total_paid',
            'total_invoiced',
            'remaining_due',
            'amount_due',
        ]

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
    

    def get_revision_date(self, obj):
        return obj.revision_date

    def get_invoice_number(self, obj):
        return obj.invoice_number
    
    def get_amount(self, obj):
        return obj.amount
    
    def get_sub_total(self, obj):
        return obj.sub_total
    
    def get_total_paid(self, obj):
        return obj.total_paid
    
    def get_total_invoiced(self, obj):
        return obj.total_invoiced
    
    def get_remaining_due(self, obj):
        return obj.remaining_due
    
    def get_amount_due(self, obj):
        return obj.amount_due


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
