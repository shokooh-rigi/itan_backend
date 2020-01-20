from rest_framework import serializers


class ProjectSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=255)
    address_line_1 = serializers.CharField(max_length=255)
    city = serializers.CharField(max_length=55)
    state = serializers.CharField(max_length=55)
    zip = serializers.CharField(max_length=10)
    created_on = serializers.DateTimeField()
    estimator = serializers.CharField(max_length=255)
    tech = serializers.CharField(max_length=255)
    passedSteps = serializers.IntegerField()
