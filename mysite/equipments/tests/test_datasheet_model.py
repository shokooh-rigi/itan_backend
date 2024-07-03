import factory
from factory.django import DjangoModelFactory
from ..models import Equipment, DataSheet
import pytest
from django.urls import reverse
# from mysite.order.models import Order
from mysite.dbmanagement.models import EquipmentManufacturer as Manufacturer


# class OrderFactory(DjangoModelFactory):
#     class Meta:
#         model = Order


class EquipmentFactory(DjangoModelFactory):
    class Meta:
        model = Equipment

    name = factory.Faker('word')
    price = factory.Faker('pydecimal', left_digits=6, right_digits=2, positive=True)
    form_fields = factory.Dict({'foo': 'bar'})
    # # Assuming you have some existing Service and TestSheet instances you can associate with
    # service = factory.SubFactory(ServiceFactory)  # You need to define this factory
    # test_sheet = factory.SubFactory(TestSheetFactory)  # You need to define this factory
    # Include default values or factories for any other required fields


class ManufacturerFactory(DjangoModelFactory):
    class Meta:
        model = Manufacturer

    # define fields

class DataSheetFactory(DjangoModelFactory):
    class Meta:
        model = DataSheet

    # project = factory.SubFactory(OrderFactory)
    equipment_type = factory.SubFactory(EquipmentFactory)
    manufacturer = factory.SubFactory(ManufacturerFactory)
    system = factory.Faker('word')
    # define other fields as required


@pytest.mark.django_db
def test_create_data_sheet():
    data_sheet = DataSheetFactory()
    assert DataSheet.objects.count() == 1

@pytest.mark.django_db
def test_read_data_sheet():
    data_sheet = DataSheetFactory()
    fetched_sheet = DataSheet.objects.get(id=data_sheet.id)
    assert fetched_sheet == data_sheet

@pytest.mark.django_db
def test_update_data_sheet():
    data_sheet = DataSheetFactory()
    data_sheet.system = 'New System'
    data_sheet.save()
    updated_sheet = DataSheet.objects.get(id=data_sheet.id)
    assert updated_sheet.system == 'New System'

@pytest.mark.django_db
def test_delete_data_sheet():
    data_sheet = DataSheetFactory()
    id = data_sheet.id
    data_sheet.delete()
    with pytest.raises(DataSheet.DoesNotExist):
        DataSheet.objects.get(id=id)
