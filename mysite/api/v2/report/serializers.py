from rest_framework import serializers


class PerformanceReportSerializer(serializers.Serializer):
    customer_type = serializers.ChoiceField(choices=["company", "person"])
    from_date = serializers.DateField()
    to_date = serializers.DateField()

    bid_count = serializers.IntegerField()
    bid_total = serializers.DecimalField(max_digits=12, decimal_places=2)

    estimate_count = serializers.IntegerField()
    estimate_total = serializers.DecimalField(max_digits=12, decimal_places=2)

    proposal_count = serializers.IntegerField()
    proposal_total = serializers.DecimalField(max_digits=12, decimal_places=2)

    order_count = serializers.IntegerField()
    order_total = serializers.DecimalField(max_digits=12, decimal_places=2)

    invoice_count = serializers.IntegerField()
    invoice_total = serializers.DecimalField(max_digits=12, decimal_places=2)
