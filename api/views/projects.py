import datetime
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from mysite.estimator.models import *
from mysite.order.models import *
from mysite.gi.models import *

from ..authentication_mixin import AuthenticationMixin
from ..serializers.project import ProjectSerializer
from ..pagination import StandardResultsSetPagination


class ProjectsAPIView(AuthenticationMixin, APIView):
    serializer_class = ProjectSerializer

    # Fetch a list of Projects
    def get(self, request, project_id=None, format=None):
        if project_id != None:
            project = get_object_or_404(BidFile, pk=project_id)
            serializer = self.serializer_class(project, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            projects = BidFile.objects.filter(
                customer=request.user.profile.customer)
            projects = self.filter_projects(request, projects)
            paginator = StandardResultsSetPagination()
            return paginator.get_paginated_response(projects, request, None, self.serializer_class)

    # Filter the estimates
    def filter_projects(self, request, estimates):
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
