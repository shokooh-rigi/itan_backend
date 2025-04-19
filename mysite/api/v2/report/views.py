from datetime import datetime

from django.db.models import Sum
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from mysite.api.v2.report.serializers import PerformanceReportSerializer, JobCostingSerializer
from mysite.bidfilemgm.models import BidFile
from mysite.core.models import Company, Person
from mysite.estimator.models import Estimate
from mysite.gi.models import Invoice
from mysite.order.models import Order
from mysite.proposal.models import Proposal


class PerformanceListView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Generate aggregated report for Bids, Estimates, Proposals, Orders, and Invoices",
        operation_description="Get data for a specific date range and customer type (Company/Person).",
        manual_parameters=[
            openapi.Parameter(
                "from_date",
                openapi.IN_QUERY,
                description="Start date (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                "to_date",
                openapi.IN_QUERY,
                description="End date (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                "customer_type",
                openapi.IN_QUERY,
                description="Type of customer (company/person)",
                type=openapi.TYPE_STRING,
                enum=["company", "person"],
                required=True
            ),
        ],
        responses={200: PerformanceReportSerializer()},
    )
    def get(self, request):
        """Generate report based on Bids, Estimates, Proposals, Orders, and Invoices."""
        from_date = request.GET.get("from_date")
        to_date = request.GET.get("to_date")
        customer_type = request.GET.get("customer_type")

        try:
            from_date = datetime.strptime(from_date, "%Y-%m-%d").date()
            to_date = datetime.strptime(to_date, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if customer_type == "company":
            customers = Person.objects.filter(company__in=Company.objects.all())
            customer_filter = {"customer__in": customers}
        elif customer_type == "person":
            customers = Person.objects.all()
            customer_filter = {"customer__in": customers}
        else:
            return Response(
                {"error": "Invalid customer type. Valid types are company/person."},
                status=status.HTTP_400_BAD_REQUEST
            )

        bids = BidFile.objects.filter(
            created_on__range=(from_date, to_date),
            **customer_filter
        )
        estimates = Estimate.objects.filter(
            created_on__range=(from_date, to_date),
            **customer_filter
        )
        proposals = Proposal.objects.filter(
            created_on__range=(from_date, to_date),
            estimate__customer__in=customers
        )
        orders = Order.objects.filter(
            created_on__range=(from_date, to_date),
            proposal__estimate__customer__in=customers
        )
        invoices = Invoice.objects.filter(
            created_on__range=(from_date, to_date),
            order__proposal__estimate__customer__in=customers
        )
        estimate_total = sum(estimate.sub_total for estimate in estimates)
        proposal_total = sum(proposal.estimate.sub_total for proposal in proposals if proposal.estimate)
        response_data = {
            "customer_type": customer_type,
            "from_date": from_date,
            "to_date": to_date,
            "bid_count": bids.count(),
            "estimate_count": estimates.count(),
            "estimate_total": estimate_total,
            "proposal_count": proposals.count(),
            "proposal_total": proposal_total,
            "order_count": orders.count(),
            "order_total": orders.aggregate(total=Sum("amount"))["total"] or 0,
            "invoice_count": invoices.count(),
            "invoice_total": invoices.aggregate(total=Sum("total_invoiced"))["total"] or 0,
        }

        serializer = PerformanceReportSerializer(response_data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class JobCostingListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get Job Costing Data",
        description="Returns a list of job costing details including estimated/actual hours and price.",
        responses={200: JobCostingSerializer(many=True)},
    )
    def get(self, request):
        orders = Order.objects.filter(invoice__isnull=False).order_by("created_on")
        serializer = JobCostingSerializer(orders, many=True)
        return Response(serializer.data)
