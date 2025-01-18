from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from mysite.order.models import Order
from mysite.projectprocess.models import ProjectProcess, ProjectProcessPreDemo
from .serializers import ProjectProcessSerializer, ProjectProcessPreDemoSerializer
from ..order.serializers import OrderSerializer


class ProjectProcessListView(ListAPIView):
    """
    API endpoint to list and filter project processes with pagination and ordering.
    """
    serializer_class = OrderSerializer
    pagination_class = PageNumberPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        search = self.request.query_params.get('search', '')
        ordering = self.request.query_params.get('ordering', '-project_number')
        project_type = self.request.query_params.get('type', 'all')

        queryset = Order.objects.filter(
            Q(proposal__estimate__project__name__icontains=search) |
            Q(project_number__icontains=search)
        ).order_by(ordering)

        # Filter by type
        if project_type == 'tp':
            queryset = queryset.filter(projectprocess__tech_package=True)
        elif project_type == 'ts':
            queryset = queryset.filter(projectprocess__tech_scheduled=True)
        elif project_type == 'jc':
            queryset = queryset.filter(projectprocess__job_completed=True)
        elif project_type == 'ro':
            queryset = queryset.filter(projectprocess__report_out=True)
        elif project_type == 'in':
            queryset = queryset.filter(projectprocess__invoiced=True)
        elif project_type == 'co':
            queryset = queryset.filter(projectprocess__completed=True)
        elif project_type == 'ntp':
            queryset = queryset.filter(Q(projectprocess__tech_package=False) | Q(projectprocess__isnull=True))
        elif project_type == 'nts':
            queryset = queryset.filter(Q(projectprocess__tech_scheduled=False) | Q(projectprocess__isnull=True))
        elif project_type == 'njc':
            queryset = queryset.filter(Q(projectprocess__job_completed=False) | Q(projectprocess__isnull=True))
        elif project_type == 'nro':
            queryset = queryset.filter(Q(projectprocess__report_out=False) | Q(projectprocess__isnull=True))
        elif project_type == 'nin':
            queryset = queryset.filter(Q(projectprocess__invoiced=False) | Q(projectprocess__isnull=True))
        elif project_type == 'nco':
            queryset = queryset.filter(Q(projectprocess__completed=False) | Q(projectprocess__isnull=True))

        return queryset

class ProjectProcessView(APIView):
    """
    API endpoint to edit, update, or create a project process or project process pre-demo.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id, pre_demo):
        """
        Retrieve the project process or project process pre-demo for the given order.
        """
        if pre_demo == 0:
            instance = get_object_or_404(ProjectProcess, order_id=order_id)
            serializer = ProjectProcessSerializer(instance)
        else:
            instance = get_object_or_404(ProjectProcessPreDemo, order_id=order_id)
            serializer = ProjectProcessPreDemoSerializer(instance)

        return Response(serializer.data)

    def post(self, request, order_id, pre_demo):
        """
        Create a new project process or project process pre-demo.
        """
        if pre_demo == 0:
            serializer_class = ProjectProcessSerializer
        else:
            serializer_class = ProjectProcessPreDemoSerializer

        serializer = serializer_class(data=request.data)

        if serializer.is_valid():
            serializer.save(order_id=order_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, order_id, pre_demo):
        """
        Update an existing project process or project process pre-demo.
        """
        if pre_demo == 0:
            instance = get_object_or_404(ProjectProcess, order_id=order_id)
            serializer_class = ProjectProcessSerializer
        else:
            instance = get_object_or_404(ProjectProcessPreDemo, order_id=order_id)
            serializer_class = ProjectProcessPreDemoSerializer

        serializer = serializer_class(instance, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
