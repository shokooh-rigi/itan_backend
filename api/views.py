from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from mysite.estimator.models import Estimate
from api.serializers import ProjectsSerializer


class MyProjectsList(APIView):
    def get(self, request, format=None):
        if request.user.is_authenticated:
            projects = Estimate.objects.filter(customer=request.user.profile.customer).order_by('-created_on')
            serializer = ProjectsSerializer(projects, many=True)
            return Response(serializer.data)
        else:
            return Response('Forbidden 403', status=status.HTTP_403_FORBIDDEN)
