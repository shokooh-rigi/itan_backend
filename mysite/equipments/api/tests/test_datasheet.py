import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from ...models import DataSheet
from custom_user.models import User
import factory
from factory.django import DjangoModelFactory
from .test_equipment import EquipmentFactory


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    password = factory.PostGenerationMethodCall('set_password', 'defaultpassword')
    is_active = True


# class OrderFactory(DjangoModelFactory):
#     class Meta:
#         model = Order

#     # Add necessary fields and default values

# class EquipmentFactory(DjangoModelFactory):
#     class Meta:
#         model = Equipment

#     # Add necessary fields and default values

# class ManufacturerFactory(DjangoModelFactory):
#     class Meta:
#         model = Manufacturer

#     # Add necessary fields and default values

class DataSheetFactory(DjangoModelFactory):
    class Meta:
        model = DataSheet

    # project = factory.SubFactory(OrderFactory)
    system = factory.Sequence(lambda n: f"System {n}")
    equipment_type = factory.SubFactory(EquipmentFactory)
    # manufacturer = factory.SubFactory(ManufacturerFactory)
    # Other fields with defaults or sequences as needed


@pytest.mark.django_db
class TestDataSheetAPI:
    client = APIClient()

    def setup_method(self, method):
        # Create and authenticate the user for each test
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)  # Authenticate the user

    def test_create_data_sheet(self):
        url = reverse('create-data-sheet')
        data = {
            'system': 'New System',
            'number_of_equipment_groups': 1,
            'archive': False,
            # other fields as required
            'name': 'Sheet 1',
            'equipment_type': EquipmentFactory().id,
        }
        response = self.client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['system'] == 'New System'

    def test_retrieve_data_sheet(self):
        data_sheet = DataSheetFactory()
        url = reverse('retrieve-data-sheet', args=[data_sheet.id])
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == data_sheet.id

    def test_update_data_sheet(self):
        data_sheet = DataSheetFactory(system="Old System")
        url = reverse('update-data-sheet', args=[data_sheet.id])
        data = {'system': 'Updated System'}
        response = self.client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['system'] == 'Updated System'

    def test_delete_data_sheet(self):
        data_sheet = DataSheetFactory()
        url = reverse('delete-data-sheet', args=[data_sheet.id])
        response = self.client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not DataSheet.objects.filter(id=data_sheet.id).exists()
