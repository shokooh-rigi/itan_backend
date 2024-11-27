from rest_framework import serializers

from mysite.order.models import Order


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for handling Order creation and updates.

    - Validates and processes Order data.
    """
    class Meta:
        model = Order

    fields = '__all_'
