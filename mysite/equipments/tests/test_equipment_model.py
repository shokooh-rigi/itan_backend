# In your tests/factories.py file
import factory
from factory.django import DjangoModelFactory
from ..models import Equipment
import pytest
# from mysite.core.models import Service
# from mysite.dbmanagement.models import TestSheet
from ..models import TestSheet


# class ServiceFactory(DjangoModelFactory):
#     class Meta:
#         model = Service
#     name = factory.Faker('name')

class TestSheetFactory(DjangoModelFactory):
    class Meta:
        model = TestSheet
    # Add necessary fields here

class EquipmentFactory(DjangoModelFactory):
    class Meta:
        model = Equipment

    # service = factory.SubFactory(ServiceFactory)
    test_sheet = factory.SubFactory(TestSheetFactory)
    name = factory.Faker('word')
    price = factory.Faker('pydecimal', left_digits=6, right_digits=2, positive=True)
    estimate_work = 10
    form_fields = factory.Faker('pydict', value_types=['str', 'int', 'float'])




@pytest.mark.django_db
def test_create_equipment():
    equipment = EquipmentFactory(
        name="New Equipment",
        price=99.99
    )
    assert equipment.name == "New Equipment"
    assert equipment.price == 99.99
    assert Equipment.objects.count() == 1


@pytest.mark.django_db
def test_read_equipment():
    equipment = EquipmentFactory()
    fetched_equipment = Equipment.objects.get(id=equipment.id)
    assert fetched_equipment == equipment


@pytest.mark.django_db
def test_update_equipment():
    equipment = EquipmentFactory(price=50.00)
    equipment.price = 75.00
    equipment.save()
    updated_equipment = Equipment.objects.get(id=equipment.id)
    assert updated_equipment.price == 75.00


@pytest.mark.django_db
def test_delete_equipment():
    equipment = EquipmentFactory()
    equipment_id = equipment.id
    equipment.delete()
    with pytest.raises(Equipment.DoesNotExist):
        Equipment.objects.get(id=equipment_id)

