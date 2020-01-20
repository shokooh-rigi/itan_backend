from rest_framework import serializers

from mysite.estimator.models import Estimate


class ProjectsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Estimate
        fields = ['customer', 'project', 'engineer', 'created_by', 'created_on']

