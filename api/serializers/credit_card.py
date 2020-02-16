from rest_framework import serializers

from mysite.core.models import CreditCard


class CreditCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditCard
        fields = "__all__"
