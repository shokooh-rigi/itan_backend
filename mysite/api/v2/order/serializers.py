from rest_framework import serializers

from mysite.order.models import Order


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for handling Order creation and updates.

    - Validates and processes Order data.
    """
    class Meta:
        model = Order

    fields = [
        "id",
        "project_number",
        "po_number",
        "date_po_received",
        "estimated_date_of_project",
        "completion_percentage",
        "fully_settled",
        "archive",
        "state",
        "start_date",
        "end_date",
        "created_on",
    ]
