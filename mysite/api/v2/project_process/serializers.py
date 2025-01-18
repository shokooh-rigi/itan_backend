from rest_framework import serializers

from mysite.projectprocess.models import ProjectProcess, ProjectProcessPreDemo


class ProjectProcessSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectProcess
        fields = '__all__'


class ProjectProcessPreDemoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectProcessPreDemo
        fields = '__all__'
