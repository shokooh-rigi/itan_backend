import datetime
import logging
from copy import deepcopy
from datetime import datetime, timedelta

from django.conf import settings
from django.core.paginator import Paginator
from django.db import DatabaseError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from mysite.bidfilemgm.models import BidFile
from mysite.core.models import Person, LicenseFiles, LicenseInfo
from mysite.equipments.models import Equipment
from mysite.estimator.models import Estimate, EstimateDetails, EstimateEquipment, EstimateHistory
from mysite.estimator.templatetags.estimator_tags import pdf_filename_generator
from mysite.gi.models import InvoiceHistory
from mysite.order.templatetags.order_tags import calculate_total_amount_due, calculate_total_paid, \
    calculate_remaining_invoice_due
from mysite.s3_file_manager import S3
from .serializers import EstimateSerializer, EmailSerializer, EstimateEquipmentSerializer, EstimateDetailsSerializer, \
    EstimateHistorySerializer
from .services import EstimateEmailService, TemplateService
from ..proposal.services import ProposalService

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
            estimate.bfm.unarchive_record()

        # todo: check PDF deletion (assumed method from old code) is work ok?
        estimate.delete_estimate_pdf({'file_name': pdf_filename_generator(estimate.id, 'E')})

        # Delete the estimate
        estimate.soft_delete()
        logger.info("Estimate with ID %s deleted.", estimate_id)
        return Response(
            {"message": "Estimate  soft deleted"},
            status=status.HTTP_204_NO_CONTENT,
        )


class EstimateArchiveView(APIView):
    """
    Archives an estimate if the user is authorized and confirms the action.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Archives an estimate if the user is authorized and confirms the action.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'confirm': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Confirmation to archive the estimate')
            },
            required=['confirm']
        ),
        responses={
            200: openapi.Response(description="Estimate archived successfully"),
            400: openapi.Response(description="Confirmation not received for archiving."),
            403: openapi.Response(description="User is not authorized to archive this record.")
        }
    )
    def post(self, request, estimate_id):
        estimate = get_object_or_404(Estimate, id=estimate_id)

        # Check user authorization
        if estimate.created_by != request.user and request.user.profile.user_type != 2:
            return Response(
                {"error": "You are not authorized to archive this record."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check for confirmation
        if not request.data.get("confirm"):
            return Response(
                {"error": "Confirmation not received for archiving."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Archive associated BFM record if it exists
        if estimate.bfm:
            estimate.bfm.archive_record()

        # Archive the estimate using archive_record()
        estimate.archive_record()

        return Response(
            {"message": "Estimate archived successfully"},
            status=status.HTTP_200_OK
        )


class EstimateHistoryView(APIView):
    """
    View the history of an estimate.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_description="Get the history of an estimate.")
    def get(self, request, estimate_id):
        """
        Get the history of an estimate by ID.
        """
        estimate = get_object_or_404(Estimate, id=estimate_id)
        estimate_histories = EstimateHistory.objects.filter(estimate=estimate)

        data = {
            'estimate_id': estimate.id,
            'estimate_histories': EstimateHistorySerializer(estimate_histories, many=True).data
        }

        return Response(data)


class EstimateDetailsView(APIView):
    """
    View and update details of an estimate.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_description="Get or update the details of an estimate.")
    def get(self, request, estimate_id):
        """
        Get the details of the estimate.
        """
        estimate = get_object_or_404(Estimate, id=estimate_id)
        estimate_details = get_object_or_404(EstimateDetails, estimate=estimate)
        estimate_equipments_pricing = EstimateEquipment.objects.filter(estimate=estimate, flag=True)

        estimate_sub = sum(
            float(eq.price_override if eq.price_override else eq.equipment.price) * float(eq.quantity)
            for eq in estimate_equipments_pricing
        )

        data = {
            "estimate_id": estimate_id,
            "estimate": EstimateSerializer(estimate).data,
            "estimate_details": EstimateDetailsSerializer(estimate_details).data,
            "estimate_sub": estimate_sub,
            "estimate_equipments_pricing": EstimateEquipmentSerializer(estimate_equipments_pricing, many=True).data
        }

        return Response(data=data, status=status.HTTP_200_OK)

    @swagger_auto_schema(operation_description="Update the details of the estimate.")
    def post(self, request, estimate_id):
        """
        Update the details of an estimate.
        """
        estimate = get_object_or_404(Estimate, id=estimate_id)
        estimate_details = get_object_or_404(EstimateDetails, estimate=estimate)
        # Add form processing and save logic here, similar to your original function

        # Example of how to update estimate details
        serializer = EstimateDetailsSerializer(estimate_details, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EstimateEquipmentDeleteView(APIView):
    """
    Delete the Estimate Equipment record.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_description="Delete the estimate equipment by ID.")
    def delete(self, request, estimate_equipment_id):
        """
        Delete the estimate equipment by ID if confirmed.
        """
        # todo: what is used for: interval_id?
        estimate_equipment = get_object_or_404(EstimateEquipment, id=estimate_equipment_id)

        # Ensure confirmation is received before proceeding with deletion
        if request.data.get("confirm"):
            estimate_equipment.soft_delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {"detail": "Confirmation required to delete."},
            status=status.HTTP_400_BAD_REQUEST
        )


class EstimateDuplicateView(APIView):
    """
    Duplicates an estimate along with associated records if the user is authorized.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Duplicates an estimate with associated records.",
        responses={
            200: openapi.Response(description="Estimate duplicated successfully"),
            400: openapi.Response(description="Invalid data provided for duplication."),
            403: openapi.Response(description="You are not authorized to duplicate this record.")
        }
    )
    def post(self, request, estimate_id):
        this_estimate = get_object_or_404(Estimate, id=estimate_id)

        # todo: Ask to is directly get the customer from the request data ??
        customer_id = request.data.get("customer")
        if not customer_id:
            return Response(
                {"error": "Customer ID is required for duplication."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Duplicate the estimate object
        duplicated_obj = deepcopy(this_estimate)
        duplicated_obj.id = None  # Reset the ID to create a new instance

        # Duplicate BidFile if it exists
        if this_estimate.bfm:
            duplicated_bfm = deepcopy(this_estimate.bfm)
            duplicated_bfm.id = None
            duplicated_bfm.save()
            duplicated_obj.bfm = duplicated_bfm

        # Set the new customer for the duplicated estimate
        duplicated_obj.customer = get_object_or_404(Person, id=customer_id)
        duplicated_obj.save()

        # Duplicate services associated with the estimate
        duplicated_obj.service.set(this_estimate.service.all())

        # Duplicate EstimateEquipment records
        all_equipments = EstimateEquipment.objects.filter(estimate=this_estimate)
        for equipment in all_equipments:
            equipment.pk = None
            equipment.estimate = duplicated_obj
            equipment.save()

        # Duplicate EstimateDetails if it exists
        try:
            estimate_detail = deepcopy(EstimateDetails.objects.get(estimate=this_estimate))
            estimate_detail.id = None
            estimate_detail.estimate = duplicated_obj
            estimate_detail.save()
        except EstimateDetails.DoesNotExist:
            pass

        return Response(
            {"message": "Estimate duplicated successfully"},
            status=status.HTTP_200_OK
        )


class EstimateEquipmentView(APIView):
    """
    Handles equipment-related operations for an estimate, including
    retrieving equipment pricing details and adding or updating equipment.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieves equipment details for an estimate service, including pricing information.",
        responses={
            200: openapi.Response(
                description="Returns the equipment details and total estimate price.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'estimate_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'estimate_money': openapi.Schema(type=openapi.TYPE_NUMBER),
                        'interval_set': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'estimate_service_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'equipments': openapi.Schema(type=openapi.TYPE_ARRAY,
                                                     items=openapi.Items(type=openapi.TYPE_INTEGER)),
                        'equipment_in': openapi.Schema(type=openapi.TYPE_ARRAY,
                                                       items=openapi.Items(type=openapi.TYPE_INTEGER)),
                    }
                ),
            ),
            404: "Estimate not found.",
            500: "Internal server error.",
        }
    )
    def get(self, request, estimate_id, estimate_service_id):
        """
        Retrieves equipment and pricing data for a specific estimate and service interval.

        Arguments:
            estimate_id (int): The ID of the estimate.
            estimate_service_id (int): The ID of the service interval.

        Returns:
            Response: The equipment details and total pricing.
        """
        estimate = get_object_or_404(Estimate, id=estimate_id)
        interval_set = estimate.service.all()[estimate_service_id]

        try:
            # Get the equipment pricing data
            estimate_equipments_pricing = EstimateEquipment.objects.filter(estimate=estimate, flag=True)
            estimate_money = sum(
                (float(e.price_override) if e.price_override else float(e.equipment.price)) * float(e.quantity)
                for e in estimate_equipments_pricing
            )

            # Filter equipment based on the service interval
            equipments = Equipment.objects.filter(service=interval_set.id)
            equipment_in = [item.equipment.id for item in estimate_equipments_pricing]

            return Response({
                'estimate_id': estimate_id,
                'estimate_money': estimate_money,
                'interval_set': interval_set.id,
                'estimate_service_id': estimate_service_id,
                'equipments': [equipment.id for equipment in equipments],
                'equipment_in': equipment_in
            })

        except DatabaseError:
            return Response(
                {"error": "An error occurred while retrieving the equipment details."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="Adds or updates equipment for an estimate service.",
        request_body=EstimateEquipmentSerializer,
        responses={
            200: openapi.Response(
                description="Equipment added/updated successfully.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'estimate_money': openapi.Schema(type=openapi.TYPE_NUMBER),
                    }
                )
            ),
            400: openapi.Response(description="Invalid input data."),
            404: "Estimate not found.",
            500: "Internal server error.",
        }
    )
    def post(self, request, estimate_id):
        """
        Adds or updates equipment for a specific estimate and service interval.

        Arguments:
            estimate_id (int): The ID of the estimate.

        Returns:
            Response: Success message and updated estimate pricing.
        """
        estimate = get_object_or_404(Estimate, id=estimate_id)
        serializer = EstimateEquipmentSerializer(data=request.data, context={'estimate_id': estimate_id})

        if serializer.is_valid():
            try:
                equipment = serializer.validated_data['equipment']
                quantity = serializer.validated_data['quantity']
                price_override = serializer.validated_data['price_override']

                # Check if the equipment already exists in the estimate
                existing_equipment = EstimateEquipment.objects.filter(estimate=estimate_id, equipment=equipment).first()
                if existing_equipment:
                    # Update existing equipment pricing
                    existing_equipment.quantity = quantity
                    existing_equipment.price_override = price_override
                    existing_equipment.save()
                else:
                    # Create a new EstimateEquipment entry
                    EstimateEquipment.objects.create(
                        estimate=estimate,
                        equipment=equipment,
                        quantity=quantity,
                        price_override=price_override,
                        flag=True
                    )

                # Recalculate the total price
                estimate_equipments_pricing = EstimateEquipment.objects.filter(estimate=estimate, flag=True)
                estimate_money = sum(
                    (float(e.price_override) if e.price_override else float(e.equipment.price)) * float(e.quantity)
                    for e in estimate_equipments_pricing
                )

                return Response({
                    'message': 'Estimate equipment updated successfully.',
                    'estimate_money': estimate_money
                }, status=status.HTTP_200_OK)

            except DatabaseError:
                return Response(
                    {"error": "An error occurred while updating the equipment."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EstimateBidView(APIView):
    """
    Generate the bid for an estimate.
    """
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _get_license_info():
        """
        Retrieve required license information and files.
        """
        required_keys = [
            'OwnerName', 'OwnerTitle', 'OwnerAddressLine1', 'OwnerAddressLine2',
            'OwnerTel', 'OwnerFax', 'OwnerWeb', 'OwnerMail', 'PDFHeaderText',
            'CompanyName'
        ]
        required_files = ['OwnerSignature', 'OwnerLogo', 'PDFHeaderLogo']

        license_info = {
            info['key']: info['value']
            for info in LicenseInfo.objects.filter(key__in=required_keys).values('key', 'value')
        }

        license_files = {
            file['key']: file['value']
            for file in LicenseFiles.objects.filter(key__in=required_files).values('key', 'value')
        }

        return license_info, license_files

    @staticmethod
    def _estimate_total_work(estimate_id: int):
        """
        Calculate the total work based on estimate equipment.
        """
        estimate_equipments = EstimateEquipment.objects.filter(estimate=estimate_id, flag=True)
        estimate_work = sum(
            int(each_estimate_equipment.quantity) * int(each_estimate_equipment.equipment.estimate_work)
            for each_estimate_equipment in estimate_equipments
        )
        return estimate_work

    @staticmethod
    def _estimate_equipments(estimate_id: int):
        estimate_equipments = EstimateEquipment.objects.filter(estimate=estimate_id, flag=True)
        return estimate_equipments

    @staticmethod
    def _calculate_estimate_totals(estimate, estimate_sub):
        """
        Calculate control system, hours, predemo, and final estimate total.
        """
        control_system_calculated = round(
            (estimate_sub * (1 + estimate.estimatedetails.control_system / 100)) - estimate_sub, 2
        )
        hours_calculated = round(
            (estimate_sub * (1 + estimate.estimatedetails.hours / 100)) - estimate_sub, 2
        )
        predemo_calculated = estimate.estimatedetails.pre_demo * 1200

        estimate_total = round(
            estimate_sub + control_system_calculated + hours_calculated + predemo_calculated +
            float(estimate.estimatedetails.adjustment) + float(estimate.estimatedetails.customer_adjustment), 2
        )
        return control_system_calculated, hours_calculated, predemo_calculated, estimate_total

    @staticmethod
    def _generate_invoice_history(estimate):
        """
        Generate and log the invoice history for the estimate.
        """
        try:
            invoice = estimate.proposal.order.invoice
            invoice.times_estimate_changed += 1
            invoice.save()

            total_count = InvoiceHistory.objects.filter(invoice=invoice).count() + 1
            invoice_file_name = f"Invoice-{estimate.proposal.order.project_number[3:]:0>3}-{invoice.id:0>3}-{total_count}"

            InvoiceHistory.objects.create(
                invoice=invoice,
                total_invoiced=calculate_total_amount_due(invoice),
                total_paid=calculate_total_paid(invoice),
                balance_due=calculate_remaining_invoice_due(invoice),
                pdf_filename=invoice_file_name
            )
            return None
        except Exception as e:
            return str(e)

    @staticmethod
    def _prepare_response_data(
            request,
            estimate,
            license_info,
            license_files,
            estimate_totals,
            estimate_work,
            estimate_equipments,
    ):
        """
        Prepare the final response data dictionary.
        """
        control_system_calculated, hours_calculated, predemo_calculated, estimate_total = estimate_totals
        estimate_sub = sum(
            float(eq.price_override if eq.price_override else eq.equipment.price) * float(eq.quantity)
            for eq in EstimateEquipment.objects.filter(estimate=estimate, flag=True)
        )
        estimate_file_name = pdf_filename_generator(estimate.id, 'E')

        return {
            'file_name': estimate_file_name,
            'estimate': estimate,
            'other_than_dalt_services': estimate.service.exclude(name__iexact="DALT"),
            'has_dalt': estimate.service.filter(name__iexact="DALT").exists(),
            'estimate_equipments_pricing': estimate_equipments(estimate_id=estimate.id),
            'estimate_work_in_hours': int(estimate_work / 60),
            'estimate_work_in_minutes': int(estimate_work % 60),
            **license_info,
            **license_files,
            'pdf_header_logo': license_files.get('PDFHeaderLogo'),
            'company_name': license_info.get('CompanyName'),
            'estimate_id': estimate.id,
            'estimate_sub': estimate_sub,
            'estimate_total': estimate_total,
            'control_system_calculated': control_system_calculated,
            'hours_calculated': hours_calculated,
            'predemo_calculated': predemo_calculated,
            'datetime': datetime.datetime.now(),
            'user_name': f"{request.user.first_name} {request.user.last_name or 'TAB Technologies, INC. Operator'}",
            'user_title': request.user.profile.title or 'Estimator',
            'user_signature': request.user.profile.e_sign,
            'user_cell': request.user.profile.cell or '',
        }

    @swagger_auto_schema(operation_description="Generate and retrieve the estimate bid.")
    def get(self, request, estimate_id):
        """
        Generate and return the estimate bid with relevant data.
        """
        try:
            license_info, license_files = self._get_license_info()
            estimate = get_object_or_404(Estimate, id=estimate_id)
            estimate_sub = sum(
                float(eq.price_override if eq.price_override else eq.equipment.price) * float(eq.quantity)
                for eq in EstimateEquipment.objects.filter(estimate=estimate, flag=True)
            )
            estimate_work = self._estimate_total_work(estimate_id=estimate_id)
            estimate_totals = self._calculate_estimate_totals(estimate, estimate_sub)
            estimate_equipments = self._estimate_equipments(estimate_id=estimate_id)

            invoice_error = self._generate_invoice_history(estimate)
            response_data = self._prepare_response_data(
                request=request,
                estimate=estimate,
                license_info=license_info,
                license_files=license_files,
                estimate_totals=estimate_totals,
                estimate_work=estimate_work,
                estimate_equipments=estimate_equipments,
            )

            if invoice_error:
                response_data['invoice_error'] = invoice_error

            return Response(response_data, status=status.HTTP_200_OK)

        except Estimate.DoesNotExist:
            return Response({"error": "Estimate not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
