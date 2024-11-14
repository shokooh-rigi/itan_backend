from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from mysite.core.models import ContactInfo, Person, Project
from .serializers import (
    CompanyCustomerSerializer, CompanyEngineerSerializer,
    CustomerSerializer, EngineerSerializer,
    ManufacturerSerializer, ProjectSerializer
)


class CompanyCustomerViewSet(viewsets.ModelViewSet):
    """
    API endpoint for creating and editing Company Customers.
    """
    queryset = ContactInfo.objects.all()
    serializer_class = CompanyCustomerSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save()


class CompanyEngineerViewSet(viewsets.ModelViewSet):
    """
    API endpoint for creating and editing Company Engineers.
    """
    queryset = ContactInfo.objects.all()
    serializer_class = CompanyEngineerSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save()


class CustomerViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Customer Persons.
    """
    queryset = Person.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save()


class EngineerViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Engineer Persons.
    """
    queryset = Person.objects.all()
    serializer_class = EngineerSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save()


class ManufacturerViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Manufacturer Persons.
    """
    queryset = Person.objects.all()
    serializer_class = ManufacturerSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save()


class ProjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Projects.
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save()


class GetEngineerId(APIView):
    """
    Retrieve the engineer ID based on the engineer's name.
    """
    def get(self, request):
        engineer_name = request.GET.get('engineer_name')
        try:
            engineer = Person.objects.get(name=engineer_name)
            return Response({'person_id': engineer.id}, status=status.HTTP_200_OK)
        except Person.DoesNotExist:
            return Response({'error': 'Engineer not found'}, status=status.HTTP_404_NOT_FOUND)


class GetProjectId(APIView):
    """
    Retrieve the project ID based on the project name.
    """
    def get(self, request):
        project_name = request.GET.get('project_name')
        try:
            project = Project.objects.get(name=project_name)
            return Response({'project_id': project.id}, status=status.HTTP_200_OK)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)


class GetPersonId(APIView):
    """
    Retrieve the person ID based on the person's name.
    """
    def get(self, request):
        person_name = request.GET.get('person_name')
        try:
            person = Person.objects.get(name=person_name)
            return Response({'person_id': person.id}, status=status.HTTP_200_OK)
        except Person.DoesNotExist:
            return Response({'error': 'Person not found'}, status=status.HTTP_404_NOT_FOUND)


class GetCompanyId(APIView):
    """
    Retrieve the company ID based on the company name.
    """
    def get(self, request):
        company_name = request.GET.get('company_name')
        try:
            company = ContactInfo.objects.get(name=company_name)
            return Response({'company_id': company.id}, status=status.HTTP_200_OK)
        except ContactInfo.DoesNotExist:
            return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)
