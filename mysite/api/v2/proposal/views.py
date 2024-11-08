from datetime import datetime, timedelta

from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from mysite.proposal.models import Proposal
from mysite.s3_file_manager import S3
from .serializers import ProposalSerializer
from ..estimator.serializers import EmailSerializer
from ..estimator.services import TemplateService, EstimateEmailService


class ProposalListView(APIView):
    """
    List and filter proposals with pagination.

    Provides endpoints for authenticated users to retrieve and filter a paginated list of proposals.
    Allows optional search by estimate ID, project name, and customer company name, with date filtering.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="List proposals",
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY,
                              description="Search term (estimate ID, project, or customer name)",
                              type=openapi.TYPE_STRING),
            openapi.Parameter('fromDate', openapi.IN_QUERY, description="Start date for filtering (MM/DD/YYYY)",
                              type=openapi.TYPE_STRING),
            openapi.Parameter('toDate', openapi.IN_QUERY, description="End date for filtering (MM/DD/YYYY)",
                              type=openapi.TYPE_STRING),
            openapi.Parameter('paginate_by', openapi.IN_QUERY, description="Number of items per page",
                              type=openapi.TYPE_INTEGER),
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number to retrieve",
                              type=openapi.TYPE_INTEGER),
        ],
        responses={200: openapi.Response("List of proposals returned successfully."),
                   400: openapi.Response("Invalid parameters provided.")},
    )
    def get(self, request):
        search = request.GET.get('search', '')
        paginate_by = int(request.GET.get('paginate_by', settings.PAGE_SIZE))
        ordering = request.GET.get('ordering', '-created_on')

        # Basic filters
        filters = Q(archive=False)

        # Search filter
        if search:
            if search.isnumeric():
                filters &= Q(estimate__id=search) | Q(estimate__project__name__icontains=search) | Q(
                    estimate__customer__company__name__icontains=search)
            else:
                filters &= Q(estimate__project__name__icontains=search) | Q(
                    estimate__customer__company__name__icontains=search)

        # Date range filtering
        from_date = request.GET.get("fromDate")
        to_date = request.GET.get("toDate")

        if from_date and to_date:
            try:
                from_date_obj = datetime.strptime(from_date, '%m/%d/%Y')
                to_date_obj = datetime.strptime(to_date, '%m/%d/%Y') + timedelta(days=1) - timedelta(seconds=1)
                filters &= Q(estimate__due_date__range=(from_date_obj, to_date_obj))
            except ValueError:
                return Response({"error": "Invalid date format. Use MM/DD/YYYY."}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch and order proposals
        proposals = Proposal.objects.filter(filters).order_by(ordering)

        # Pagination
        paginator = Paginator(proposals, paginate_by)
        page_number = request.GET.get('page', 1)
        paginated_proposals = paginator.get_page(page_number)

        serializer = ProposalSerializer(paginated_proposals, many=True)

        # Response structure
        data = {
            'proposals': serializer.data,
            'pagination': {
                'total_rows': paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': paginated_proposals.number,
                'page_size': paginate_by,
            }
        }
        return Response(data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=EmailSerializer,
        operation_summary="Send proposal email",
        responses={
            200: openapi.Response("Email sent successfully."),
            400: openapi.Response("Invalid email data provided.")
        }
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
            to_email = email_data['to_email']
            cc = email_data['cc'] + ['est@tabtechinc.com', 'a.behehsti@tabtechinc.com']
            email_id = email_data['email_id']
            subject = email_data['subject']

            template_service = TemplateService()
            email_service = EstimateEmailService(
                request=request,
                estimate_id=email_id,
                storage_service=S3(),
                template_service=template_service,
                modules_to_email_template=5,
                pdf_path='/pdfs/proposal/',
                pdf_prefix='P',
            )
            try:
                email_service.send_email(
                    to_email=to_email,
                    cc=cc,
                    subject=subject,
                )
                return Response({"message": "Email sent successfully."}, status=status.HTTP_200_OK)
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(email_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProposalCreateView(APIView):
    pass
class ProposalArchiveView(APIView):
    pass
class ProposalDeleteView(APIView):
    pass
