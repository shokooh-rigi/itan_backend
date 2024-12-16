from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib.auth.tokens import (
    default_token_generator as account_activation_token,
)
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

from mysite import settings
from mysite.core.models import (
    ContactInfo,
    Person,
    Project,
    Company,
    Profile,
    CreditCard,
    LicenseInfo, CompanyType,
)
from mysite.s3_file_manager import S3
from .permissions import IsOwnerOrAdmin
from .serializers import (
    CustomerSerializer,
    ProjectSerializer,
    CompanySerializer,
    PersonSerializer,
    CreditCardSerializer,
    ProfileSerializer,
    UserSerializer,
    DocumentSerializer,
)


class CustomerViewSet(viewsets.ModelViewSet):
    """
    API endpoint for creating and editing Customers.
    """

    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    permission_classes = [IsAuthenticated]


class EngineerViewSet(viewsets.ModelViewSet):
    """
    API endpoint for creating and editing Engineers.
    """

    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    permission_classes = [IsAuthenticated]


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
        "user",
        "customer",
        "tech",
        "contact_info",
        "location",
        "physical_address",
        "billing_address",
    )
    serializer_class = ProfileSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        queryset = super().get_queryset()
        filters = {}
        if user_id := self.request.query_params.get("user"):
            filters["user__id"] = user_id
        if user_type := self.request.query_params.get("user_type"):
            filters["user_type"] = user_type
        if worker_status := self.request.query_params.get("worker_status"):
            filters["worker_status"] = worker_status

        return queryset.filter(**filters)

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            profile = serializer.save(user=self.request.user)
            s3 = S3()
            # Upload files after profile is created
            self.upload_file_to_s3(profile, "photo", s3)
            self.upload_file_to_s3(profile, "e_sign", s3)
            self.upload_file_to_s3(profile, "stamp", s3)
            self.upload_file_to_s3(profile, "wallpaper", s3)
        else:
            raise PermissionDenied("Authentication is required to create a profile.")

    def upload_file_to_s3(self, profile, field_name, s3):
        file = getattr(profile, field_name, None)
        if file:
            s3.upload_file_to_bucket(file_name=file.name, key=file.name)

    def delete(self, *args, **kwargs):
        profile = self.get_object()  # Get the profile instance to delete
        s3 = S3()
        for field_name in ["photo", "e_sign", "stamp", "wallpaper"]:
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
        engineer_name = request.GET.get("engineer_name")
        try:
            engineer = Person.objects.get(name=engineer_name)
            return Response({"person_id": engineer.id}, status=status.HTTP_200_OK)
        except Person.DoesNotExist:
            return Response(
                {"error": "Engineer not found"}, status=status.HTTP_404_NOT_FOUND
            )


class GetProjectId(APIView):
    """
    Retrieve the project ID based on the project name.
    """

    def get(self, request):
        project_name = request.GET.get("project_name")
        try:
            project = Project.objects.get(name=project_name)
            return Response({"project_id": project.id}, status=status.HTTP_200_OK)
        except Project.DoesNotExist:
            return Response(
                {"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND
            )


class GetPersonId(APIView):
    """
    Retrieve the person ID based on the person's name.
    """

    def get(self, request):
        person_name = request.GET.get("person_name")
        try:
            person = Person.objects.get(name=person_name)
            return Response({"person_id": person.id}, status=status.HTTP_200_OK)
        except Person.DoesNotExist:
            return Response(
                {"error": "Person not found"}, status=status.HTTP_404_NOT_FOUND
            )


class GetCompanyId(APIView):
    """
    Retrieve the company ID based on the company name.
    """

    def get(self, request):
        company_name = request.GET.get("company_name")
        try:
            company = CompanyType.objects.get(name=company_name)
            return Response({"company_id": company.id}, status=status.HTTP_200_OK)
        except CompanyType.DoesNotExist:
            return Response(
                {"error": "Company not found"}, status=status.HTTP_404_NOT_FOUND
            )


class SignUpAPIView(APIView):
    """
    API for user registration. Creates a new user and sends an activation email.
    """

    def post(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save(
                is_active=False
            )  # Deactivate user until they activate their account

            # Send activation email
            current_site = get_current_site(request)
            subject = "Activate Your Account on Tab Technologies INC."
            message = render_to_string(
                "account_activation_email.html",
                {
                    "user": user,
                    "domain": current_site.domain,
                    "main_website": LicenseInfo.objects.get(key="OwnerWeb").value,
                    "uid": urlsafe_base64_encode(str(user.pk).encode()),
                    "token": account_activation_token.make_token(user),
                },
            )
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

            return Response(
                {
                    "message": "Account created. Please check your email to activate your account."
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AccountActivationSentAPIView(APIView):
    """
    API to confirm that the account activation link has been sent.
    """

    def get(self, request, *args, **kwargs):
        return Response(
            {"message": "Account activation link sent. Please check your email."},
            status=status.HTTP_200_OK,
        )


class ActivateAccountAPIView(APIView):
    """
    API for activating user accounts via email link.
    """

    def get(self, request, uidb64, token, *args, **kwargs):
        try:
            # Decode the user ID
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, ObjectDoesNotExist):
            user = None

        if user is not None and account_activation_token.check_token(user, token):
            user.is_active = True
            user.save()
            return Response(
                {"message": "Account successfully activated."},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"message": "Invalid activation link."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class DocumentUploadAPIView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        serializer = DocumentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Document uploaded successfully."},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class ChangePasswordAPIView(APIView):
    """
    API for changing passwords and invalidating JWT tokens.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        form = PasswordChangeForm(user=request.user, data=request.data)
        if form.is_valid():
            form.save()
            # Blacklist all outstanding tokens for the user
            tokens = OutstandingToken.objects.filter(user=request.user)
            for token in tokens:
                token.blacklist()
            return Response(
                {"message": "Password successfully updated. Please log in again."},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"errors": form.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
