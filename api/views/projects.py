from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from mysite.estimator.models import Estimate

from ..models.project import ProjectModel
from ..serializers.project import ProjectSerializer


class ProjectsAPIView(APIView):

    # Fetch a list of Projects
    def get(self, request, format=None):
        if request.user.is_authenticated:
            estimates = Estimate.objects\
                .filter(customer=request.user.profile.customer)\
                .order_by('-created_on')

            items = map((lambda estimate: (estimate.project,
                                           estimate.customer,
                                           estimate.engineer)),
                        estimates)

            projects = map((lambda item:
                            ProjectModel(
                                item[0].id,
                                item[0].name,
                                item[0].address_line_1,
                                item[0].city,
                                item[0].state,
                                item[0].zip,
                                item[0].created_on,
                                item[1].name,
                                item[2].name,
                                0)
                            ),
                           items)

            serializer = ProjectSerializer(projects, many=True)
            return Response(serializer.data)
        else:
            return Response('401 Unauthorized', status=status.HTTP_401_UNAUTHORIZED)
