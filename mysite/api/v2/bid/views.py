from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from mysite.bidfilemgm.models import BidFile


class BidFileArchiveView(APIView):
    """
    Archives a bid file if the user is authorized and confirms the action.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        bid_file = get_object_or_404(BidFile, id=id)

        # Check if the requesting user is the creator of the bid file
        if bid_file.created_by != request.user:
            return Response(
                {"error": "You are not authorized to archive this record."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Confirm archiving action
        if request.data.get("confirm"):
            bid_file.archive = True
            bid_file.save()
            return Response(
                {"message": "Bid file archived successfully"},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"error": "Confirmation not received for archiving."},
            status=status.HTTP_400_BAD_REQUEST,
        )
