from rest_framework import status
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from mysite.core.models import ContactInfo, Person, Project, Company, Profile, CreditCard
from mysite.s3_file_manager import S3
from .permissions import IsOwnerOrAdmin
from .serializers import (
    CompanyCustomerSerializer, CompanyEngineerSerializer,
    ProjectSerializer, CompanySerializer, PersonSerializer, CreditCardSerializer
)
from .serializers import ProfileSerializer


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


class CompanyViewSet(ModelViewSet):
    """
    API ViewSet for managing Company objects.
    Supports CRUD operations.
    """
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Optionally filter the queryset based on query parameters.
        """
        queryset = super().get_queryset()
        name = self.request.query_params.get("name", None)
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset


class PersonViewSet(ModelViewSet):
    """
    API ViewSet for managing Person objects.
    Supports CRUD operations.
    """
    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Optionally filter the queryset based on query parameters.
        """
        queryset = super().get_queryset()
        company_id = self.request.query_params.get("company", None)
        name = self.request.query_params.get("name", None)

        if company_id:
            queryset = queryset.filter(company__id=company_id)
        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset


class ProfileViewSet(ModelViewSet):
    queryset = Profile.objects.select_related(
        'user', 'customer', 'tech', 'contact_info', 'location', 'physical_address', 'billing_address'
    )
    serializer_class = ProfileSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        queryset = super().get_queryset()
        filters = {}
        if user_id := self.request.query_params.get('user'):
            filters['user__id'] = user_id
        if user_type := self.request.query_params.get('user_type'):
            filters['user_type'] = user_type
        if worker_status := self.request.query_params.get('worker_status'):
            filters['worker_status'] = worker_status

        return queryset.filter(**filters)

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            profile = serializer.save(user=self.request.user)
            s3 = S3()
            # Upload files after profile is created
            self.upload_file_to_s3(profile, 'photo', s3)
            self.upload_file_to_s3(profile, 'e_sign', s3)
            self.upload_file_to_s3(profile, 'stamp', s3)
            self.upload_file_to_s3(profile, 'wallpaper', s3)
        else:
            raise PermissionDenied("Authentication is required to create a profile.")

    def upload_file_to_s3(self, profile, field_name, s3):
        file = getattr(profile, field_name, None)
        if file:
            s3.upload_file_to_bucket(file_name=file.name, key=file.name)

    def delete(self, *args, **kwargs):
        profile = self.get_object()  # Get the profile instance to delete
        s3 = S3()
        for field_name in ['photo', 'e_sign', 'stamp', 'wallpaper']:
            file = getattr(profile, field_name, None)
            if file:
                s3.delete_file_from_bucket(file.name)
        return super().delete(*args, **kwargs)


class CreditCardViewSet(viewsets.ModelViewSet):
    queryset = CreditCard.objects.all()
    serializer_class = CreditCardSerializer
    permission_classes = [IsOwnerOrAdmin]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save()


class EngineerViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Engineer Persons.
    """
    queryset = Person.objects.all()
    serializer_class = PersonSerializer
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
    serializer_class = PersonSerializer
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
