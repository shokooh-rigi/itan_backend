import factory
from django.utils import timezone
from ..models import TestSheet
import pytest


class TestSheetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TestSheet

    name = factory.Sequence(lambda n: f"Sheet {n}")
    inheritance = None  # Assuming it can be null
    priority = factory.Sequence(lambda n: n)
    created_on = factory.LazyFunction(timezone.now)
    sheet_generator = False
    flag = True
    form_fields = factory.LazyFunction(lambda: {"field1": "value1", "field2": "value2"})




@pytest.mark.django_db
def test_create_test_sheet():
    test_sheet = TestSheetFactory()
    assert TestSheet.objects.count() == 1
    assert TestSheet.objects.get(pk=test_sheet.pk) == test_sheet

@pytest.mark.django_db
def test_read_test_sheet():
    test_sheet = TestSheetFactory(name="Unique Sheet")
    fetched_sheet = TestSheet.objects.get(name="Unique Sheet")
    assert fetched_sheet == test_sheet

@pytest.mark.django_db
def test_update_test_sheet():
    test_sheet = TestSheetFactory()
    test_sheet.name = "Updated Name"
    test_sheet.save()
    updated_sheet = TestSheet.objects.get(pk=test_sheet.pk)
    assert updated_sheet.name == "Updated Name"

@pytest.mark.django_db
def test_delete_test_sheet():
    test_sheet = TestSheetFactory()
    sheet_id = test_sheet.id
    test_sheet.delete()
    with pytest.raises(TestSheet.DoesNotExist):
        TestSheet.objects.get(pk=sheet_id)
