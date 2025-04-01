from rest_framework import serializers

from mysite.estimator.templatetags.estimator_tags import estimate_total_calculator
from mysite.jobcosting.templatetags.costing_tags import (
    estimate_total_work,
    actual_total_work,
    delta_total_work,
    delta_total_price
)
from mysite.order.models import Order
from mysite.order.templatetags.order_tags import calculate_total_amount_due


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



class JobCostingSerializer(serializers.ModelSerializer):
    project_number = serializers.CharField(source="project_number")
    project_name = serializers.CharField(source="proposal.estimate.project")
    estimated_hours = serializers.SerializerMethodField()
    actual_hours = serializers.SerializerMethodField()
    hours_delta = serializers.SerializerMethodField()
    estimated_price = serializers.SerializerMethodField()
    actual_price = serializers.SerializerMethodField()
    price_delta = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "project_number",
            "project_name",
            "estimated_hours",
            "actual_hours",
            "hours_delta",
            "estimated_price",
            "actual_price",
            "price_delta",
        ]

    def get_estimated_hours(self, obj):
        return estimate_total_work(obj.proposal.estimate.id)

    def get_actual_hours(self, obj):
        return actual_total_work(obj.id)

    def get_hours_delta(self, obj):
        return delta_total_work(obj)

    def get_estimated_price(self, obj):
        return estimate_total_calculator(obj.proposal.estimate.id)

    def get_actual_price(self, obj):
        return calculate_total_amount_due(obj.invoice) if obj.invoice else 0

    def get_price_delta(self, obj):
        return delta_total_price(obj)
