import datetime
import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from mysite.bidfilemgm.models import BidFile
from mysite.estimator.models import Estimate, EstimateDetails, EstimateEquipment
from mysite.estimator.templatetags.estimator_tags import pdf_filename_generator
from mysite.s3_file_manager import S3
from .serializers import EstimateSerializer, EmailSerializer
from .services import EstimateEmailService, TemplateService

logger = logging.getLogger(__name__)


class EstimateListView(APIView):
    """
    List, filter, and email estimates with pagination.

    This view provides an endpoint for authenticated users to retrieve a paginated
    list of estimates with search and date filters, and to send emails related to estimates.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="List estimates",
        manual_parameters=[
            openapi.Parameter(
                'search', openapi.IN_QUERY, description="Search term for estimates", type=openapi.TYPE_STRING),
            openapi.Parameter(
                'fromDate', openapi.IN_QUERY, description="Start date for filtering", type=openapi.TYPE_STRING),
            openapi.Parameter(
                'toDate', openapi.IN_QUERY, description="End date for filtering", type=openapi.TYPE_STRING),
            openapi.Parameter(
                'paginate_by', openapi.IN_QUERY, description="Number of items per page", type=openapi.TYPE_INTEGER),
            openapi.Parameter(
                'page', openapi.IN_QUERY, description="Page number to retrieve", type=openapi.TYPE_INTEGER),
        ],
        responses={200: openapi.Response("List of estimates returned successfully.")}
    )
    def get(self, request):
        search = request.GET.get('search', '')
        paginate_by = int(request.GET.get('paginate_by', settings.PAGE_SIZE))
        ordering = request.GET.get('ordering', '-created_on')
        from_date = request.GET.get("fromDate")
        to_date = request.GET.get("toDate")

        filters = Q(archive=False)
        if search:
            filters &= Q(id__icontains=search) | Q(project__name__icontains=search) | Q(customer__company__name__icontains=search)

        if from_date:
            from_date_obj = datetime.strptime(from_date, '%m/%d/%Y')
            filters &= Q(due_date__gte=from_date_obj)
        if to_date:
            to_date_obj = datetime.strptime(to_date, '%m/%d/%Y') + datetime.timedelta(days=1) - timedelta(seconds=1)
            filters &= Q(due_date__lte=to_date_obj)

        object_list = Estimate.objects.filter(filters).order_by(ordering)
        paginator = Paginator(object_list, paginate_by)
        page_number = request.GET.get('page', 1)
        paginated_estimates = paginator.get_page(page_number)

        serializer = EstimateSerializer(paginated_estimates, many=True)
        data = {
            'estimates': serializer.data,
            'pagination': {
                'total_rows': paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': paginated_estimates.number,
                'page_size': paginate_by,
            }
        }
        return Response(data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Send an email related to an estimate",
        request_body=EmailSerializer,
        responses={
            200: openapi.Response("Email sent successfully."),
            400: openapi.Response("Invalid email data provided."),
        },
    )
    def post(self, request):
        """
        Sends an email based on the provided validated data in the request.

        Args:
            request: The incoming HTTP request with email data.

        Returns:
            Response: JSON indicating the result of the email send operation.
        """
        serializer = EmailSerializer(data=request.data)
        if serializer.is_valid():
            to_emails = serializer.validated_data['to_email'].replace(" ", "").split(',')
            cc_emails = serializer.validated_data['cc'].replace(" ", "").split(',')
            email_id = serializer.validated_data['email_id']
            subject = serializer.validated_data['subject']

            email_service = EstimateEmailService(
                estimate_id=email_id,
                storage_service=S3(),
                template_service=TemplateService(),
                request=request,
                modules_to_email_template=1,
                pdf_path='/pdfs/estimate/',
                pdf_prefix='E',
            )
            try:
                email_service.send_email(
                    to_email=to_emails,
                    cc=cc_emails,
                    subject=subject,
                )
                return Response({"message": "Email sent successfully."}, status=status.HTTP_200_OK)
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EstimateCreateView(APIView):
    """
    API view to create a new estimate.

    This view handles the creation of a new estimate based on provided data.
    It accepts a POST request and returns the newly created estimate's ID along with associated BidFiles.

    Attributes:
        permission_classes (list): List of permissions required for this view.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Create a new estimate.",
        request_body=EstimateSerializer,
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Estimate created successfully",
                schema=EstimateSerializer(),
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Invalid data provided",
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="BidFile not found",
            ),
        }
    )
    def post(self, request, bid_file_id=None):
        """
        Handle POST request to create an estimate.

        Args:
            request (Request): The request object containing data to create the estimate.
            bid_file_id (int, optional): The ID of the BidFile associated with the estimate.

        Returns:
            Response: A response containing either the newly created estimate's ID or an error message,
                      along with the list of BidFiles if applicable.
        """
        logger.info("Request to create an estimate with bid_file_id: %s", bid_file_id)

        # Check if the BidFile exists if bid_file_id is provided
        if bid_file_id:
            bid_file = BidFile.objects.filter(id=bid_file_id).first()
            if not bid_file:
                logger.error("BidFile with ID %s not found", bid_file_id)
                return Response(
                    {"error": "BidFile not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Prepare the response with the single BidFile
            response_bid_files = [bid_file]  # Wrap in a list to maintain consistency
        else:
            # If no bid_file_id is provided, retrieve all relevant BidFiles
            response_bid_files = BidFile.objects.filter(
                archive=False
            ).exclude(
                id__in=Estimate.objects.filter(
                    bfm_id__isnull=False
                ).values_list('bfm_id')
            ).order_by('due_date')

        # Initialize the serializer with the request data
        serializer = EstimateSerializer(data=request.data)

        # Validate and save the estimate
        if serializer.is_valid():
            new_estimate = serializer.save(created_by=request.user)  # Save with user information
            logger.info("New estimate created with ID %s", new_estimate.pk)

            # Update EstimateDetails after creating the estimate
            EstimateDetails.objects.filter(
                estimate=new_estimate
            ).update(
                pre_demo=request.data.get(
                    'predemo', 0
                )
            )

            # Prepare the response
            response_data = {
                "message": "Estimate created",
                "estimate_id": new_estimate.pk,
                "bid_files_id": [bid_file.pk for bid_file in response_bid_files],  # Send only IDs for brevity
            }

            return Response(
                response_data,
                status=status.HTTP_201_CREATED,
            )

        logger.error(
            "Error creating estimate: %s",
            serializer.errors,
        )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class EstimateUpdateView(APIView):
    """
    API view to update or retrieve an existing estimate.

    This view handles the updating and retrieval of an existing estimate identified by estimate_id.
    It accepts PUT requests to update the estimate and GET requests to retrieve the estimate details.

    **Why use this view for frontend developers:**
    - **Unified API Endpoint**: This view provides both the update and retrieval functionalities for an estimate in one place, simplifying the API structure.
    - **Efficient Data Handling**: Frontend applications can easily fetch an estimate's current data and submit updates to the same endpoint, reducing the need for multiple API calls.
    - **Improved User Experience**: Users can load an estimate, make changes, and save them without navigating between different endpoints, leading to a more seamless experience.
    - **Maintainability**: Keeping related functionalities together in a single class makes it easier to manage and understand the codebase, promoting better collaboration between frontend and backend developers.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Update an existing estimate",
        operation_description=(
            "This endpoint allows updating an existing estimate by ID. "
            "Frontend developers can use this to send updated estimate data "
            "to the server and receive confirmation of the update."
        ),
        responses={
            200: openapi.Response(
                description="Estimate updated successfully",
                examples={
                    "application/json": {
                        "message": "Estimate updated",
                        "estimate_id": 1
                    }
                }
            ),
            400: openapi.Response(
                description="Bad request with validation errors",
                examples={
                    "application/json": {
                        "error": "Validation error details"
                    }
                }
            ),
            404: "Estimate not found"
        },
        request_body=EstimateSerializer,
    )
    def put(self, request, estimate_id):
        logger.info("Request to update estimate with ID: %s", estimate_id)
        this_estimate = get_object_or_404(Estimate, id=estimate_id)

        # Initialize the serializer with the current estimate instance and incoming data
        serializer = EstimateSerializer(
            this_estimate,
            data=request.data,
            partial=True  # Allow partial updates
        )

        # Check for cancel request
        if request.data.get("cancel"):
            logger.info("Estimate update operation cancelled.")
            return Response(
                {"message": "Operation cancelled"},
                status=status.HTTP_200_OK,
            )

        # Validate and save the estimate
        if serializer.is_valid():
            updated_estimate = serializer.save(created_by=request.user)
            EstimateDetails.objects.filter(
                estimate=updated_estimate
            ).update(
                pre_demo=request.data.get(
                    'predemo', 0
                )
            )
            # Update EstimateEquipment flags based on services
            estimate_equipments = EstimateEquipment.objects.filter(
                estimate=updated_estimate
            )
            for equipment in estimate_equipments:
                equipment.flag = equipment.equipment.service in updated_estimate.service.all()
                equipment.save()

            logger.info("Estimate with ID %s updated.", updated_estimate.pk)
            return Response(
                {"message": "Estimate updated",
                 "estimate_id": updated_estimate.pk},
                status=status.HTTP_200_OK,
            )

        logger.error("Error updating estimate: %s", serializer.errors)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @swagger_auto_schema(
        operation_summary="Retrieve an estimate",
        operation_description=(
            "Get details of an existing estimate by ID. "
            "This endpoint allows frontend developers to fetch the current data "
            "for an estimate before making updates, facilitating a smoother user workflow."
        ),
        responses={
            200: openapi.Response(
                description="Estimate retrieved successfully",
                schema=EstimateSerializer
            ),
            404: "Estimate not found"
        }
    )
    def get(self, request, estimate_id):
        """
        Handle GET request to retrieve an estimate by ID.
        """
        this_estimate = get_object_or_404(Estimate, id=estimate_id)
        serializer = EstimateSerializer(this_estimate)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EstimateDeleteView(APIView):
    """
    API view to delete an existing estimate.

    This view handles the deletion of an existing estimate identified by estimate_id.
    It accepts a DELETE request and returns a success message upon deletion.

    **Authorization Logic**:
    - Only the user who created the estimate or users with a specific user type (e.g., admin) can delete the estimate.
    - If the estimate has associated BFM data, it will be archived before deletion.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Delete an existing estimate",
        operation_description=(
                "This endpoint allows deletion of an existing estimate by ID. "
                "Only the creator of the estimate or an authorized user can perform this action. "
                "The request must include confirmation to proceed with the deletion."
        ),
        responses={
            204: openapi.Response(
                description="Estimate deleted successfully"
            ),
            403: openapi.Response(
                description="Forbidden: User not authorized to delete this estimate",
                examples={
                    "application/json": {
                        "error": "You are not authorized to delete this record."
                    }
                }
            ),
            404: "Estimate not found"
        },
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'confirm': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Confirmation to delete the estimate")
            },
            required=['confirm']
        )
    )
    def delete(self, request, estimate_id):
        logger.info("Request to delete estimate with ID: %s", estimate_id)

        # Fetch the estimate object
        estimate = get_object_or_404(Estimate, id=estimate_id)

        # Check if the user is authorized to delete the estimate
        if estimate.created_by != request.user and request.user.profile.user_type != 2:
            logger.warning("Unauthorized deletion attempt by user: %s", request.user.username)
            return Response(
                {"error": "You are not authorized to delete this record."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if the confirmation flag is set
        if not request.data.get("confirm"):
            return Response(
                {"error": "Deletion must be confirmed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Archive related BFM data if applicable
        if estimate.bfm:
            estimate.bfm.archive = False
            estimate.bfm.save()

        # todo: check PDF deletion (assumed method from old code) is work ok?
        estimate.delete_estimate_pdf({'file_name': pdf_filename_generator(estimate.id, 'E')})

        # Delete the estimate
        estimate.delete()
        logger.info("Estimate with ID %s deleted.", estimate_id)
        return Response(
            {"message": "Estimate deleted"},
            status=status.HTTP_204_NO_CONTENT,
        )
