from mysite.gi.models import *

from ..serializers.project import MyProjectSerializer
from django.http import JsonResponse


def project_details(request, project_id):
    if request.method == 'GET':
        project = Estimate.objects.filter(id=project_id)
        serializer = MyProjectSerializer(project, many=True)
        return JsonResponse(serializer.data, safe=False)
