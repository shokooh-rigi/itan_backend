from ...models import Equipment
from custom_user.models import User
from mysite.core.models import Service
from mysite.dbmanagement.models import TestSheet

import factory
from factory import django

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status


# class ServiceFactory(django.DjangoModelFactory):
#     class Meta:
#         model = Service

#     name = "Default Service"

# class TestSheetFactory(django.DjangoModelFactory):
#     class Meta:
#         model = TestSheet

#     # Assuming TestSheet has a field 'details'
#     details = "Default details"


class UserFactory(django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    password = factory.PostGenerationMethodCall('set_password', 'defaultpassword')
    is_active = True


class EquipmentFactory(django.DjangoModelFactory):
    class Meta:
        model = Equipment

    # service = factory.SubFactory(ServiceFactory)
    # test_sheet = factory.SubFactory(TestSheetFactory)
    name = factory.Sequence(lambda n: f"Equipment {n}")
    price = 100.00
    estimate_work = 30
    flag = True


@pytest.mark.django_db
class TestEquipmentAPI:
    client = APIClient()

    def setup_method(self, method):
        # Create and authenticate the user for each test
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)  # Authenticate the user

    def test_create_equipment(self):
        url = reverse('create-equipment')
        data = {
            'name': 'New Equipment',
            'price': '150.50',
            # 'service': ServiceFactory().id,
            # 'test_sheet': TestSheetFactory().id,
            'estimate_work': 20,
            'flag': True
        }
        response = self.client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Equipment'

    def test_retrieve_equipment(self):
        equipment = EquipmentFactory()
        url = reverse('retrieve-equipment', args=[equipment.id])
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == equipment.id

    def test_update_equipment(self):
        equipment = EquipmentFactory(name="Old Equipment")
        url = reverse('update-equipment', args=[equipment.id])
        data = {'name': 'Updated Equipment'}
        response = self.client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Equipment'

    def test_delete_equipment(self):
        equipment = EquipmentFactory()
        url = reverse('delete-equipment', args=[equipment.id])
        response = self.client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Equipment.objects.filter(id=equipment.id).exists() is False
