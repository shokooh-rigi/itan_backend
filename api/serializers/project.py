from rest_framework import serializers
from mysite.estimator.models import *


class ProjectSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=255)
    created_on = serializers.DateTimeField()
    estimator = serializers.CharField(max_length=255)
    passedSteps = serializers.IntegerField()
    step_date_1 = serializers.DateTimeField()
    step_date_2 = serializers.DateTimeField()
    step_date_3 = serializers.DateTimeField()


class MyProjectSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name')
    project_address_line_1 = serializers.CharField(source='project.address_line_1')
    project_address_line_2 = serializers.CharField(source='project.address_line_2')
    project_city = serializers.CharField(source='project.city')
    project_state = serializers.CharField(source='project.state')
    project_zip = serializers.CharField(source='project.zip')
    estimator_fName = serializers.CharField(source='created_by.profile.user.first_name')
    estimator_lName = serializers.CharField(source='created_by.profile.user.last_name')

    class Meta:
        model = Estimate
        fields = "__all__"
