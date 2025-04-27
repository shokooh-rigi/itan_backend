import datetime
import os
from datetime import datetime
from rest_framework.parsers import MultiPartParser
from drf_spectacular.utils import extend_schema, OpenApiParameter

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    CreateAPIView,
    ListAPIView,
    DestroyAPIView,
    RetrieveAPIView,
)
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import RetrieveDestroyAPIView
from django.db import transaction

from mysite.order.models import (
    Order,
    TechLabel,
    ChangeOrder,
    ControlSystem,
    ControlSystemManufacturer,
    TechLabelExtraFields,
)
from mysite.order.views import control_system
from mysite.proposal.models import Proposal
from .serializers import (
    OrderSerializer,
    ChangeOrderSerializer,
    OrderControlSystemSerializer,
    ControlSystemSerializer,
    ControlSystemManufacturerSerializer,
    GeneralNotesSerializer,
    EquipmentSubmittalSerializer,
    ColorDrawingUploadSerializer,
)
from .serializers import TechLabelSerializer
from .services.change_order_service import (
    ChangeOrderServiceLayer,
    DeleteChangeOrderService,
)
from .services.order_equipment_submittal_service import OrderEquipmentSubmittalService
from .services.order_full_update_service import OrderFullUpdateService
from .services.order_service import OrderService, OrderEditService
from .services.order_site_pictures_service import OrderSitePicturesService
from ..proposal.serializers import ProposalSerializer


class OrderListAPIView(APIView):
    """
    API view to handle listing and filtering of orders.

    Query Parameters:
        - project_name (str): Search orders by project name or related fields.
        - type (str): Type of orders to filter (all, inprogress, invoiced, notinvoiced, reported).
        - ordering (str): Field to order the results by (default: '-created_on').
        - paginate_by (int): Number of orders per page (default: 20).
        - page (int): The page number to return (default: 1).

    Returns:
        - Paginated list of orders based on filters and ordering.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve a paginated list of orders with optional filters and ordering.",
        manual_parameters=[
            openapi.Parameter(
                "project_name",
                openapi.IN_QUERY,
                description="Search orders by project name or related fields.",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "type",
                openapi.IN_QUERY,
                description="Type of orders to filter (all, inprogress, invoiced, notinvoiced, reported).",
                type=openapi.TYPE_STRING,
                enum=["all", "inprogress", "invoiced", "notinvoiced", "reported"],
                default="all",
            ),
            openapi.Parameter(
                "ordering",
                openapi.IN_QUERY,
                description="Field to order the results by (default: '-created_on').",
                type=openapi.TYPE_STRING,
                default="-created_on",
            ),
            openapi.Parameter(
                "page_size",
                openapi.IN_QUERY,
                description="Number of orders per page (default: 20).",
                type=openapi.TYPE_INTEGER,
                default=settings.PAGE_SIZE,
            ),
            openapi.Parameter(
                "page",
                openapi.IN_QUERY,
                description="The page number to return (default: 1).",
                type=openapi.TYPE_INTEGER,
                default=1,
            ),
        ],
        responses={
            200: openapi.Response(
                "A paginated list of orders",
                OrderSerializer(many=True),
            ),
            400: "Invalid date format or other error",
        },
    )
    def get(self, request):
        project_name = request.query_params.get("project_name", "")
        order_type = request.query_params.get("type", "all")
        ordering = request.query_params.get("ordering", "-created_on")
        page_size = int(request.query_params.get("page_size", settings.PAGE_SIZE))
        orders_queryset = OrderService.get_filtered_orders(
            project_name=project_name,
            order_type=order_type,
            ordering=ordering,
        )
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        paginated_orders = paginator.paginate_queryset(orders_queryset, request)
        serializer = OrderSerializer(paginated_orders, many=True)
        return paginator.get_paginated_response(serializer.data)


class OrderAddAPIView(APIView):
    """
    API view for adding a new order.

    Methods:
        - POST: Creates a new order.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Create a new order by providing the required data.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "architect_name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Architect's name"
                ),
                "po_number": openapi.Schema(
                    type=openapi.TYPE_STRING, description="PO order number"
                ),
                "date_po_received": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_DATE,
                    description="Date PO was received",
                ),
                "final_offset": openapi.Schema(
                    type=openapi.TYPE_NUMBER, description="Final offset value"
                ),
                "note": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Additional notes"
                ),
                "estimated_date_of_project": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_DATE,
                    description="Estimated project date",
                ),
                "proposal_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="ID of the associated proposal",
                ),
            },
            required=["po_number", "proposal_id"],
        ),
        responses={
            201: openapi.Response(
                description="Order created successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"message": openapi.Schema(type=openapi.TYPE_STRING)},
                ),
            ),
            400: openapi.Response(
                description="Validation errors",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    additional_properties=openapi.Schema(type=openapi.TYPE_STRING),
                ),
            ),
        },
    )
    def post(self, request):
        """
        Handle the creation of a new order.
        """
        serializer = OrderSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Order created successfully!"},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderProposalListView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Retrieve non-archived and unassociated proposals",
        operation_description="Endpoint retrieves proposals that are not archived and not associated with any order.",
        responses={
            200: openapi.Response(
                description="List of available proposals",
                schema=ProposalSerializer(many=True),
            ),
            401: "Unauthorized - User must be authenticated",
        },
    )
    def get(self, request, proposal_id=None):
        """
        Retrieves available proposals that are not archived or associated with an order.
        """
        try:

            proposals = Proposal.objects.filter(archive=False, is_deleted=False)

            if not proposals.exists():
                return Response(
                    {"detail": "No proposals available."},
                    status=status.HTTP_200_OK,
                )

            if proposal_id:
                proposals = proposals.filter(id=proposal_id)

            proposals = proposals.exclude(
                id__in=Order.objects.values_list("proposal_id", flat=True)
            )

            serializer = ProposalSerializer(proposals, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {
                    "detail": "An error occurred while retrieving proposals.",
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class OrderEditAPIView(APIView):
    """
    API view for editing an existing order.

    Methods:
        - GET: Retrieve order details, proposals, and change orders.
        - PUT: Update the order based on user input.

    Path Parameters:
        - order_id (int): The ID of the order to edit.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve details of a specific order.",
        manual_parameters=[
            openapi.Parameter(
                "order_id",
                openapi.IN_PATH,
                description="The ID of the order to retrieve.",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        responses={
            200: openapi.Response(
                description="Order details.",
                schema=OrderSerializer(),
            )
        },
    )
    def get(self, request, order_id):
        """
        Retrieve order details.
        """
        this_order = get_object_or_404(
            Order,
            id=order_id,
            is_deleted=False,
            archive=False,
        )

        order_data = OrderSerializer(this_order).data

        return Response(order_data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Update an existing order by providing the updated fields.",
        request_body=OrderSerializer,
        responses={
            200: openapi.Response(
                description="Order updated successfully.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            400: openapi.Response(
                description="Validation errors.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    additional_properties=openapi.Schema(type=openapi.TYPE_STRING),
                ),
            ),
        },
    )
    def put(self, request, order_id):
        """
        Update an existing order.
        """
        this_order = OrderEditService.get_order(order_id)
        serializer = OrderSerializer(this_order, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Order updated successfully!"}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderDeleteAPIView(APIView):
    """
    API view for deleting an order.

    Methods:
        - DELETE: Deletes the specified order.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Delete a specified order by its ID.",
        manual_parameters=[
            openapi.Parameter(
                "order_id",
                openapi.IN_PATH,
                description="The ID of the order to delete.",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        responses={
            200: openapi.Response(
                description="Order deleted successfully.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            403: openapi.Response(
                description="User is not authorized to delete the order.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
        },
    )
    def delete(self, request, order_id):
        this_order = OrderService.get_order(order_id)
        try:
            # Check user permissions
            OrderService.validate_user_permission(this_order, request.user)

            OrderService.delete_order(this_order)
            return Response(
                {"message": "Order deleted successfully!"}, status=status.HTTP_200_OK
            )

        except PermissionDenied as e:
            # Return error if the user is unauthorized
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)


class OrderArchiveAPIView(APIView):
    """
    API view for archiving an order.

    Methods:
        - POST: Archives the specified order.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Archive a specified order by its ID.",
        manual_parameters=[
            openapi.Parameter(
                "order_id",
                openapi.IN_PATH,
                description="The ID of the order to archive.",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        responses={
            200: openapi.Response(
                description="Order archived successfully.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            403: openapi.Response(
                description="User is not authorized to archive the order.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
        },
    )
    def post(self, request, order_id):
        this_order = OrderService.get_order(order_id)
        if order.proposal.estimate.created_by != user:
            return Response(
                {"message": "You are not authorized to modify this record."},
                status=status.HTTP_403_FORBIDDEN,
            )

        OrderService.archive_order(this_order)
        return Response(
            {"message": "Order archived successfully!"}, status=status.HTTP_200_OK
        )


class ChangeOrderApiView(APIView):
    """
    API endpoint for creating and deleting a change order.

    This view handles:
    - Validating incoming data using a serializer.
    - Delegating business logic to the ChangeOrderServiceLayer.

    Methods:
        - post: Creates a new change order along with associated services and generates a PDF.
        - delete: Deletes a specific change order associated with an order.

    Parameters:
        - order_id (int): The ID of the order to associate with the change order.
        - change_order_id (int): The ID of the change order to delete.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Create a change-order instance.",
        request_body=ChangeOrderSerializer,
        responses={
            201: openapi.Response(
                "Successfully created the change-order instance", ChangeOrderSerializer
            ),
            400: "Validation error in input data",
            404: "Order not found",
        },
    )
    def post(self, request, order_id):
        """
        Handles the creation of a change order.

        Args:
            request: The HTTP request containing the data for the change order.
            order_id (int): The ID of the order to associate with the change order.

        Returns:
            Response: Success or error response based on the validation and execution.
        """
        # Retrieve the order from the URL parameter (order_id)
        this_order = get_object_or_404(
            Order,
            id=order_id,
            is_deleted=False,
        )

        # Don't include order_id in the request body; it should be in the URL
        request_data = request.data.copy()
        request_data["order"] = this_order.id

        # Initialize the serializer with the request data
        serializer = ChangeOrderSerializer(data=request_data)
        if serializer.is_valid():
            # Save the change order and return a success response
            change_order = serializer.save(order=this_order)
            return Response(
                {
                    "status": "Change order created successfully",
                    "change_order_id": change_order.id,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Delete a specific change-order instance.",
        manual_parameters=[
            openapi.Parameter(
                "order_id",
                openapi.IN_PATH,
                description="The ID of the order associated with the change order.",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
            openapi.Parameter(
                "change_order_id",
                openapi.IN_PATH,
                description="The ID of the change order to delete.",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        responses={
            200: openapi.Response(
                description="Change order deleted successfully.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "status": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            404: openapi.Response(
                description="Order or change order not found.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
        },
    )
    def delete(self, request, order_id, change_order_id):
        """
        Handles the deletion of a change order.

        Args:
            request: The HTTP request.
            order_id (int): The ID of the order associated with the change order.
            change_order_id (int): The ID of the change order to delete.

        Returns:
            Response: Success or error response based on the validation and execution.
        """
        # Retrieve the order and change order
        this_order = get_object_or_404(
            Order,
            id=order_id,
            is_deleted=False,
        )
        change_order = get_object_or_404(
            ChangeOrder,
            id=change_order_id,
            order=this_order,
            is_deleted=False,
        )

        # Perform the deletion
        change_order.delete()
        return Response(
            {"status": "Change order deleted successfully."},
            status=status.HTTP_200_OK,
        )


class ChangeOrderApiView(APIView):
    """
    API endpoint for creating and deleting a change order.

    This view handles:
    - Validating incoming data using a serializer.
    - Delegating business logic to the ChangeOrderServiceLayer.

    Methods:
        - post: Creates a new change order along with associated services and generates a PDF.
        - delete: Deletes a specific change order associated with an order.

    Parameters:
        - order_id (int): The ID of the order to associate with the change order.
        - change_order_id (int): The ID of the change order to delete.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Create a change-order instance.",
        request_body=ChangeOrderSerializer,
        responses={
            201: openapi.Response(
                "Successfully created the change-order instance", ChangeOrderSerializer
            ),
            400: "Validation error in input data",
            404: "Order not found",
        },
    )
    def post(self, request, order_id):
        """
        Handles the creation of a change order.

        Args:
            request: The HTTP request containing the data for the change order.
            order_id (int): The ID of the order to associate with the change order.

        Returns:
            Response: Success or error response based on the validation and execution.
        """
        # Retrieve the order from the URL parameter (order_id)
        this_order = get_object_or_404(
            Order,
            id=order_id,
            is_deleted=False,
        )

        # Don't include order_id in the request body; it should be in the URL
        request_data = request.data.copy()
        request_data["order"] = this_order.id

        # Initialize the serializer with the request data
        serializer = ChangeOrderSerializer(data=request_data)
        if serializer.is_valid():
            # Save the change order and return a success response
            change_order = serializer.save(order=this_order)
            return Response(
                {
                    "status": "Change order created successfully",
                    "change_order_id": change_order.id,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangeOrderDeleteAPIView(APIView):
    """
    API View to delete a Change Order.
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, change_order_id):
        change_order = get_object_or_404(
            ChangeOrder,
            id=change_order_id,
            is_deleted=False,
        )

        # Service layer handling change order deletion
        service = DeleteChangeOrderService(change_order.order, request.user)
        success = service.delete_change_order(change_order)

        if success:
            return Response(
                {"detail": "Change order deleted successfully."},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"detail": "Change order not found."}, status=status.HTTP_404_NOT_FOUND
            )


class ChangeOrderList(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve all change orders for a specific order.",
        manual_parameters=[
            openapi.Parameter(
                "order_id",
                openapi.IN_PATH,
                description="The ID of the order to retrieve change orders for.",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        responses={
            200: openapi.Response(
                description="List of change orders for the specified order.",
                schema=ChangeOrderSerializer(many=True),
            ),
            404: openapi.Response(
                description="Order not found.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
        },
    )
    def get(self, request, order_id):
        """
        Get all change orders for a specific order.
        """
        order = get_object_or_404(
            Order,
            id=order_id,
            is_deleted=False,
        )
        change_orders = ChangeOrder.objects.filter(order=order)
        serializer = ChangeOrderSerializer(change_orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChangeOrderApproveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, change_order_id):
        try:
            # Call the service to approve the change order and generate the invoice PDF
            change_order = ChangeOrderServiceLayer.approve_change_order(
                change_order_id=change_order_id,
            )
            return Response(
                {
                    "message": f"Change order approved and invoice generated successfully.",
                    "change_order": ChangeOrderSerializer(change_order).data,
                },
                status=status.HTTP_200_OK,
            )
        except ChangeOrder.DoesNotExist:
            return Response(
                {"message": "Change order not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ChangeOrderUnapproveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, change_order_id):
        try:
            # Call the service to approve the change order and generate the invoice PDF
            change_order = ChangeOrderServiceLayer.unapprove_change_order(
                change_order_id=change_order_id,
            )
            return Response(
                {
                    "message": f"Change order unapproved and invoice generated successfully.",
                    "change_order": ChangeOrderSerializer(change_order).data,
                },
                status=status.HTTP_200_OK,
            )
        except ChangeOrder.DoesNotExist:
            return Response(
                {"message": "Change order not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TechLabelDeleteView(DestroyAPIView):
    queryset = TechLabel.objects.all()
    serializer_class = TechLabelSerializer
    permission_classes = [IsAuthenticated]

    def perform_destroy(self, instance):
        # Optional: Delete related extra fields if needed
        instance.extra_fields.all().delete()
        super().perform_destroy(instance)


class TechLabelByOrderView(RetrieveAPIView):

    serializer_class = TechLabelSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id, *args, **kwargs):
        try:
            tech_label = TechLabel.objects.get(order_id=order_id)
            serializer = self.get_serializer(tech_label)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except TechLabel.DoesNotExist:
            return Response(
                {"detail": "TechLabel not found for this order_id"},
                status=status.HTTP_404_NOT_FOUND,
            )


class TechLabelListView(ListAPIView):
    """
    API to list TechLabel instances.
    """

    queryset = TechLabel.objects.all()
    serializer_class = TechLabelSerializer
    permission_classes = [IsAuthenticated]


class TechLabelCreateUpdateView(CreateAPIView):
    """
    API to create or update TechLabel based on order_id.
    If a TechLabel already exists for the given order_id, it will be updated.
    """

    serializer_class = TechLabelSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """
        Use the TechLabelSerializer, which handles both create and update.
        """
        return TechLabelSerializer


class ControlSystemAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        """
        Retrieve the current control system for the given order.
        """
        order = get_object_or_404(
            Order,
            id=order_id,
            is_deleted=False,
        )

        if not order.control_system:
            return Response({}, status=status.HTTP_200_OK)

        serializer = OrderControlSystemSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, order_id):
        """
        Update the control system for the given order.
        """
        order = get_object_or_404(
            Order,
            id=order_id,
            is_deleted=False,
        )

        if not order.control_system:
            return Response({}, status=status.HTTP_200_OK)

        serializer = OrderControlSystemSerializer(
            order,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Control system updated successfully!"},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ControlSystemListCreateView(ListCreateAPIView):
    """
    API for listing and creating Control Systems
    """

    queryset = ControlSystem.objects.all()
    serializer_class = ControlSystemSerializer

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["manufacturer_id"],
            properties={
                "version_number": openapi.Schema(type=openapi.TYPE_STRING),
                "documentation": openapi.Schema(type=openapi.TYPE_FILE),
                "os": openapi.Schema(type=openapi.TYPE_STRING),
                "release_date": openapi.Schema(type=openapi.TYPE_STRING, format="date"),
                "control_file_url": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format="url",
                ),
                "manufacturer_id": openapi.Schema(type=openapi.TYPE_INTEGER),
            },
        ),
        responses={
            201: ControlSystemSerializer(),
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)



class ControlSystemDeleteRetriveView(RetrieveDestroyAPIView):
    """
    API for retrieving and deleting a specific Control System.
    """

    queryset = ControlSystem.objects.all()
    serializer_class = ControlSystemSerializer

    @swagger_auto_schema(
        operation_description="Retrieve a specific Control System by its ID.",
        responses={
            200: ControlSystemSerializer,
            404: openapi.Response(description="Control System not found."),
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete a specific Control System by its ID.",
        responses={
            204: openapi.Response(description="Control System deleted successfully."),
            404: openapi.Response(description="Control System not found."),
        },
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class ControlSystemUpdateAPIView(APIView):
    """
    API for updating a specific Control System.
    """

    @swagger_auto_schema(
        operation_description="Update a specific Control System by its ID.",
        request_body=ControlSystemSerializer,
        responses={
            200: ControlSystemSerializer,
            400: openapi.Response(description="Validation error."),
            404: openapi.Response(description="Control System not found."),
        },
    )
    def put(self, request, control_system_id):
        """
        Update a control system with the provided data.
        """
        control_system = get_object_or_404(ControlSystem, id=control_system_id)
        serializer = ControlSystemSerializer(control_system, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ControlSystemManufacturerListCreateView(ListCreateAPIView):
    """
    API for listing and creating Control System Manufacturers.
    """

    queryset = ControlSystemManufacturer.objects.all()
    serializer_class = ControlSystemManufacturerSerializer


class ControlSystemManufacturerDetailView(RetrieveUpdateDestroyAPIView):
    """
    API for retrieving, updating, and deleting a specific Control System Manufacturer.
    """

    queryset = ControlSystemManufacturer.objects.all()
    serializer_class = ControlSystemManufacturerSerializer


class OrderEquipmentSubmittalView(APIView):
    """
    API for managing order equipment submittal.
    - Clear submitted equipment data.
    - Upload files and update the order with submitted equipment.
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]  # Supports file uploads

    @swagger_auto_schema(
        operation_summary="Manage equipment submittal for an order",
        operation_description="""
            - **Clear equipment submittal**: If `equipment_submittal_clear` is `true`, it removes existing submittals.
            - **Upload files**: If `equipment_submittal` contains files, they will be uploaded.
        """,
        manual_parameters=[
            openapi.Parameter(
                "order_id",
                openapi.IN_PATH,
                description="The unique identifier for the order",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
            openapi.Parameter(
                "equipment_submittal_clear",
                openapi.IN_QUERY,
                description="Set to true to clear all existing submittals",
                type=openapi.TYPE_BOOLEAN,
                required=False,
            ),
            openapi.Parameter(
                "equipment_submittal",
                openapi.IN_FORM,
                description="Equipment submittal files",
                type=openapi.TYPE_FILE,
                required=False,
            ),
        ],
        responses={
            200: openapi.Response("Equipment submittal updated successfully."),
            400: openapi.Response("Invalid input"),
            500: openapi.Response("Server error"),
        },
    )
    def post(self, request, order_id):
        """
        Handle POST request to manage equipment submittal for an order.
        - Clear equipment submittal
        - Upload files and update order with equipment submittal.
        """
        try:
            # Fetch the order instance
            order = get_object_or_404(
                Order,
                id=order_id,
                is_deleted=False,
            )

            # Validate request data using serializer
            serializer = EquipmentSubmittalSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data

            # Handle clearing the equipment submittal
            if data.get("equipment_submittal_clear"):
                OrderEquipmentSubmittalService.clear_equipment_submittal(order_id)
                return Response(
                    {"detail": "Equipment submittal cleared."},
                    status=status.HTTP_200_OK,
                )

            # Handle files upload and processing
            files = request.FILES.getlist("equipment_submittal")
            if not files:
                return Response(
                    {"detail": "No files provided."}, status=status.HTTP_400_BAD_REQUEST
                )

            OrderEquipmentSubmittalService.update_order_with_equipment_submittal(
                order, files
            )

            return Response(
                {"detail": "Equipment submittal updated successfully."},
                status=status.HTTP_200_OK,
            )

        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {"detail": f"An error occurred. {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class OrderColorDrawingView(APIView):
    """
    API View to handle color drawings for an order.
    - `GET`: Retrieve color drawings for an order.
    - `POST`: Upload color drawings for an order.
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]  # Supports file uploads
    serializer_class = ColorDrawingUploadSerializer

    @swagger_auto_schema(
        operation_summary="Retrieve color drawings for an order",
        operation_description="Returns the color drawings associated with the order.",
        manual_parameters=[
            openapi.Parameter(
                "order_id",
                openapi.IN_PATH,
                description="The unique identifier for the order",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        responses={
            200: openapi.Response(
                "Color drawings retrieved successfully.", ColorDrawingUploadSerializer
            )
        },
    )

    def get(self, request, order_id):
        order = get_object_or_404(
            Order,
            id=order_id,
            is_deleted=False
        )
        serializer = ColorDrawingUploadSerializer(order)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Upload color drawings for an order",
        operation_description="""
            - Accepts multiple files as color drawings.
            - Validates and processes uploaded files.
            - Creates a ZIP archive for the uploaded files.
        """,
        manual_parameters=[
            openapi.Parameter(
                "order_id",
                openapi.IN_PATH,
                description="The unique identifier for the order",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
            openapi.Parameter(
                "colored_drawing_finalize",
                openapi.IN_QUERY,
                description="Set to true to finalize the colored drawing",
                type=openapi.TYPE_BOOLEAN,
            ),
            openapi.Parameter(
                "colored_drawing",
                openapi.IN_FORM,
                description="Field drawing files to be uploaded",
                type=openapi.TYPE_FILE,
            ),
            openapi.Parameter(
                "report_colored_drawing",
                openapi.IN_FORM,
                description="Field drawing files to be uploaded",
                type=openapi.TYPE_FILE,
            ),
        ],
        responses={
            200: openapi.Response("Field drawing updated successfully."),
            400: openapi.Response("Invalid input or no files provided."),
            500: openapi.Response("Server error"),
        },
    )
    def put(self, request, order_id):
        try:
            order = get_object_or_404(
                Order,
                id=order_id,
                is_deleted=False
            )
            serializer = ColorDrawingUploadSerializer(data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)

            colored_drawing = request.FILES.get("colored_drawing")
            report_colored_drawing = request.FILES.get("report_colored_drawing")
            finalize = serializer.validated_data.get("colored_drawing_finalize", False)
            if finalize:
                order.colored_drawing_finalize = True
                order.save()

            uploaded_files = []

            if colored_drawing:
                if order.colored_drawing:
                    order.colored_drawing.delete(save=False)
                order.colored_drawing.save(colored_drawing.name, colored_drawing)
                uploaded_files.append(colored_drawing)

            if report_colored_drawing:
                if order.report_colored_drawing:
                    order.report_colored_drawing.delete(save=False)
                order.report_colored_drawing.save(
                    report_colored_drawing.name, report_colored_drawing
                )
                uploaded_files.append(report_colored_drawing)

            return Response(
                {"detail": "Color drawing updated successfully."},
                status=status.HTTP_200_OK,
            )

        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {"detail": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class OrderGeneralNotesView(APIView):
    """
    API View to handle the general notes and comments for an order.

    - `GET`: Retrieve the general notes and comments.
    - `POST`: Save the general notes and comments.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Retrieve general notes for an order",
        operation_description="Returns the general notes and comments associated with the order.",
        manual_parameters=[
            openapi.Parameter(
                "order_id",
                openapi.IN_PATH,
                description="The unique identifier for the order",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        responses={
            200: openapi.Response(
                "General notes retrieved successfully.", GeneralNotesSerializer
            )
        },
    )
    def get(self, request, order_id):
        """Retrieve the general notes and comments for an order."""
        order = get_object_or_404(Order, id=order_id, is_deleted=False)
        serializer = GeneralNotesSerializer(order)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Save general notes for an order",
        operation_description="Saves the general notes and comments for the order.",
        request_body=GeneralNotesSerializer,
        responses={
            200: openapi.Response("General notes updated successfully."),
            400: openapi.Response("Invalid input"),
        },
    )
    def post(self, request, order_id):
        """Save the general notes and comments for an order."""
        order = get_object_or_404(Order, id=order_id, is_deleted=False)

        serializer = GeneralNotesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if "general_notes_and_comments" in serializer.validated_data:
            order.general_notes_and_comments = serializer.validated_data[
                "general_notes_and_comments"
            ]
        if "general_notes_and_comments_finalize" in serializer.validated_data:
            order.general_notes_and_comments_finalize = serializer.validated_data[
                "general_notes_and_comments_finalize"
            ]
        order.save()

        return Response(
            {"detail": "General notes updated successfully."},
            status=status.HTTP_200_OK,
        )


class OrderSitePicturesView(APIView):
    """
    API View to handle uploading and saving site pictures for an order.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Upload site pictures for an order",
        operation_description="Handles the upload of site pictures for a specific order. The uploaded files are processed and saved as a ZIP archive.",
        manual_parameters=[
            openapi.Parameter(
                name="order_id",
                in_=openapi.IN_PATH,
                description="The ID of the order to upload site pictures for.",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "site_pictures": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_FILE),
                    description="List of site pictures to upload.",
                )
            },
            required=["site_pictures"],
        ),
        responses={
            200: openapi.Response(
                description="Site pictures uploaded successfully.",
                examples={"application/json": {"detail": "Site pictures uploaded and saved as <zip_file_name>."}},
            ),
            400: openapi.Response(description="Validation error."),
            500: openapi.Response(description="Server error."),
        },
    )
    def post(self, request, order_id):
        """
        Handle POST request to save site pictures
        """
        order = get_object_or_404(
            Order,
            id=order_id,
            is_deleted=False,
        )

        # Process the form data and files using the service layer
        try:
            service = OrderSitePicturesService(
                order_id, request.FILES.getlist("site_pictures")
            )
            zip_file_name = service.process_upload()
            return Response(
                {"detail": f"Site pictures uploaded and saved as {zip_file_name}."},
                status=status.HTTP_200_OK,
            )

        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {"error": "An error occurred during the upload process."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_summary="Retrieve site pictures for an order",
        operation_description="Fetches the URL of the site pictures for a specific order, if available.",
        manual_parameters=[
            openapi.Parameter(
                name="order_id",
                in_=openapi.IN_PATH,
                description="The ID of the order to retrieve site pictures for.",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        responses={
            200: openapi.Response(
                description="Site pictures retrieved successfully.",
                examples={"application/json": {"site_pictures": "<site_pictures_url>"}},
            ),
            404: openapi.Response(description="No site pictures available for this order."),
        },
    )
    def get(self, request, order_id):
        """
        Handle GET request to retrieve the site pictures for a specific order.
        """
        order = get_object_or_404(
            Order,
            id=order_id,
            is_deleted=False,
        )

        if order.site_pictures:
            return Response(
                {"site_pictures": order.site_pictures.url}, status=status.HTTP_200_OK
            )

        return Response(
            {"message": "No site pictures available for this order."},
            status=status.HTTP_404_NOT_FOUND,
        )

class OrderFullUpdateAPIView(APIView):
    """
    API endpoint for retrieving all necessary data related to an order
    to facilitate its full update process. This includes details such as:
    - Equipment related to the order
    - Test sheets associated with the order
    - Estimates and pricing
    - Manufacturers and other relevant data

    This endpoint is used to prepare the data required for updating an order,
    ensuring that all related information is available for the user to make
    necessary changes.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, order_id, *args, **kwargs):
        """
        Handles the GET request to retrieve comprehensive data for updating
        an order. The data includes the order's equipment, test sheet details,
        manufacturers, and other relevant information.

        Args:
            request: The HTTP request object.
            order_id: The unique identifier of the order to be updated.

        Returns:
            Response: A JSON response containing all necessary data for
            updating the order or an error message if the order is not found.

        Raises:
            Order.DoesNotExist: If the order with the given order_id is not found.
            Exception: For any other errors during data retrieval.
        """
        try:
            # Fetch the order instance by its ID
            order = Order.objects.get(id=order_id)

            # Initialize the service class with the order instance
            order_full_update_service = OrderFullUpdateService(order)

            # Get the order details using the correct method
            order_data = order_full_update_service.get_order_details()

            return Response(order_data, status=status.HTTP_200_OK)

        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
