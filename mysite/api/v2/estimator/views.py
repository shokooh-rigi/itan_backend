import datetime
import logging
from copy import deepcopy
from datetime import datetime, timedelta

from django.conf import settings
from django.core.paginator import Paginator
from django.db import DatabaseError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter, extend_schema_view
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

if settings.TAB_SYSTEM:
    from mysite.api.v2.invoice.services.invoice_services import InvoiceService
from mysite.bidfilemgm.models import BidFile
from mysite.core.models import Person, LicenseFiles, LicenseInfo
from mysite.equipments.models import Equipment
from mysite.estimator.models import (
    Estimate,
    EstimateDetails,
    EstimateEquipment,
    EstimateHistory,
)
from mysite.estimator.templatetags.estimator_tags import pdf_filename_generator
from mysite.s3_file_manager import S3
from .serializers import (
    EstimateSerializer,
    EmailSerializer,
    EstimateEquipmentSerializer,
    EstimateDetailsSerializer,
    EstimateHistorySerializer,
)
from .services import EstimateEmailService, TemplateService
from ..bid.serializers import BidSerializer

logger = logging.getLogger(__name__)


class EstimateListView(APIView):
    """
    List, filter, and email estimates with pagination.

    This view provides an endpoint for authenticated users to retrieve a paginated
    list of estimates with search and date filters, and to send emails related to estimates.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get a list of estimates",
        operation_description="Retrieve a paginated list of estimates with optional search and date filters.",
        manual_parameters=[
            openapi.Parameter(
                "search",
                openapi.IN_QUERY,
                description="Search term for filtering estimates by ID, project name, or customer company name.",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "page_size",
                openapi.IN_QUERY,
                description="Number of estimates to display per page. Default is set in settings.PAGE_SIZE.",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "ordering",
                openapi.IN_QUERY,
                description="Field to order the estimates by. Default is '-created_on'.",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "fromDate",
                openapi.IN_QUERY,
                description="Start date for filtering estimates (format: MM/DD/YYYY).",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "toDate",
                openapi.IN_QUERY,
                description="End date for filtering estimates (format: MM/DD/YYYY).",
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
                description="List of estimates with pagination.",
                examples={
                    "application/json": {
                        "estimates": [
                            {
                                "bfm": "value",
                                "customer": "customer_data",
                                "customer_name": "customer_name",
                                "project": "project_data",
                                "project_name": "project_name",
                                "engineer": "engineer_data",
                                "service": "service_data",
                                "note": "note_data",
                                "due_date": "YYYY-MM-DD",
                                "drawing_date": "YYYY-MM-DD",
                                "predemo": 0,
                                "created_by": "user_id",
                            }
                        ],
                        "pagination": {
                            "total_rows": 100,
                            "total_pages": 10,
                            "current_page": 1,
                            "page_size": 10,
                        },
                    }
                },
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Invalid parameters.",
            ),
        },
    )
    def get(self, request):

        search = request.GET.get("search", "")
        page_size = int(request.GET.get("page_size", settings.PAGE_SIZE))
        ordering = request.GET.get("ordering", "-created_on")
        from_date = request.GET.get("fromDate")
        to_date = request.GET.get("toDate")

        filters = Q(archive=False, is_deleted=False)
        if search:
            filters &= (
                Q(id__icontains=search)
                | Q(project__name__icontains=search)
                | Q(customer__company__name__icontains=search)
            )

        if from_date:
            from_date_obj = datetime.strptime(from_date, "%m/%d/%Y")
            filters &= Q(due_date__gte=from_date_obj)
        if to_date:
            to_date_obj = (
                datetime.strptime(to_date, "%m/%d/%Y")
                + datetime.timedelta(days=1)
                - timedelta(seconds=1)
            )
            filters &= Q(due_date__lte=to_date_obj)

        object_list = Estimate.objects.filter(filters).order_by(ordering)
        paginator = Paginator(object_list, page_size)
        page_number = request.GET.get("page", 1)
        paginated_estimates = paginator.get_page(page_number)

        try:
            serializer = EstimateSerializer(paginated_estimates, many=True)
            data = {
                "estimates": serializer.data,
                "pagination": {
                    "total_rows": paginator.count,
                    "total_pages": paginator.num_pages,
                    "current_page": paginated_estimates.number,
                    "page_size": page_size,
                },
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response(
                {"error": "An error occurred while retrieving the estimates."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_summary="Send an email for an estimate",
        operation_description="Sends an email based on the provided validated data in the request body.",
        request_body=EmailSerializer,
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Email sent successfully.",
                examples={"application/json": {"message": "Email sent successfully."}},
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Invalid input or email sending error.",
                examples={"application/json": {"error": "Invalid email data."}},
            ),
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
            to_emails = (
                serializer.validated_data["to_email"].replace(" ", "").split(",")
            )
            cc_emails = serializer.validated_data["cc"].replace(" ", "").split(",")
            email_id = serializer.validated_data["email_id"]
            subject = serializer.validated_data["subject"]

            email_service = EstimateEmailService(
                estimate_id=email_id,
                storage_service=S3(),
                template_service=TemplateService(),
                request=request,
                modules_to_email_template=1,
                pdf_path="/pdfs/estimate/",
                pdf_prefix="E",
            )
            try:
                email_service.send_email(
                    to_email=to_emails,
                    cc=cc_emails,
                    subject=subject,
                )
                return Response(
                    {"message": "Email sent successfully."}, status=status.HTTP_200_OK
                )
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EstimateCreateView(APIView):
    """
    API view to create a new estimate.

    Handles creation of a new estimate and optionally associates it with a BidFile.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Create a new estimate",
        operation_description="Create a new estimate based on the provided data. Optionally associate it with a BidFile.",
        request_body=EstimateSerializer,
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Estimate created successfully.",
                examples={
                    "application/json": {
                        "message": "Estimate created",
                        "estimate_id": 123,
                        "bid_files_id": [1, 2, 3],
                    }
                },
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Invalid input data.",
                examples={
                    "application/json": {
                        "error": "Validation errors",
                        "field_name": ["This field is required."],
                    }
                },
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="BidFile not found.",
                examples={
                    "application/json": {
                        "error": "BidFile not found",
                    }
                },
            ),
        },
    )
    def post(self, request):
        """
        Handle POST request to create an estimate.

        Args:
            request (Request): The request object containing data to create the estimate.

        Returns:
            Response: A response containing either the newly created estimate's ID or an error message,
                      along with the list of BidFiles if applicable.
        """
        logger.info("Request to create an estimate")

        # Initialize the serializer with the request data
        serializer = EstimateSerializer(data=request.data)

        # Validate and save the estimate
        if serializer.is_valid():
            # Handle the creation process
            try:
                new_estimate = serializer.save(
                    created_by=request.user
                )  # Save with user information
                logger.info("New estimate created with ID %s", new_estimate.pk)

                # Update EstimateDetails if required
                pre_demo = request.data.get("predemo", 0)
                EstimateDetails.objects.filter(
                    estimate=new_estimate,
                    is_deleted=False,
                ).update(pre_demo=pre_demo)

                # Prepare the response
                response_data = {
                    "message": "Estimate created",
                    "estimate_id": new_estimate.pk,
                }
                return Response(response_data, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error("Error creating estimate: %s", str(e))
                return Response(
                    {"error": "An unexpected error occurred."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        logger.error("Validation errors: %s", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EstimateUpdateView(APIView):
    """
    API view to update an existing estimate.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Update an existing estimate by its ID.",
        manual_parameters=[
            openapi.Parameter(
                "id",
                openapi.IN_PATH,
                description="The ID of the estimate to update",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        request_body=EstimateSerializer,
        responses={
            200: openapi.Response(
                description="Estimate updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING, description="A success message"
                        ),
                        "estimate_id": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="The ID of the updated estimate",
                        ),
                    },
                ),
            ),
            400: openapi.Response(
                description="Bad request, invalid data",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(
                            type=openapi.TYPE_STRING, description="Error message"
                        )
                    },
                ),
            ),
            404: "Estimate not found",
        },
    )
    def put(self, request, id):
        logger.info("Request to update estimate with ID: %s", id)
        this_estimate = get_object_or_404(
            Estimate,
            id=id,
            is_deleted=False,
        )

        # Initialize the serializer with the current estimate instance and incoming data
        serializer = EstimateSerializer(
            this_estimate, data=request.data, partial=True  # Allow partial updates
        )

        # Validate and save the estimate
        if serializer.is_valid():
            updated_estimate = serializer.save(created_by=request.user)
            EstimateDetails.objects.filter(
                estimate=updated_estimate,
                is_deleted=False,
            ).update(pre_demo=request.data.get("predemo", 0))
            # Update EstimateEquipment flags based on services
            estimate_equipments = EstimateEquipment.objects.filter(
                estimate=updated_estimate,
                is_deleted=False,
            )
            for equipment in estimate_equipments:
                equipment.flag = (
                    equipment.equipment.service in updated_estimate.service.all()
                )
                equipment.save()

            logger.info("Estimate with ID %s updated.", updated_estimate.pk)
            return Response(
                {"message": "Estimate updated", "estimate_id": updated_estimate.pk},
                status=status.HTTP_200_OK,
            )

        logger.error("Error updating estimate: %s", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EstimateDeleteView(APIView):
    """
    API view to delete an existing estimate.

    This view handles the deletion of an existing estimate identified by id.
    It accepts a DELETE request and returns a success message upon deletion.

    **Authorization Logic**:
    - Only the user who created the estimate or users with a specific user type (e.g., admin) can delete the estimate.
    - If the estimate has associated Bid data, it will be archived before deletion.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Delete an existing estimate",
        operation_description=(
            "Delete an estimate identified by its ID. Only the user who created the estimate "
            "or admin users (user_type=2) are authorized to perform this action. "
            "If the estimate has associated Bid data, it will be archived before deletion."
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Estimate soft deleted successfully.",
                examples={"application/json": {"message": "Estimate soft deleted"}},
            ),
            status.HTTP_403_FORBIDDEN: openapi.Response(
                description="Unauthorized deletion attempt.",
                examples={
                    "application/json": {
                        "error": "You are not authorized to delete this record."
                    }
                },
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Estimate not found.",
                examples={"application/json": {"error": "Estimate not found"}},
            ),
        },
    )
    def delete(self, request, id):
        logger.info("Request to delete estimate with ID: %s", id)

        # Fetch the estimate object
        estimate = get_object_or_404(
            Estimate,
            id=id,
            is_deleted=False,
        )

        # Check if the user is authorized to delete the estimate
        if estimate.created_by != request.user and request.user.profile.user_type != 2:
            logger.warning(
                "Unauthorized deletion attempt by user: %s", request.user.username
            )
            return Response(
                {"error": "You are not authorized to delete this record."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Archive related BFM data if applicable
        if estimate.bfm:
            estimate.bfm.unarchive_record()

        # Soft delete the estimate
        estimate.delete()
        logger.info("Estimate with ID %s deleted.", id)
        return Response(
            {"message": "Estimate soft deleted"},
            status=status.HTTP_200_OK,
        )


class EstimateArchiveView(APIView):
    """
    Archives an estimate if the user is authorized.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Archive an Estimate",
        operation_description="Archives an existing estimate identified by `id` if the user is authorized. If the estimate has an associated Bid record, it will also be archived.",
        responses={
            200: openapi.Response(
                description="Estimate archived successfully.",
                examples={
                    "application/json": {"message": "Estimate archived successfully"}
                },
            ),
            403: openapi.Response(
                description="Authorization error.",
                examples={
                    "application/json": {
                        "error": "You are not authorized to archive this record."
                    }
                },
            ),
            404: openapi.Response(
                description="Estimate not found.",
                examples={"application/json": {"error": "Not found."}},
            ),
        },
    )
    def post(self, request, id):
        estimate = get_object_or_404(
            Estimate,
            id=id,
            is_deleted=False,
        )

        # Check user authorization
        if estimate.created_by != request.user and request.user.profile.user_type != 2:
            return Response(
                {"error": "You are not authorized to archive this record."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Archive associated BFM record if it exists
        if estimate.bfm:
            estimate.bfm.archive_record()

        # Archive the estimate using archive_record()
        estimate.archive_record()

        return Response(
            {"message": "Estimate archived successfully"}, status=status.HTTP_200_OK
        )


class EstimateHistoryView(APIView):
    """
    View the history of an estimate.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get the history of an estimate by its ID.",
        manual_parameters=[
            openapi.Parameter(
                "estimate_id",
                openapi.IN_PATH,
                description="The ID of the estimate",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "estimate_id": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="The ID of the estimate",
                        ),
                        "estimate_histories": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "estimate": openapi.Schema(
                                        type=openapi.TYPE_INTEGER,
                                        description="The ID of the associated estimate",
                                    ),
                                    "total": openapi.Schema(
                                        type=openapi.TYPE_NUMBER,
                                        description="Total amount of the estimate history",
                                    ),
                                    "version": openapi.Schema(
                                        type=openapi.TYPE_INTEGER,
                                        description="The version number of the estimate history",
                                    ),
                                },
                            ),
                        ),
                    },
                ),
            ),
            404: "Estimate not found",
        },
    )
    def get(self, request, id):
        """
        Get the history of an estimate by ID.
        """
        estimate = get_object_or_404(
            Estimate,
            id=id,
            is_deleted=False,
        )
        estimate_histories = EstimateHistory.objects.filter(
            estimate=estimate,
            is_deleted=False,
        )

        data = {
            "estimate_id": estimate.id,
            "estimate_histories": EstimateHistorySerializer(
                estimate_histories, many=True
            ).data,
        }

        return Response(data)


class EstimateDetailsView(APIView):
    """
    View and update details of an estimate.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        """
        Get the details of the estimate.
        """
        estimate = get_object_or_404(
            Estimate,
            id=id,
            is_deleted=False,
        )
        return Response(
            data=EstimateSerializer(estimate).data, status=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        operation_summary="Create estimate detail",
        operation_description="Create estimate detail based on the provided data.",
        request_body=EstimateDetailsSerializer,
    )
    def post(self, request, id):
        """
        create the details of an estimate.
        """
        estimate = get_object_or_404(
            Estimate,
            id=id,
            is_deleted=False,
        )
        estimate_details = get_object_or_404(
            EstimateDetails,
            estimate=estimate,
            is_deleted=False,
        )

        serializer = EstimateDetailsSerializer(
            estimate_details, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Update estimate details",
        operation_description="Update estimate details for the given estimate ID.",
        request_body=EstimateDetailsSerializer,
    )
    def put(self, request, id):
        """
        Update the details of an estimate.
        """
        estimate = get_object_or_404(
            Estimate,
            id=id,
            is_deleted=False,
        )
        estimate_details = get_object_or_404(
            EstimateDetails,
            estimate=estimate,
            is_deleted=False,
        )
        serializer = EstimateDetailsSerializer(
            estimate_details, data=request.data, partial=False
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EstimateEquipmentDeleteView(APIView):
    """
    Delete the Estimate Equipment record.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="delete_estimate_equipment",
        summary="Delete Estimate Equipment",
        description=(
            "Deletes an Estimate Equipment record by its ID. "
            "Marks the record as deleted instead of physically removing it from the database."
        ),
        parameters=[
            OpenApiParameter(
                name="estimate_equipment_id",
                description="ID of the Estimate Equipment to delete.",
                required=True,
                type=int,
            ),
        ],
        responses={
            200: "The Estimate Equipment was successfully deleted.",
            404: "The requested Estimate Equipment was not found.",
            401: "Authentication credentials were not provided or are invalid.",
        },
    )
    def delete(self, request, estimate_equipment_id):
        """
        Delete the estimate equipment by ID
        """
        estimate_equipment = get_object_or_404(
            EstimateEquipment,
            id=estimate_equipment_id,
            is_deleted=False,
        )
        estimate_equipment.delete()
        return Response(status=status.HTTP_200_OK)


class EstimateDuplicateView(APIView):

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Duplicate estimate",
        operation_description="Duplicate estimate based on the provided data.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "customer_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="ID of the new customer"
                )
            },
            required=["customer_id"],
        ),
    )
    def post(self, request, id):
        this_estimate = get_object_or_404(
            Estimate,
            id=id,
            is_deleted=False,
        )

        customer_id = request.data.get("customer_id")
        if not customer_id:
            return Response(
                {"error": "Customer ID is required for duplication."},
                status=status.HTTP_400_BAD_REQUEST,
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
        duplicated_obj.customer = get_object_or_404(
            Person,
            id=int(customer_id),
            is_deleted=False,
        )
        duplicated_obj.save()

        # Duplicate services associated with the estimate
        duplicated_obj.service.set(this_estimate.service.all())

        # Duplicate EstimateEquipment records
        all_equipments = EstimateEquipment.objects.filter(
            estimate=this_estimate,
            is_deleted=False,
        )
        for equipment in all_equipments:
            equipment.pk = None
            equipment.estimate = duplicated_obj
            equipment.save()

        # Duplicate EstimateDetails if it exists
        try:
            EstimateDetails.objects.get(estimate=duplicated_obj.pk).delete()
            estimate_detail = deepcopy(
                EstimateDetails.objects.get(estimate=this_estimate)
            )
            estimate_detail.id = None
            estimate_detail.estimate = duplicated_obj
            estimate_detail.save()
        except EstimateDetails.DoesNotExist:
            pass

        return Response(
            {"message": "Estimate duplicated successfully"}, status=status.HTTP_200_OK
        )


class EstimateEquipmentView(APIView):
    """
    Handles equipment-related operations for an estimate, including
    retrieving equipment pricing details and adding or updating equipment.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, estimate_id, service_id):
        """
        Retrieves equipment and pricing data for a specific estimate and service.

        Arguments:
            estimate_id (int): The ID of the estimate.
            service_id (int): The ID of the service.

        Returns:
            Response: The equipment details and total pricing.
        """
        estimate = get_object_or_404(
            Estimate,
            id=estimate_id,
            is_deleted=False,
        )
        interval_set = estimate.service.all()[service_id]

        try:
            # Get the equipment pricing data
            estimate_equipments_pricing = EstimateEquipment.objects.filter(
                estimate=estimate,
                flag=True,
                is_deleted=False,
            )
            estimate_money = sum(
                (
                    float(e.price_override)
                    if e.price_override
                    else float(e.equipment.price)
                )
                * float(e.quantity)
                for e in estimate_equipments_pricing
            )

            # Filter equipment based on the service interval
            equipments = Equipment.objects.filter(service=interval_set.id)
            equipment_in = [item.equipment.id for item in estimate_equipments_pricing]

            return Response(
                {
                    "estimate_id": estimate_id,
                    "estimate_money": estimate_money,
                    "interval_set": interval_set.id,
                    "service_id": service_id,
                    "equipments": [equipment.id for equipment in equipments],
                    "equipment_in": equipment_in,
                }
            )

        except DatabaseError:
            return Response(
                {"error": "An error occurred while retrieving the equipment details."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_summary="Create estimate equipment",
        operation_description="Create estimate equipment based on the provided data.",
        request_body=EstimateEquipmentSerializer(many=True),
    )
    def post(self, request, estimate_id, service_id):
        """
        Adds equipment for a specific estimate and service.

        Arguments:
            estimate_id (int): The ID of the estimate.
            service_id (int): The ID of the service.

        Returns:
            Response: Success message and updated estimate pricing.
        """
        estimate = get_object_or_404(
            Estimate,
            id=estimate_id,
            is_deleted=False,
        )
        serializer = EstimateEquipmentSerializer(
            data=request.data, many=True, context={"estimate_id": estimate_id}
        )

        if serializer.is_valid():
            for equipment_data in serializer.validated_data:
                equipment = equipment_data["equipment"]
                quantity = equipment_data["quantity"]
                price_override = equipment_data.get("price_override")

                # Check if the equipment already exists in the estimate
                existing_equipment = EstimateEquipment.objects.filter(
                    estimate=estimate_id,
                    equipment=equipment,
                    is_deleted=False,
                ).first()

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
                    )

            # Recalculate the total price
            estimate_equipments_pricing = EstimateEquipment.objects.filter(
                estimate=estimate,
                flag=True,
                is_deleted=False,
            )
            estimate_money = sum(
                (
                    float(e.price_override)
                    if e.price_override
                    else float(e.equipment.price)
                )
                * float(e.quantity)
                for e in estimate_equipments_pricing
            )

            return Response(
                {
                    "message": "Estimate equipment created successfully.",
                    "estimate_money": estimate_money,
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Update estimate equipment",
        operation_description="Updates the details of existing equipment for an estimate.",
        request_body=EstimateEquipmentSerializer(many=True),
    )
    def put(self, request, estimate_id, service_id):
        """
        Updates existing equipment details for a specific estimate and service.

        Arguments:
            estimate_id (int): The ID of the estimate.
            service_id (int): The ID of the service.

        Returns:
            Response: Success message and updated estimate pricing.
        """
        estimate = get_object_or_404(Estimate, id=estimate_id, is_deleted=False)
        serializer = EstimateEquipmentSerializer(
            data=request.data, many=True, context={"estimate_id": estimate_id}
        )

        if serializer.is_valid():
            for equipment_data in serializer.validated_data:
                equipment = equipment_data["equipment"]
                quantity = equipment_data["quantity"]
                price_override = equipment_data.get("price_override")

                # Check if the equipment exists in the estimate
                existing_equipment = EstimateEquipment.objects.filter(
                    estimate=estimate,
                    equipment=equipment,
                    is_deleted=False,
                ).first()

                if existing_equipment:
                    # Update existing equipment details
                    existing_equipment.quantity = quantity
                    existing_equipment.price_override = price_override
                    existing_equipment.save()
                else:
                    return Response(
                        {
                            "error": f"Equipment with ID {equipment.id} does not exist in this estimate."
                        },
                        status=status.HTTP_404_NOT_FOUND,
                    )

            # Recalculate the total price
            estimate_equipments_pricing = EstimateEquipment.objects.filter(
                estimate=estimate, flag=True, is_deleted=False
            )
            estimate_money = sum(
                (
                    float(e.price_override)
                    if e.price_override
                    else float(e.equipment.price)
                )
                * float(e.quantity)
                for e in estimate_equipments_pricing
            )

            return Response(
                {
                    "message": "Estimate equipment updated successfully.",
                    "estimate_money": estimate_money,
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EstimateBidListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve Available Bids for Estimates",
        description="Fetch a list of bids that are not archived and are not associated with any existing estimate.",
        parameters=[
            OpenApiParameter(
                name="bid_id",
                description="The ID of a specific bid to retrieve (optional)",
                required=False,
                type=int,
            ),
        ],
        responses={
            200: BidSerializer(many=True),
            500: dict,
        },
    )
    def get(self, request, bid_id=None):
        """
        Retrieve available bids that are not archived or associated with an estimate.

        Args:
            bid_id (int, optional): The ID of a specific bid to retrieve.

        Returns:
            - 200: Serialized data of available bids.
            - 500: Error message if an exception occurs.
        """
        try:
            # Query for available bids
            bids = (
                BidFile.objects.filter(archive=False)
                .exclude(id__in=Estimate.objects.values_list("bfm_id", flat=True))
                .order_by("-created_on")
            )

            # Filter by bid_id if provided
            if bid_id:
                bids = bids.filter(id=bid_id)

            if not bids.exists():
                return Response(
                    {"detail": "No bids available."},
                    status=status.HTTP_200_OK,
                )

            serializer = BidSerializer(bids, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {
                    "detail": "An error occurred while retrieving bids.",
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


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
            "OwnerName",
            "OwnerTitle",
            "OwnerAddressLine1",
            "OwnerAddressLine2",
            "OwnerTel",
            "OwnerFax",
            "OwnerWeb",
            "OwnerMail",
            "PDFHeaderText",
            "CompanyName",
        ]
        required_files = ["OwnerSignature", "OwnerLogo", "PDFHeaderLogo"]

        license_info = {
            info["key"]: info["value"]
            for info in LicenseInfo.objects.filter(key__in=required_keys).values(
                "key", "value"
            )
        }

        license_files = {
            file["key"]: file["value"]
            for file in LicenseFiles.objects.filter(key__in=required_files).values(
                "key", "value"
            )
        }

        return license_info, license_files

    @staticmethod
    def _estimate_total_work(estimate_id: int):
        """
        Calculate the total work based on estimate equipment.
        """
        estimate_equipments = EstimateEquipment.objects.filter(
            estimate=estimate_id,
            flag=True,
            is_deleted=False,
        )
        estimate_work = sum(
            int(each_estimate_equipment.quantity)
            * int(each_estimate_equipment.equipment.estimate_work)
            for each_estimate_equipment in estimate_equipments
        )
        return estimate_work

    @staticmethod
    def _estimate_equipments(estimate_id: int):
        estimate_equipments = EstimateEquipment.objects.filter(
            estimate=estimate_id,
            flag=True,
            is_deleted=False,
        )
        return estimate_equipments

    @staticmethod
    def _calculate_estimate_totals(estimate, estimate_sub):
        """
        Calculate control system, hours, predemo, and final estimate total.
        """
        control_system_calculated = round(
            (estimate_sub * (1 + estimate.estimatedetails.control_system / 100))
            - estimate_sub,
            2,
        )
        hours_calculated = round(
            (estimate_sub * (1 + estimate.estimatedetails.hours / 100)) - estimate_sub,
            2,
        )
        predemo_calculated = estimate.estimatedetails.pre_demo * 1200

        estimate_total = round(
            estimate_sub
            + control_system_calculated
            + hours_calculated
            + predemo_calculated
            + float(estimate.estimatedetails.adjustment)
            + float(estimate.estimatedetails.customer_adjustment),
            2,
        )
        return (
            control_system_calculated,
            hours_calculated,
            predemo_calculated,
            estimate_total,
        )

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
        (
            control_system_calculated,
            hours_calculated,
            predemo_calculated,
            estimate_total,
        ) = estimate_totals
        estimate_sub = sum(
            float(eq.price_override if eq.price_override else eq.equipment.price)
            * float(eq.quantity)
            for eq in EstimateEquipment.objects.filter(
                estimate=estimate,
                flag=True,
                is_deleted=False,
            )
        )
        estimate_file_name = pdf_filename_generator(estimate.id, "E")

        return {
            "file_name": estimate_file_name,
            "estimate": estimate,
            "other_than_dalt_services": estimate.service.exclude(name__iexact="DALT"),
            "has_dalt": estimate.service.filter(name__iexact="DALT").exists(),
            "estimate_equipments_pricing": estimate_equipments(estimate_id=estimate.id),
            "estimate_work_in_hours": int(estimate_work / 60),
            "estimate_work_in_minutes": int(estimate_work % 60),
            **license_info,
            **license_files,
            "pdf_header_logo": license_files.get("PDFHeaderLogo"),
            "company_name": license_info.get("CompanyName"),
            "estimate_id": estimate.id,
            "estimate_sub": estimate_sub,
            "estimate_total": estimate_total,
            "control_system_calculated": control_system_calculated,
            "hours_calculated": hours_calculated,
            "predemo_calculated": predemo_calculated,
            "datetime": datetime.datetime.now(),
            "user_name": f"{request.user.first_name} {request.user.last_name or 'TAB Technologies, INC. Operator'}",
            "user_title": request.user.profile.title or "Estimator",
            "user_signature": request.user.profile.e_sign,
            "user_cell": request.user.profile.cell or "",
        }

    def get(self, request, estimate_id):
        """
        Generate and return the estimate bid with relevant data.
        """
        try:
            license_info, license_files = self._get_license_info()
            estimate = get_object_or_404(
                Estimate,
                id=estimate_id,
                is_deleted=False,
            )
            estimate_sub = sum(
                float(eq.price_override if eq.price_override else eq.equipment.price)
                * float(eq.quantity)
                for eq in EstimateEquipment.objects.filter(
                    estimate=estimate,
                    flag=True,
                    is_deleted=False,
                )
            )
            estimate_work = self._estimate_total_work(estimate_id=estimate_id)
            estimate_totals = self._calculate_estimate_totals(estimate, estimate_sub)
            estimate_equipments = self._estimate_equipments(estimate_id=estimate_id)

            if settings.TAB_SYSTEM:
                invoice_error = InvoiceService._generate_invoice_history(estimate)
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
                response_data["invoice_error"] = invoice_error

            return Response(response_data, status=status.HTTP_200_OK)

        except Estimate.DoesNotExist:
            return Response(
                {"error": "Estimate not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
