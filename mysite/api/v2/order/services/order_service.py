from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404

from mysite.order.models import Order, ChangeOrder
from mysite.proposal.models import Proposal


class OrderService:
    """
    Service layer for handling Order-related logic.
    """

    @staticmethod
    def get_filtered_orders(project_name: str, order_type: str, ordering: str):
        """
        Fetches filtered and ordered orders based on query parameters.

        Args:
            project_name (str): Project name or part of it to search for.
            order_type (str): Type of orders to filter by.
            ordering (str): Field for ordering the results.

        Returns:
            QuerySet: A filtered and ordered queryset of orders.
        """
        object_list = Order.objects.filter(
            Q(proposal__estimate__project__name__icontains=project_name)
            | Q(project_number__icontains=project_name)
            | Q(proposal__estimate__customer__company__name__icontains=project_name)
        ).order_by(ordering)

        if order_type == "all" or order_type is None:
            return object_list
        if order_type == "inprogress":
            return object_list.filter(invoice__isnull=True).filter(report__isnull=True)
        if order_type == "invoiced":
            return object_list.filter(invoice__isnull=False)
        if order_type == "notinvoiced":
            return object_list.filter(
                invoice__isnull=True,
                colored_drawing__isnull=False,
                report_colored_drawing__isnull=False,
            )
        if order_type == "reported":
            return object_list.filter(report__isnull=False)

        return object_list

    @staticmethod
    def get_proposals(proposal_id=None):
        """
        Retrieve proposals based on whether a specific proposal ID is provided.

        Args:
            proposal_id (int): Optional ID of a proposal.

        Returns:
            QuerySet: A queryset of proposals.
        """
        if proposal_id:
            return Proposal.objects.filter(id=proposal_id)
        return (
            Proposal.objects.filter(archive=False)
            .exclude(id__in=Order.objects.values_list("proposal_id", flat=True))
            .order_by("-created_on")
        )

    @staticmethod
    def get_order(order_id):
        """
        Retrieve a specific order by ID.
        """
        order = get_object_or_404(
            Order,
            id=order_id,
            is_deleted=False,
        )
        return order

    @staticmethod
    def validate_user_permission(order, user):
        """
        Validate if the user is authorized to perform an action on the order.
        """
        if order.proposal.estimate.created_by != user:
            raise PermissionDenied("You are not authorized to modify this record.")

    @staticmethod
    def delete_order(order):
        """
        Delete the given order.
        """
        order.delete()

    @staticmethod
    def archive_order(order):
        """
        Archive the given order.
        """
        order.archive = True
        order.save()


class OrderEditService:
    """
    Service layer for handling Order-related business logic.
    """

    @staticmethod
    def get_order(order_id):
        """
        Retrieve a specific order by ID.
        """
        order = get_object_or_404(
            Order,
            id=order_id,
            is_deleted=False,
        )
        return order

    @staticmethod
    def get_proposals():
        """
        Retrieve active proposals not linked to existing orders.
        """
        return Proposal.objects.filter(archive=False).exclude(
            id__in=Order.objects.values_list("proposal_id", flat=True)
        )

    @staticmethod
    def get_change_orders(order_id):
        """
        Retrieve all change orders related to a specific order.
        """
        return ChangeOrder.objects.filter(order=order_id)
