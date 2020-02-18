from rest_framework import serializers

from mysite.core.models import BusinessCheckingAccount


class BusinessCheckingAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessCheckingAccount
        fields = "__all__"
