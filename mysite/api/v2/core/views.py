from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.tokens import (
    default_token_generator as account_activation_token,
)
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.core.paginator import Paginator
from django.conf import settings
from datetime import datetime, timedelta
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from dateutil.relativedelta import relativedelta

from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from django.db.models import Sum, Q

from custom_user.models import User
from mysite import settings
from mysite.bidfilemgm.models import BidFile
from mysite.core.models import (
    Announcement,
    AnnouncementSeen,
    Person,
    Project,
    Company,
    Profile,
    CreditCard,
    LicenseInfo,
    CompanyType,
    Service,
)
from mysite.estimator.models import Estimate
from mysite.proposal.models import Proposal
from mysite.s3_file_manager import S3
from .permissions import IsOwnerOrAdmin
from django.utils.timezone import now
from django.db.models.functions import TruncMonth, TruncDay
from django.db.models import Count
from .serializers import (
    AnnouncementSerializer,
    ProjectSerializer,
    CompanySerializer,
    PersonSerializer,
    CreditCardSerializer,
    ProfileSerializer,
    UserSerializer,
    DocumentSerializer,
    CompanyTypeSerializer,
    ServiceSerializer,
)


class CustomerViewSet(ModelViewSet):
    """
    API endpoint for creating and editing Customers.
    """

    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "name",
                openapi.IN_QUERY,
                description="Search for customers by name or company name",
                type=openapi.TYPE_STRING,
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """
        Retrieve a list of customers, optionally filtered by name.
        """
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        """
        Optionally filter the queryset based on query parameters.
        """
        queryset = super().get_queryset()
        name = self.request.query_params.get("name", None)
        if name:
            queryset = queryset.filter(
                Q(name__icontains=name) | Q(company__name__icontains=name)
            )
        return queryset


class EngineerViewSet(ModelViewSet):
    """
    API endpoint for creating and editing Engineers.
    """

    queryset = Person.objects.filter(company__company_type__name__icontains="engineer")
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


class CompanyListView(APIView):
    """
    API View to list, filter, and paginate companies.

    This API allows authenticated users to retrieve a paginated list of companies
    with optional search, sorting, and date filtering.
    """

    permission_classes = [
        permissions.IsAuthenticated
    ]  # Require authentication for access

    @swagger_auto_schema(
        operation_summary="Retrieve a list of companies",
        operation_description="Get a paginated list of companies with search and filter capabilities.",
        manual_parameters=[
            openapi.Parameter(
                "search",
                openapi.IN_QUERY,
                description="Search query to filter companies by name or ID.",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "page_size",
                openapi.IN_QUERY,
                description="Number of companies per page. Defaults to the project setting.",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "ordering",
                openapi.IN_QUERY,
                description="Sort companies by a specific field. Default is '-created_on'.",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "fromDate",
                openapi.IN_QUERY,
                description="Start date for filtering companies (Format: MM/DD/YYYY).",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "toDate",
                openapi.IN_QUERY,
                description="End date for filtering companies (Format: MM/DD/YYYY).",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "page",
                openapi.IN_QUERY,
                description="Page number to retrieve. Default is 1.",
                type=openapi.TYPE_INTEGER,
            ),
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="List of companies with pagination info.",
                examples={
                    "application/json": {
                        "companies": [
                            {
                                "id": 1,
                                "name": "Company A",
                                "created_on": "YYYY-MM-DD",
                                "owner": "User ID",
                                "address": "Some Address",
                            }
                        ],
                        "pagination": {
                            "total_rows": 50,
                            "total_pages": 5,
                            "current_page": 1,
                            "page_size": 10,
                        },
                    }
                },
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Invalid request parameters.",
            ),
        },
    )
    def get(self, request):
        """Retrieve a paginated list of companies with search and filter options."""

        # Extract query parameters
        search = request.GET.get("search", "")
        page_size = int(request.GET.get("page_size", settings.PAGE_SIZE))
        ordering = request.GET.get("ordering", "-created_on")
        from_date = request.GET.get("fromDate")
        to_date = request.GET.get("toDate")

        # Build filter conditions
        filters = Q()
        if search:
            filters &= Q(name__icontains=search) | Q(
                id__icontains=search
            )  # Search by name or ID

        # Filter by date range if provided
        if from_date:
            from_date_obj = datetime.strptime(from_date, "%m/%d/%Y")
            filters &= Q(created_on__gte=from_date_obj)

        if to_date:
            to_date_obj = (
                datetime.strptime(to_date, "%m/%d/%Y")
                + timedelta(days=1)
                - timedelta(seconds=1)
            )
            filters &= Q(created_on__lte=to_date_obj)

        # Query the database with filters and ordering
        object_list = Company.objects.filter(filters).order_by(ordering)

        # Apply pagination
        paginator = Paginator(object_list, page_size)
        page_number = request.GET.get("page", 1)
        paginated_companies = paginator.get_page(page_number)

        try:
            # Serialize the paginated results
            serializer = CompanySerializer(paginated_companies, many=True)
            data = {
                "companies": serializer.data,
                "pagination": {
                    "total_rows": paginator.count,
                    "total_pages": paginator.num_pages,
                    "current_page": paginated_companies.number,
                    "page_size": page_size,
                },
            }
            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            # Handle unexpected errors
            return Response(
                {"error": "An error occurred while retrieving companies."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


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


class ProfilesViewSet(ModelViewSet):
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


class ProfileView(APIView):
    """
    Get current user's profile.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):

        profile = Profile.objects.get(user=request.user)

        serializer = ProfileSerializer(profile)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        profile = Profile.objects.get(user=request.user)

        # Extract firstName and lastName from the request data
        first_name = request.data.get("firstName")
        last_name = request.data.get("lastName")

        # Update the profile fields if provided
        if first_name:
            profile.user.first_name = first_name
        if last_name:
            profile.user.last_name = last_name

        profile.user.save()

        # Serialize the updated profile
        serializer = ProfileSerializer(profile)

        return Response(serializer.data, status=status.HTTP_200_OK)


class HomeView(APIView):
    """
    Get user's data for the home page
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Fetch all announcements (don't filter out unseen at this stage)
        announcements = Announcement.objects.filter(archive=False)

        # Get the IDs of announcements the user has already seen
        seen_announcement_ids = AnnouncementSeen.objects.filter(user=user).values_list(
            "announcement_id", flat=True
        )

        # Serialize announcements and include the 'seen' status
        announcements_serializer = AnnouncementSerializer(
            announcements,
            many=True,
            context={
                "request": request,
                "seen_announcement_ids": seen_announcement_ids,
            },
        )

        # Cache the serialized response data
        response_data = announcements_serializer.data

        # Record unseen announcements
        unseen_announcements = announcements.exclude(id__in=seen_announcement_ids)

        # Bulk create AnnouncementSeen records for unseen announcements
        AnnouncementSeen.objects.bulk_create(
            [
                AnnouncementSeen(user=user, announcement=announcement)
                for announcement in unseen_announcements
            ]
        )

        current_year = now().year
        current_month = now().month
        today = now().date()
        start_date = today - timedelta(days=6)
        total_bids = BidFile.objects.filter(created_on__year=current_year)

        bids_total_amount = sum(
            estimate.total_calculated
            for estimate in Estimate.objects.filter(bfm__in=total_bids)
        )

        bids_by_day = (
            BidFile.objects.filter(created_on__date__range=[start_date, today])
            .annotate(day=TruncDay("created_on"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )

        daily_bid_counts = {
            str((today - timedelta(days=i)).strftime("%a")): 0 for i in range(6, -1, -1)
        }
        for entry in bids_by_day:
            day_str = entry["day"].strftime("%a")
            daily_bid_counts[day_str] = entry["count"]

        estimates = Estimate.objects.filter(
            bfm__created_on__year=current_year, archive=False
        )
        estimates_by_month = (
            estimates.annotate(month=TruncMonth("created_on"))
            .values("month")
            .annotate(total_calculated_sum=Sum("total_calculated"))
            .order_by("month")
        )

        monthly_estimates = {
            (now() - relativedelta(months=(current_month - i))).strftime("%b"): 0
            for i in range(1, current_month + 1)
        }
        for entry in estimates_by_month:
            month_name = entry["month"].strftime("%b")
            monthly_estimates[month_name] = entry["total_calculated_sum"]

        proposals = Proposal.objects.filter(estimate__in=estimates)

        proposals_by_month = (
            proposals.annotate(month=TruncMonth("created_on"))
            .values("month")
            .annotate(total_calculated_sum=Sum("estimate__total_calculated"))
            .order_by("month")
        )

        monthly_proposals = {
            (now() - relativedelta(months=(current_month - i))).strftime("%b"): 0
            for i in range(1, current_month + 1)
        }
        for entry in proposals_by_month:
            month_name = entry["month"].strftime("%b")
            monthly_proposals[month_name] = entry["total_calculated_sum"]

        return Response(
            {
                "announcements": response_data,  # Return the cached response data
                "bidsCount": total_bids.count(),
                "bidsTotal": bids_total_amount,
                "dailyBidCounts": daily_bid_counts,
                "totalEstimatesByMonth": monthly_estimates,
                "totalProposalsByMonth": monthly_proposals,
            },
            status=status.HTTP_200_OK,
        )


class CreditCardViewSet(ModelViewSet):
    queryset = CreditCard.objects.all()
    serializer_class = CreditCardSerializer
    permission_classes = [IsOwnerOrAdmin]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save()


class ManufacturerViewSet(ModelViewSet):
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


class ProjectViewSet(ModelViewSet):
    """
    API endpoint for managing Projects.
    """

    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
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

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save()


class ServiceViewSet(ModelViewSet):
    """
    ViewSet for managing Service model CRUD operations.
    """

    queryset = Service.objects.filter(is_deleted=False)
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]

    def perform_destroy(self, instance):
        """
        Soft delete the service by setting `is_deleted` to True.
        """
        instance.soft_delete()
        instance.save()


class UserViewSet(ModelViewSet):
    """
    - `create`: Creates a new user with the provided data, marking them as inactive by default.
        Handles the creation of a new user.

        Inserts the following during user creation:
        - `username`, `email`, `password`, `first_name`, `last_name` are taken from the request data.

    - `update`: Updates an existing user with the provided data. Does not modify fields that are not provided in the request.
            Inserts the following during user update:
        - Fields like `username`, `email`, `first_name`, `last_name`
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save()


class GetEngineerId(APIView):
    """
    Retrieve the engineer ID based on the engineer's name.
    """

    permission_classes = [IsAuthenticated]

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

    permission_classes = [IsAuthenticated]

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

    permission_classes = [IsAuthenticated]

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

    permission_classes = [IsAuthenticated]

    def get(self, request):
        company_name = request.GET.get("company_name")
        try:
            company = CompanyType.objects.get(name=company_name)
            return Response({"company_id": company.id}, status=status.HTTP_200_OK)
        except CompanyType.DoesNotExist:
            return Response(
                {"error": "Company not found"}, status=status.HTTP_404_NOT_FOUND
            )


class CompanyTypeList(APIView):
    """
    Retrieve all company types.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            name_filter = request.query_params.get("name")
            if name_filter:
                company_types = CompanyType.objects.filter(name__icontains=name_filter)
            else:
                company_types = CompanyType.objects.all()
            serializer = CompanyTypeSerializer(
                company_types,
                many=True,
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"An error occurred in get company types: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SignUpAPIView(APIView):
    """
    API for user registration. Creates a new user and sends an activation email.
    """

    permission_classes = [IsAuthenticated]

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

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return Response(
            {"message": "Account activation link sent. Please check your email."},
            status=status.HTTP_200_OK,
        )


class ActivateAccountAPIView(APIView):
    """
    API for activating user accounts via email link.
    """

    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

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
