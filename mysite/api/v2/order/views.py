import datetime
from django.core.exceptions import PermissionDenied

from django.conf import settings
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import OrderSerializer
from .services import OrderService, OrderEditService


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
            "now": datetime.datetime.now()
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
        - GET: Retrieves a list of proposals.
        - POST: Creates a new order.

    Query Parameters:
        - proposal_id (int): Optional ID of a specific proposal to fetch.
    """

    def get(self, request):
        """
        Retrieve proposals based on the provided proposal_id.
        """
        proposal_id = request.query_params.get("proposal_id", None)
        proposals = OrderService.get_proposals(proposal_id)
        data = [
            {
                "id": proposal.id,
                "name": proposal.name,  # Replace `name` with appropriate fields.
                "created_on": proposal.created_on,
            }
            for proposal in proposals
        ]
        return Response({"proposals": data}, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Handle the creation of a new order.
        """
        serializer = OrderSerializer(data=request.data)
        if request.data.get("cancel"):
            return Response({"message": "Order creation canceled."}, status=status.HTTP_200_OK)

        if serializer.is_valid():
            serializer.save()
            if request.data.get("next"):
                return Response({"message": "Order created successfully!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderEditAPIView(APIView):
    """
    API view for editing an existing order.

    Methods:
        - GET: Retrieve order details, proposals, and change orders.
        - PUT: Update the order based on user input.

    Path Parameters:
        - order_id (int): The ID of the order to edit.

    """

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

    def put(self, request, order_id):
        """
        Update an existing order.
        """
        this_order = OrderEditService.get_order(order_id)
        serializer = OrderSerializer(this_order, data=request.data)

        # Check for cancellation
        if request.data.get("cancel"):
            return Response({"message": "Order edit canceled."}, status=status.HTTP_200_OK)

        # Redirect actions based on custom keys
        redirection_keys = {
            "co": "changeOrder",
            "cs": "controlSystem",
            "es": "equipmentSubmittal",
            "tl": "techLabel",
            "ucd": "fieldDrawing",
            "usp": "sitePictures",
            "uts": "testSheets",
        }
        for key, redirect_url in redirection_keys.items():
            if request.data.get(key):
                return Response({"redirect_to": redirect_url, "order_id": order_id}, status=status.HTTP_200_OK)

        # Save the order if valid
        if serializer.is_valid():
            if request.data.get("save"):
                serializer.save()
                return Response({"message": "Order updated successfully!"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderDeleteAPIView(APIView):
    """
    API view for deleting an order.

    Methods:
        - POST: Deletes the specified order after confirming user permissions.
    """

    def delete(self, request, order_id):
        # Fetch the order
        this_order = OrderService.get_order(order_id)

        try:
            # Check user permissions
            OrderService.validate_user_permission(this_order, request.user)

            # Perform deletion if confirmed
            if request.data.get("confirm"):
                OrderService.delete_order(this_order)
                return Response({"message": "Order deleted successfully!"}, status=status.HTTP_200_OK)

        except PermissionDenied as e:
            # Return error if the user is unauthorized
            return Response(
                {"error": str(e)},
                status=status.HTTP_403_FORBIDDEN
            )

        # Redirect to the order home if not confirmed
        return Response(
            {"message": "Order deletion canceled."},
            status=status.HTTP_400_BAD_REQUEST
        )


class OrderArchiveAPIView(APIView):
    """
    API view for archiving an order.

    Methods:
        - POST: Archives the specified order after confirming user permissions.
    """

    def post(self, request, order_id):
        # Fetch the order
        this_order = OrderService.get_order(order_id)

        try:
            # Check user permissions
            OrderService.validate_user_permission(this_order, request.user)

            # Perform archiving if confirmed
            if request.data.get("confirm"):
                OrderService.archive_order(this_order)
                return Response({"message": "Order archived successfully!"}, status=status.HTTP_200_OK)

        except PermissionDenied as e:
            # Return error if the user is unauthorized
            return Response(
                {"error": str(e)},
                status=status.HTTP_403_FORBIDDEN
            )

        # Redirect to the order home if not confirmed
        return Response(
            {"message": "Order archiving canceled."},
            status=status.HTTP_400_BAD_REQUEST
        )
