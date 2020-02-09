from django.shortcuts import get_object_or_404
import datetime
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from mysite.estimator.models import *
from mysite.order.models import *
from mysite.gi.models import *

from ..models.project import ProjectModel
from ..serializers.project import MyProjectSerializer
from ..pagination import StandardResultsSetPagination
from django.http import JsonResponse


def project_details(request, project_id):
    if request.method == 'GET':
        project = Estimate.objects.filter(id=project_id)
        serializer = MyProjectSerializer(project, many=True)
        return JsonResponse(serializer.data, safe=False)
