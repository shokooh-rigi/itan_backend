from datetime import datetime, timedelta

from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from mysite.core.models import LicenseFiles, LicenseInfo
from mysite.estimator.models import Estimate
from mysite.estimator.templatetags.estimator_tags import pdf_filename_generator
from mysite.proposal.models import Proposal
from mysite.s3_file_manager import S3
from .serializers import ProposalSerializer
from ..estimator.serializers import EmailSerializer, EstimateSerializer
from ..estimator.services import TemplateService, EstimateEmailService


class ProposalListView(APIView):
    """
    List and filter proposals with pagination.

    Provides endpoints for authenticated users to retrieve and filter a paginated list of proposals.
    Allows optional search by estimate ID, project name, and customer company name, with date filtering.
    """

    permission_classes = [IsAuthenticated]
    manual_parameters = (
        [
            openapi.Parameter(
                "search",
                openapi.IN_QUERY,
                description="Filter by project name or customer company name",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "ordering",
                openapi.IN_QUERY,
                description="Order the results by a field (default is 'due_date')",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "fromDate",
                openapi.IN_QUERY,
                description="Start date for filtering proposal by due date (mm/dd/yyyy)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "toDate",
                openapi.IN_QUERY,
                description="End date for filtering proposal by due date (mm/dd/yyyy)",
                type=openapi.TYPE_STRING,
            ),
        ],
    )
    responses = (
        {
            200: openapi.Response(
                "A paginated list of proposal",
                ProposalSerializer(many=True),
            ),
            400: "Invalid date format or other error",
        },
    )

    def get(self, request):
        search = request.GET.get("search", "")
        paginate_by = int(request.GET.get("paginate_by", settings.PAGE_SIZE))
        ordering = request.GET.get("ordering", "-created_on")

        # Basic filters
        filters = Q(archive=False, is_deleted=False)

        # Search filter
        if search:
            if search.isnumeric():
                filters &= (
                    Q(estimate__id=search)
                    | Q(estimate__project__name__icontains=search)
                    | Q(estimate__customer__company__name__icontains=search)
                )
            else:
                filters &= Q(estimate__project__name__icontains=search) | Q(
                    estimate__customer__company__name__icontains=search
                )

        # Date range filtering
        from_date = request.GET.get("fromDate")
        to_date = request.GET.get("toDate")

        if from_date and to_date:
            try:
                from_date_obj = datetime.strptime(from_date, "%m/%d/%Y")
                to_date_obj = (
                    datetime.strptime(to_date, "%m/%d/%Y")
                    + timedelta(days=1)
                    - timedelta(seconds=1)
                )
                filters &= Q(estimate__due_date__range=(from_date_obj, to_date_obj))
            except ValueError:
                return Response(
                    {"error": "Invalid date format. Use MM/DD/YYYY."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Fetch and order proposals
        proposals = Proposal.objects.filter(filters).order_by(ordering)

        # Pagination
        paginator = Paginator(proposals, paginate_by)
        page_number = request.GET.get("page", 1)
        paginated_proposals = paginator.get_page(page_number)

        serializer = ProposalSerializer(paginated_proposals, many=True)

        # Response structure
        data = {
            "proposals": serializer.data,
            "pagination": {
                "total_rows": paginator.count,
                "total_pages": paginator.num_pages,
                "current_page": paginated_proposals.number,
                "page_size": paginate_by,
            },
        }
        return Response(data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Retrieve or update a proposal instance by its ID.",
        request_body=EmailSerializer,  # Input schema
        responses={
            200: openapi.Response(
                "Successfully updated the proposal instance", EmailSerializer
            ),
            400: "Validation error in input data",
            404: "proposal not found",
        },
    )
    def post(self, request):
        """
        Send a proposal email to specified recipients.

        This endpoint validates and sends a proposal email based on the provided email data, which includes
        the recipient email, CC addresses, and email subject.
        """
        email_serializer = EmailSerializer(data=request.data)
        if email_serializer.is_valid():
            email_data = email_serializer.validated_data
            to_email = email_data["to_email"]
            cc = email_data["cc"] + ["est@tabtechinc.com", "a.behehsti@tabtechinc.com"]
            email_id = email_data["email_id"]
            subject = email_data["subject"]

            template_service = TemplateService()
            email_service = EstimateEmailService(
                request=request,
                estimate_id=email_id,
                storage_service=S3(),
                template_service=template_service,
                modules_to_email_template=5,
                pdf_path="/pdfs/proposal/",
                pdf_prefix="P",
            )
            try:
                email_service.send_email(
                    to_email=to_email,
                    cc=cc,
                    subject=subject,
                )
                return Response(
                    {"message": "Email sent successfully."}, status=status.HTTP_200_OK
                )
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(email_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProposalEstimateListView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Retrieve non-archived and unassociated estimates",
        operation_description=(
            "This endpoint retrieves estimates that are not archived and not associated with any proposal."
        ),
        responses={
            200: openapi.Response(
                description="List of available estimates",
                schema=EstimateSerializer(many=True),
            ),
            401: "Unauthorized - User must be authenticated",
        },
    )
    def get(self, request, estimate_id=None):
        """
        Retrieves available estimates that are not archived or associated with a proposal.

        Returns:
            - Response: Serialized data of estimates.
        """
        try:
            estimates = (
                Estimate.objects.filter(archive=False)
                .exclude(id__in=Proposal.objects.values_list("estimate_id", flat=True))
                .order_by("-created_on")
            )

            if estimate_id:
                estimates = estimates.filter(id=estimate_id)

            if estimates.count() == 0:
                return Response(
                    {"detail": "No estimates available."},
                    status=status.HTTP_200_OK,
                )

            serializer = EstimateSerializer(estimates, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {
                    "detail": "An error occurred while retrieving estimates.",
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ProposalCreateView(APIView):
    """
    API endpoint for creating a proposal.

    Handles form data for creating a new proposal, associates it with an estimate,
    and generates a proposal PDF if the form data is valid.
    """

    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    @swagger_auto_schema(
        operation_description="create a proposal instance.",
        request_body=ProposalSerializer,
        responses={
            200: openapi.Response(
                "Successfully created the Proposal instance", ProposalSerializer
            ),
            400: "Validation error in input data",
            404: "Proposal not found",
        },
    )
    def post(self, request):
        """
        Creates a new proposal.
        """
        serializer = ProposalSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProposalArchiveView(APIView):
    """
    Archives a proposal if the user is authorized.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Archives a proposal if the user is authorized and confirms the action.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
        ),
        responses={
            200: openapi.Response(
                "Successfully archived the proposal",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"message": openapi.Schema(type=openapi.TYPE_STRING)},
                ),
            ),
            403: "User is not authorized to archive this record.",
            404: "proposal not found.",
        },
    )
    def post(self, request, id):
        proposal = get_object_or_404(
            Proposal,
            id=id,
            is_deleted=False,
        )

        if (
            proposal.estimate.created_by == request.user
            or request.user.profile.user_type == 2
        ):
            proposal.archive_record()
            return Response(
                {"message": "Proposal archived successfully"}, status=status.HTTP_200_OK
            )

        return Response(
            {"error": "You are not authorized to archive this record."},
            status=status.HTTP_403_FORBIDDEN,
        )


class ProposalDeleteView(APIView):
    """
    Deletes a proposal if the user is authorized.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Deletes a proposal instance if the user is authorized.",
        responses={
            200: openapi.Response(
                "Successfully deleted the proposal",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"message": openapi.Schema(type=openapi.TYPE_STRING)},
                ),
            ),
            403: "User is not authorized to delete this record.",
            404: "proposal not found.",
            500: "Error deleting file from S3.",
        },
    )
    def delete(self, request, proposal_id):
        proposal = get_object_or_404(
            Proposal,
            id=proposal_id,
            is_deleted=False,
        )
        if (
            proposal.estimate.created_by == request.user
            or request.user.profile.user_type == 2
        ):
            proposal.soft_delete()
            return Response(
                {"message": "Proposal soft_delete successfully"},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"error": "You are not authorized to delete this record."},
            status=status.HTTP_403_FORBIDDEN,
        )
