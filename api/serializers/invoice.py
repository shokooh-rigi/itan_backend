from rest_framework import serializers

from mysite.gi.views import estimate_total_calculator, calculate_total_amount_due
from mysite.gi.models import Invoice


class InvoiceSerializer(serializers.ModelSerializer):
    invoice_number = serializers.SerializerMethodField()
    project_number = serializers.CharField(source='order.project_number')
    project_name = serializers.CharField(
        source='order.proposal.quote.estimate.bfm.project.name')
    total_ordered = serializers.SerializerMethodField()
    total_invoiced = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            'id',
            'invoice_number',
            'project_number',
            'project_name',
            'total_ordered',
            'percent_of_performance_completed',
            'total_invoiced',
            'created_on',
        ]

    def get_invoice_number(self, invoice):
        return '%s-%03d' % (invoice.order.project_number[3:], invoice.id)

    def get_total_ordered(self, invoice):
        return estimate_total_calculator(invoice.order.proposal.quote.estimate.id)

    def get_total_invoiced(self, invoice):
        return calculate_total_amount_due(invoice)
