from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from ..models import Equipment, DataSheet
from .serializers import EquipmentSerializer, DataSheetSerializer
from ast import literal_eval
from django.shortcuts import get_object_or_404
from mysite.order.models import Order
from datetime import datetime


@api_view(['POST'])
def create_equipment(request):
    serializer = EquipmentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def retrieve_equipment(request, pk):
    try:
        equipment = Equipment.objects.get(pk=pk)
    except Equipment.DoesNotExist:
        return Response({'error': 'Equipment not found.'}, status=status.HTTP_404_NOT_FOUND)
    serializer = EquipmentSerializer(equipment)
    return Response(serializer.data)

@api_view(['PUT', 'PATCH'])
def update_equipment(request, pk):
    try:
        equipment = Equipment.objects.get(pk=pk)
    except Equipment.DoesNotExist:
        return Response({'error': 'Equipment not found.'}, status=status.HTTP_404_NOT_FOUND)
    serializer = EquipmentSerializer(equipment, data=request.data, partial=True)  # 'PATCH' requests use partial=True
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def delete_equipment(request, pk):
    try:
        equipment = Equipment.objects.get(pk=pk)
    except Equipment.DoesNotExist:
        return Response({'error': 'Equipment not found.'}, status=status.HTTP_404_NOT_FOUND)
    equipment.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)



@api_view(['POST'])
def create_data_sheet(request):
    for i in request.data["data"]:
        order = get_object_or_404(Order, project_number=i["project"])
        eq = get_object_or_404(Equipment, name=i["equipment"])
        for j in range(int(i["qty"])):
            obj = DataSheet.objects.create(
                sheet_date=datetime.now().date(),
                equipment_type=eq,
                name=eq.name,
                project=order,
                form_fields=eq.form_fields,
            )
    return Response({"data": "data sheet created"})

@api_view(['GET'])
def retrieve_data_sheet(request, pk):
    try:
        data_sheet = DataSheet.objects.get(pk=pk)
    except DataSheet.DoesNotExist:
        return Response({'error': 'Data Sheet not found.'}, status=status.HTTP_404_NOT_FOUND)
    serializer = DataSheetSerializer(data_sheet)
    return Response(serializer.data)

@api_view(['PUT', 'PATCH'])
def update_data_sheet(request, pk):
    try:
        data_sheet = DataSheet.objects.get(pk=pk)
    except DataSheet.DoesNotExist:
        return Response({'error': 'Data Sheet not found.'}, status=status.HTTP_404_NOT_FOUND)
    serializer = DataSheetSerializer(data_sheet, data=request.data, partial=request.method == 'PATCH')
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def delete_data_sheet(request, pk):
    try:
        data_sheet = DataSheet.objects.get(pk=pk)
    except DataSheet.DoesNotExist:
        return Response({'error': 'Data Sheet not found.'}, status=status.HTTP_404_NOT_FOUND)
    data_sheet.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['DELETE'])
def clear_data_sheet(request, pk):
    order = get_object_or_404(Order, pk=pk)
    order.data_sheets.all().delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
