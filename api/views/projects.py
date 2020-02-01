import datetime
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from mysite.estimator.models import Estimate

from ..models.project import ProjectModel
from ..serializers.project import ProjectSerializer
from ..pagination import StandardResultsSetPagination


class ProjectsAPIView(APIView):
    serializer_class = ProjectSerializer

    # Fetch a list of Projects
    def get(self, request, format=None):
        if request.user.is_authenticated:
            estimates = Estimate.objects\
                .filter(customer=request.user.profile.customer)

            estimates = self.filter_estimates(request, estimates)

            def map_func(result_page):
                items = map((lambda estimate: (estimate.project,
                                               estimate.customer,
                                               estimate.engineer)),
                            result_page)
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
                return projects

            paginator = StandardResultsSetPagination()
            return paginator.get_paginated_response(estimates, request, map_func, self.serializer_class)
        else:
            return Response('401 Unauthorized', status=status.HTTP_401_UNAUTHORIZED)

    # Filter the estimates
    def filter_estimates(self, request, estimates):
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
