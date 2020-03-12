import datetime
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from mysite.bidfilemgm.models import BidFile

from ..authentication_mixin import AuthenticationMixin
from ..serializers.project import ProjectSerializer
from ..pagination import CustomPageNumberPagination


def _get_project(request, pk):
    """Retrieves a project"""

    return get_object_or_404(BidFile, pk=pk, customer=request.user.profile.customer)


class ProjectsAPIView(AuthenticationMixin, APIView):
    serializer_class = ProjectSerializer

    def _get_all_projects(self, request):
        return BidFile.objects.filter(customer=request.user.profile.customer, hidden_for_customer=False)

    def get(self, request, project_id=None, format=None):
        """Fetch a list of Projects"""

        if project_id != None:
            project = _get_project(request, project_id)
            serializer = self.serializer_class(project, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            projects = self._get_all_projects(request)
            projects = self._filter_projects(request, projects)
            paginator = CustomPageNumberPagination()
            return paginator.get_paginated_response(projects, request, self.serializer_class)

    def _filter_projects(self, request, estimates):
        """Filter the estimates"""

        filter = {
            'search': request.query_params.get('search', ''),
            'fromDate': request.query_params.get('fromDate', ''),
            'toDate': request.query_params.get('toDate', ''),
            'ordering': request.query_params.get('ordering', ''),
            'asc': True if request.query_params.get('asc', 'true') == 'true' else False
        }

        if filter['search']:
            estimates = estimates.filter(
                Q(project__name__icontains=filter['search']))

        if filter['fromDate'] and filter['toDate']:
            from_date_obj = datetime.datetime.strptime(
                filter['fromDate'], '%m/%d/%Y')
            to_date_obj = datetime.datetime.strptime(
                filter['toDate'], '%m/%d/%Y')
            estimates = estimates.filter(
                project__created_on__range=(from_date_obj, to_date_obj))

        if filter['ordering']:
            estimates = estimates.order_by(
                ('' if filter['asc'] else '-') + 'project__' + filter['ordering'])

        return estimates


def hide_project(request, project_id=None):
    """Hides a Project"""

    if request.method == 'PUT':
        if request.user.is_authenticated:
            project = _get_project(request, project_id)
            project.hidden_for_customer = True
            project.save()
            return HttpResponse(status=status.HTTP_204_NO_CONTENT)
        return HttpResponse('401 Unauthorized', status=status.HTTP_401_UNAUTHORIZED)
