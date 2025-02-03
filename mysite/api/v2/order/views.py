import datetime
import os
from datetime import datetime

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from mysite.order.models import Order, TechLabel, ChangeOrder, ControlSystem
from mysite.proposal.models import Proposal
from .serializers import OrderSerializer, ChangeOrderSerializer, OrderControlSystemSerializer, ControlSystemSerializer
from .serializers import TechLabelSerializer
from .services.change_order_service import ChangeOrderServiceLayer, DeleteChangeOrderService
from .services.order_equipment_submittal_service import OrderEquipmentSubmittalService
from .services.order_field_drawing_service import OrderFieldDrawingService
from .services.order_full_update_service import OrderFullUpdateService
from .services.order_service import OrderService, OrderEditService
from .services.order_site_pictures_service import OrderSitePicturesService
from .services.tech_label_service import TechLabelServiceLayer
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
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                "type",
                openapi.IN_QUERY,
                description="Type of orders to filter (all, inprogress, invoiced, notinvoiced, reported).",
                type=openapi.TYPE_STRING,
                enum=["all", "inprogress", "invoiced", "notinvoiced", "reported"],
                default="all"
            ),
            openapi.Parameter(
                "ordering",
                openapi.IN_QUERY,
                description="Field to order the results by (default: '-created_on').",
                type=openapi.TYPE_STRING,
                default="-created_on"
            ),
            openapi.Parameter(
                "paginate_by",
                openapi.IN_QUERY,
                description="Number of orders per page (default: 20).",
                type=openapi.TYPE_INTEGER,
                default=20
            ),
            openapi.Parameter(
                "page",
                openapi.IN_QUERY,
                description="The page number to return (default: 1).",
                type=openapi.TYPE_INTEGER,
                default=1
            )
        ],
        responses={
            200: openapi.Response(
                description="Paginated list of orders",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "orders": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                    "project_number": openapi.Schema(type=openapi.TYPE_STRING),
                                    "po_number": openapi.Schema(type=openapi.TYPE_STRING),
                                    "date_po_received": openapi.Schema(type=openapi.FORMAT_DATE),
                                    "estimated_date_of_project": openapi.Schema(type=openapi.FORMAT_DATE),
                                    "completion_percentage": openapi.Schema(type=openapi.TYPE_INTEGER),
                                    "fully_settled": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    "archive": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    "state": openapi.Schema(type=openapi.TYPE_STRING),
                                    "start_date": openapi.Schema(type=openapi.FORMAT_DATE),
                                    "end_date": openapi.Schema(type=openapi.FORMAT_DATE),
                                    "created_on": openapi.Schema(type=openapi.FORMAT_DATETIME)
                                }
                            )
                        ),
                        "WEB_URL": openapi.Schema(type=openapi.TYPE_STRING),
                        "MEDIA_URL": openapi.Schema(type=openapi.TYPE_STRING),
                        "now": openapi.Schema(type=openapi.FORMAT_DATETIME)
                    }
                )
            ),
            401: "Unauthorized",
            400: "Bad Request"
        }
    )
    def get(self, request):
        project_name = request.query_params.get("project_name", "")
        order_type = request.query_params.get("type", "all")
        ordering = request.query_params.get("ordering", "-created_on")
        paginate_by = int(request.query_params.get("paginate_by", 20))

        # Get filtered and ordered orders using the service layer
        orders_queryset = OrderService.get_filtered_orders(project_name, order_type, ordering)

        # Paginate the results
        paginator = PageNumberPagination()
        paginator.page_size = paginate_by
        paginated_orders = paginator.paginate_queryset(orders_queryset, request)

        # Serialize the data
        serializer = OrderSerializer(paginated_orders, many=True)

        # Add additional context parameters
        context = {
            "WEB_URL": settings.WEB_URL,
            "MEDIA_URL": settings.MEDIA_URL,
            "now": datetime.now()
        }

        # Return the paginated response with serialized data and additional context
        return paginator.get_paginated_response({
            "orders": serializer.data,
            **context
        })


class OrderAddAPIView(APIView):
    """
    API view for adding a new order.

    Methods:
        - POST: Creates a new order.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Create a new order by providing the required data.",
        request_body=OrderSerializer,
        responses={
            201: openapi.Response(
                description="Order created successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: openapi.Response(
                description="Validation errors",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    additional_properties=openapi.Schema(type=openapi.TYPE_STRING)
                )
            )
        }
    )
    def post(self, request):
        """
        Handle the creation of a new order.
        """
        serializer = OrderSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Order created successfully!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderProposalListView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Retrieve non-archived and unassociated proposals",
        operation_description=(
            "This endpoint retrieves proposals that are not archived and not associated with any order."
        ),
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

        Returns:
            - Response: Serialized data of proposals.
        """
        try:
            proposals = Proposal.objects.filter(
                archive=False,
                is_deleted=False
            )

            if proposal_id:
                proposals = proposals.filter(id=proposal_id)

            proposals = proposals.exclude(
                id__in=Order.objects.values_list(
                    "proposal_id",
                    flat=True
                )
            )

            if not proposals.exists():
                return Response(
                    {"detail": "No proposals available."},
                    status=status.HTTP_200_OK,
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
        operation_description="Retrieve details of a specific order, including proposals and change orders.",
        manual_parameters=[
            openapi.Parameter(
                "order_id",
                openapi.IN_PATH,
                description="The ID of the order to edit.",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        responses={
            200: openapi.Response(
                description="Order details with associated proposals and change orders.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "order": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "proposal": openapi.Schema(type=openapi.TYPE_INTEGER, nullable=True),
                                "order_number": openapi.Schema(type=openapi.TYPE_STRING),
                                "status": openapi.Schema(type=openapi.TYPE_STRING),
                                "description": openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        ),
                        "proposals": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                    "name": openapi.Schema(type=openapi.TYPE_STRING),
                                }
                            )
                        ),
                        "change_orders": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                    "name": openapi.Schema(type=openapi.TYPE_STRING),
                                }
                            )
                        )
                    }
                )
            )
        }
    )
    def get(self, request, order_id):
        """
        Retrieve order details, associated proposals, and change orders.
        """
        # Fetch the order and related data
        this_order = OrderEditService.get_order(order_id)
        proposals = OrderService.get_proposals()
        change_orders = OrderEditService.get_change_orders(order_id)

        # Serialize the data for the frontend
        order_data = {
            "id": this_order.id,
            "proposal": this_order.proposal.id if this_order.proposal else None,
            "order_number": this_order.order_number,
            "status": this_order.status,
            "description": this_order.description,
        }

        proposals_data = [
            {"id": proposal.id, "name": proposal.name} for proposal in proposals
        ]

        change_orders_data = [
            {"id": change_order.id, "name": change_order.name} for change_order in change_orders
        ]

        return Response(
            {
                "order": order_data,
                "proposals": proposals_data,
                "change_orders": change_orders_data,
            },
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        operation_description="Update an existing order by providing the updated fields.",
        request_body=OrderSerializer,
        responses={
            200: openapi.Response(
                description="Order updated successfully or redirection details.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: openapi.Response(
                description="Validation errors.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    additional_properties=openapi.Schema(type=openapi.TYPE_STRING)
                )
            )
        }
    )
    def put(self, request, order_id):
        """
        Update an existing order.
        """
        this_order = OrderEditService.get_order(order_id)
        serializer = OrderSerializer(this_order, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Order updated successfully!"}, status=status.HTTP_200_OK)
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
                    }
                ),
            ),
            403: openapi.Response(
                description="User is not authorized to delete the order.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING),
                    }
                ),
            ),
        }
    )
    def delete(self, request, order_id):
        this_order = OrderService.get_order(order_id)
        try:
            # Check user permissions
            OrderService.validate_user_permission(this_order, request.user)

            OrderService.delete_order(this_order)
            return Response({"message": "Order deleted successfully!"}, status=status.HTTP_200_OK)

        except PermissionDenied as e:
            # Return error if the user is unauthorized
            return Response(
                {"error": str(e)},
                status=status.HTTP_403_FORBIDDEN
            )


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
                    }
                ),
            ),
            403: openapi.Response(
                description="User is not authorized to archive the order.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING),
                    }
                ),
            ),
        }
    )
    def post(self, request, order_id):
        # Fetch the order
        this_order = OrderService.get_order(order_id)

        try:
            # Check user permissions
            OrderService.validate_user_permission(this_order, request.user)

            OrderService.archive_order(this_order)
            return Response({"message": "Order archived successfully!"}, status=status.HTTP_200_OK)

        except PermissionDenied as e:
            # Return error if the user is unauthorized
            return Response(
                {"error": str(e)},
                status=status.HTTP_403_FORBIDDEN
            )


class ChangeOrderView(APIView):
    """
    API endpoint for creating a change order.

    This view handles:
    - Validating incoming data using a serializer.
    - Delegating business logic to the ChangeOrderServiceLayer.

    Methods:
        - post: Creates a new change order along with associated services and generates a PDF.

    Parameters:
        - order_id (int): The ID of the order to associate with the change order.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        """
        Handles the creation of a change order.

        Args:
            request: The HTTP request containing the data for the change order.
            order_id (int): The ID of the order to associate with the change order.

        Returns:
            Response: Success or error response based on the validation and execution.
        """
        this_order = get_object_or_404(
            Order,
            id=order_id,
            is_deleted=False,
        )

        serializer = ChangeOrderSerializer(data=request.data)
        if serializer.is_valid():
            # Instantiate the service layer and pass the required data
            change_order_service = ChangeOrderServiceLayer(
                order=this_order,
                user=request.user,
                data=request.data,
            )

            # Create the change order and associated services
            change_order = change_order_service.create_change_order()

            return Response(
                {'status': 'Change order created successfully', 'change_order_id': change_order.id},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangeOrderDeleteAPIView(APIView):
    """
    API View to delete a Change Order.
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, order_id, change_order_id):
        order = get_object_or_404(
            Order,
            id=order_id,
            is_deleted=False,
        )
        change_order = get_object_or_404(
            ChangeOrder,
            id=change_order_id,
            is_deleted=False,

        )

        # Service layer handling change order deletion
        service = DeleteChangeOrderService(order, request.user)
        success = service.delete_change_order(change_order)

        if success:
            return Response({"detail": "Change order deleted successfully."}, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "Change order not found."}, status=status.HTTP_404_NOT_FOUND)


class ChangeOrderApproveView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, change_order_id, action):
        try:
            # Call the service to approve the change order and generate the invoice PDF
            new_file_name = ChangeOrderServiceLayer.approve_change_order(
                change_order_id=change_order_id,
                action=action,
                user=request.user,
            )
            return Response(
                {"message": f"Change order approved and invoice generated successfully.", "file_name": new_file_name},
                status=status.HTTP_200_OK
            )
        except ChangeOrder.DoesNotExist:
            return Response(
                {"message": "Change order not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class TechLabelViewSet(ModelViewSet):
    queryset = TechLabel.objects.all()
    serializer_class = TechLabelSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'], url_path='update-extra-fields')
    def update_extra_fields(self, request, order_id=None):
        """
        Updates or creates a TechLabel and its extra fields.
        """
        this_order = get_object_or_404(
            Order,
            id=order_id,
            is_deleted=False,
        )
        tech_label = TechLabel.objects.filter(order__id=order_id).first()
        service = TechLabelServiceLayer(user=request.user, data=request.data)

        try:
            updated_tech_label = service.update_tech_label(tech_label, this_order)
            return Response({
                'message': 'TechLabel updated successfully!',
                'data': TechLabelSerializer(updated_tech_label).data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='download-pdf')
    def download_pdf(self, request, order_id=None):
        """
        Download the PDF associated with a TechLabel.
        """
        this_order = get_object_or_404(
            Order,
            id=order_id,
            is_deleted=False,
        )
        tech_label = TechLabel.objects.filter(
            order__id=order_id,
            is_deleted=False,

        ).first()

        service = TechLabelServiceLayer()
        try:
            local_path = service.generate_pdf(tech_label, this_order)
            if os.path.exists(local_path):
                with open(local_path, 'rb') as pdf_file:
                    response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                    response['Content-Disposition'] = f'inline; filename={os.path.basename(local_path)}'
                    return response
            return Response({'error': 'PDF not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        serializer = OrderControlSystemSerializer(order, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Control system updated successfully!'}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ControlSystemViewSet(ModelViewSet):
    """
    API for managing control systems, including listing, creating, updating, and deleting.
    """
    queryset = ControlSystem.objects.all()
    serializer_class = ControlSystemSerializer


class OrderEquipmentSubmittalView(APIView):
    """
    API view to handle order equipment submittal actions including
    uploading files, clearing submittal, and updating the order.
    """
    permission_classes = [IsAuthenticated]

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

            # Handle clearing the equipment submittal
            if request.data.get("equipment_submittal-clear"):
                OrderEquipmentSubmittalService.clear_equipment_submittal(order_id)
                return Response(
                    {"detail": "Equipment submittal cleared."},
                    status=status.HTTP_200_OK
                )

            # Handle files upload and processing
            files = request.FILES.getlist('equipment_submittal')
            OrderEquipmentSubmittalService.update_order_with_equipment_submittal(order, files)

            return Response(
                {"detail": "Equipment submittal updated successfully."},
                status=status.HTTP_200_OK
            )

        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {"detail": "An error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OrderFieldDrawingView(APIView):
    """
    API View to handle the field drawing upload process for an order.

    This view handles the following actions:
    - Uploading field drawings as files.
    - Validating uploaded files for size and saving them after processing.
    - Creating a zip file of the uploaded field drawings.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        """
        Handle the POST request to upload and process field drawing files for an order.

        Depending on the data passed, the following actions are performed:
        - If the field drawings are provided, the files are validated and processed.
          If valid, the files are saved, and a zip file is created and associated with the order.

        Args:
            request (Request): The HTTP request object containing the data and files.
            order_id (int): The ID of the order to which the field drawings belong.

        Returns:
            Response: A DRF Response object with either success or error details.
        """
        try:
            # Fetch the order instance
            order = get_object_or_404(
                Order,
                id=order_id,
                is_deleted=False,
            )

            # Handle form submission for field drawing files
            if 'field_drawing' in request.FILES:
                files = request.FILES.getlist('field_drawing')
                OrderFieldDrawingService.process_field_drawing_files(order, files)
                return Response(
                    {"detail": "Field drawing updated successfully."},
                    status=status.HTTP_200_OK
                )

            return Response(
                {"detail": "No files provided."},
                status=status.HTTP_400_BAD_REQUEST
            )

        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {"detail": "An error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OrderGeneralNotesView(APIView):
    """
    API View to handle the general notes and comments for an order.

    This view allows:
    - Retrieving the general notes and comments for an order (GET request).
    - Saving the general notes and comments (POST request with "save" action).
    - Finalizing the general notes and comments (POST request with "finalize" action).
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        """
        Handle POST request to save, finalize

        Args:
            request (Request): The HTTP request object containing the data.
            order_id (int): The ID of the order to update.

        Returns:
            Response: DRF Response indicating success or failure of the action.
        """
        # Retrieve the order object by ID
        order = get_object_or_404(
            Order,
            id=order_id,
            is_deleted=False,
        )

        # Extract general notes and comments from the request data
        general_notes_and_comments = str(request.data.get('general_notes_and_comments', ""))

        # If "finalize" action is pressed, finalize the general notes and save them
        if request.data.get('finalize'):
            order.general_notes_and_comments = general_notes_and_comments
            order.general_notes_and_comments_finalize = True
            order.save()
            return Response(
                {"detail": "General notes finalized and saved."},
                status=status.HTTP_200_OK
            )

        # If "save" action is pressed, save the general notes without finalizing
        if request.data.get("save"):
            order.general_notes_and_comments = general_notes_and_comments
            order.save()
            return Response(
                {"detail": "General notes saved successfully."},
                status=status.HTTP_200_OK
            )

        # If no valid action is found, return a bad request error
        return Response(
            {"detail": "Invalid action or missing data."},
            status=status.HTTP_400_BAD_REQUEST
        )

    def get(self, request, order_id):
        """
        Handle GET request to retrieve the general notes and comments for an order.

        Args:
            request (Request): The HTTP request object.
            order_id (int): The ID of the order to retrieve.

        Returns:
            Response: DRF Response containing the general notes and comments of the order.
        """
        order = get_object_or_404(
            Order,
            id=order_id,
            is_deleted=False,
        )

        # Return the general notes and comments of the order
        return Response(
            {"general_notes_and_comments": order.general_notes_and_comments},
            status=status.HTTP_200_OK
        )


class OrderSitePicturesView(APIView):
    """
    API View to handle uploading and saving site pictures for an order.
    """
    permission_classes = [IsAuthenticated]

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
            service = OrderSitePicturesService(order_id, request.FILES.getlist('site_pictures'))
            zip_file_name = service.process_upload()
            return Response({"detail": f"Site pictures uploaded and saved as {zip_file_name}."},
                            status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": "An error occurred during the upload process."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            return Response({"site_pictures": order.site_pictures.url}, status=status.HTTP_200_OK)

        return Response({"message": "No site pictures available for this order."}, status=status.HTTP_404_NOT_FOUND)


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
                {"detail": "Order not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
