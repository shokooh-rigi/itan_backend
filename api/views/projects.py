import datetime
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from mysite.estimator.models import *
from mysite.order.models import *
from mysite.gi.models import *

from ..serializers.project import ProjectSerializer
from ..pagination import StandardResultsSetPagination


class ProjectsAPIView(APIView):
    serializer_class = ProjectSerializer

    # Fetch a list of Projects
    def get(self, request, format=None):
        if request.user.is_authenticated:
            projects = BidFile.objects.filter(customer=request.user.profile.customer)

            projects = self.filter_projects(request, projects)

            paginator = StandardResultsSetPagination()
            return paginator.get_paginated_response(projects, request, None, self.serializer_class)
        else:
            return Response('401 Unauthorized', status=status.HTTP_401_UNAUTHORIZED)

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


