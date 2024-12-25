from datetime import datetime, timedelta

from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404
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
from .schemas import ProposalResponseModel
from .serializers import ProposalSerializer
from .services import ProposalService
from ..estimator.serializers import EmailSerializer, EstimateSerializer
from ..estimator.services import TemplateService, EstimateEmailService


class ProposalListView(APIView):
    """
    List and filter proposals with pagination.

    Provides endpoints for authenticated users to retrieve and filter a paginated list of proposals.
    Allows optional search by estimate ID, project name, and customer company name, with date filtering.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        search = request.GET.get('search', '')
        paginate_by = int(request.GET.get('paginate_by', settings.PAGE_SIZE))
        ordering = request.GET.get('ordering', '-created_on')

        # Basic filters
        filters = Q(archive=False, is_deleted=False)

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
    """
    API endpoint for creating a proposal.

    Handles form data for creating a new proposal, associates it with an estimate,
    and generates a proposal PDF if the form data is valid.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    @staticmethod
    def get_license_info():
        """Fetches license and owner information for the proposal document."""
        return {
            'license_owner': LicenseInfo.objects.get(key='OwnerName').value,
            'owner_title': LicenseInfo.objects.get(key='OwnerTitle').value,
            'owner_address_line1': LicenseInfo.objects.get(key='OwnerAddressLine1').value,
            'owner_address_line2': LicenseInfo.objects.get(key='OwnerAddressLine2').value,
            'owner_tel': LicenseInfo.objects.get(key='OwnerTel').value,
            'owner_fax': LicenseInfo.objects.get(key='OwnerFax').value,
            'owner_web': LicenseInfo.objects.get(key='OwnerWeb').value,
            'owner_mail': LicenseInfo.objects.get(key='OwnerMail').value,
            'owner_signature': LicenseFiles.objects.get(key='OwnerSignature').value,
            'owner_logo': LicenseFiles.objects.get(key='OwnerLogo').value,
            'company_name': LicenseInfo.objects.get(key='CompanyName').value,
            'pdf_header_logo': LicenseFiles.objects.get(key='PDFHeaderLogo').value,
            'pdf_header_text': LicenseInfo.objects.get(key='PDFHeaderText').value,
        }

    @staticmethod
    def get_user_info(user):
        """Fetches user information for proposal document, providing defaults if values are missing."""
        user_profile = getattr(user, 'profile', None)
        return {
            'user_name': f"{user.first_name} {user.last_name}" if user.last_name else "TAB Technologies, INC. Operator",
            'user_title': user_profile.title if user_profile and user_profile.title else 'Estimator',
            'user_signature': user_profile.e_sign if user_profile else None,
            'user_cell': user_profile.cell if user_profile and user_profile.cell else '',
        }

    def get(self, request, estimate_id=None):
        """
        Retrieves available estimates that are not archived or associated with a proposal.

        Parameters:
            - estimate_id (int): Optional; filters by specific estimate ID.

        Returns:
            - Response: Serialized data of estimates.
        """
        if estimate_id:
            estimate = Estimate.objects.filter(id=estimate_id)
        else:
            estimate = Estimate.objects.filter(
                archive=False
            ).exclude(
                id__in=Proposal.objects.values_list('estimate_id', flat=True)
            ).order_by('-created_on')

        serializer = EstimateSerializer(estimate, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Creates a new proposal and generates a PDF document.
        """
        # Proposal creation logic
        serializer = ProposalSerializer(data=request.data)
        if serializer.is_valid():
            proposal = serializer.save()

            # Fetch license and user information
            license_info = self.get_license_info()
            user_info = self.get_user_info(request.user)

            # Prepare parameters for the proposal PDF
            parameters = {
                'file_name': pdf_filename_generator(proposal.estimate.id, 'P'),
                'other_than_dalt_services': proposal.estimate.service.exclude(name__iexact="DALT"),
                'has_dalt': proposal.estimate.service.filter(name__iexact="DALT").exists(),
                'proposal': proposal,
                'estimate': proposal.estimate,
                'predemo_calculated': proposal.estimate.estimatedetails.pre_demo * 1200,
                **license_info,
                **user_info,
            }

            # Generate the proposal PDF
            proposal_service = ProposalService()
            pdf_path = proposal_service.create_proposal_pdf(parameters=parameters)

            # Prepare and return response
            response_data = ProposalResponseModel(
                proposal_id=proposal.id,
                pdf_path=pdf_path,
                message="Proposal created successfully."
            )
            return Response(response_data.dict(), status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProposalArchiveView(APIView):
    """
    Archives a proposal if the user is authorized.
     """
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        proposal = get_object_or_404(
            Proposal,
            id=id,
            is_deleted=False,

        )

        if proposal.estimate.created_by == request.user or request.user.profile.user_type == 2:
            proposal.archive_record()  # Use the archive_record method from BaseModel
            return Response(
                {"message": "Proposal archived successfully"},
                status=status.HTTP_200_OK
            )

        return Response(
            {"error": "You are not authorized to archive this record."},
            status=status.HTTP_403_FORBIDDEN
        )


class ProposalDeleteView(APIView):
    """
    Deletes a proposal if the user is authorized.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, proposal_id):
        proposal = get_object_or_404(
            Proposal,
            id=proposal_id,
            is_deleted=False,

        )

        if proposal.estimate.created_by == request.user or request.user.profile.user_type == 2:
            file_name = pdf_filename_generator(proposal.estimate.id, 'P')
            proposal_service = ProposalService()
            proposal_service.delete_proposal_pdf(file_name)
            proposal.soft_delete()
            return Response(
                {"message": "Proposal soft_delete successfully"},
                status=status.HTTP_200_OK
            )

        return Response(
            {"error": "You are not authorized to delete this record."},
            status=status.HTTP_403_FORBIDDEN
        )
