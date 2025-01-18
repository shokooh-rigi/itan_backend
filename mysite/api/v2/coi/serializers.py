from rest_framework import serializers

from mysite.coi.models import Coi


class CoiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coi
        fields = '__all__'
