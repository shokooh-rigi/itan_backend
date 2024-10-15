# from datetime import datetime
# import pytest
# from django.urls import reverse
# from rest_framework.test import APIClient
# from rest_framework import status
# from ...models import DataSheet, Order, Equipment
# from mysite.estimator.models import Proposal, Quote, Estimate
# from mysite.dbmanagement.models import EquipmentManufacturer as Manufacturer
# from custom_user.models import User
# import factory
# from factory.django import DjangoModelFactory
# from .test_equipment import EquipmentFactory
# import json


# class UserFactory(DjangoModelFactory):
#     class Meta:
#         model = User

#     email = factory.Sequence(lambda n: f"user{n}@example.com")
#     password = factory.PostGenerationMethodCall('set_password', 'defaultpassword')
#     is_active = True


# class EstimateFactory(DjangoModelFactory):
#     class Meta:
#         model = Estimate

#     due_date = factory.LazyFunction(lambda: datetime.now().strftime('%Y-%m-%d'))
#     created_by = factory.SubFactory(UserFactory)


# class QuoteFactory(DjangoModelFactory):
#     class Meta:
#         model = Quote

#     estimate = factory.SubFactory(EstimateFactory)


# class ProposalFactory(DjangoModelFactory):
#     class Meta:
#         model = Proposal

#     quote = factory.SubFactory(QuoteFactory)


# class OrderFactory(DjangoModelFactory):
#     class Meta:
#         model = Order

#     proposal = factory.SubFactory(ProposalFactory)


# class EquipmentFactory(DjangoModelFactory):
#     class Meta:
#         model = Equipment

#     price = factory.LazyFunction(lambda: 1000)

# class ManufacturerFactory(DjangoModelFactory):
#     class Meta:
#         model = Manufacturer

#     # Add necessary fields and default values


# class DataSheetFactory(DjangoModelFactory):
#     class Meta:
#         model = DataSheet

#     project = factory.SubFactory(OrderFactory)
#     system = factory.Sequence(lambda n: f"System {n}")
#     equipment_type = factory.SubFactory(EquipmentFactory)
#     # manufacturer = factory.SubFactory(ManufacturerFactory)


# @pytest.mark.django_db
# class TestDataSheetAPI:
#     client = APIClient()

#     def setup_method(self, method):
#         self.user = UserFactory()
#         self.client.force_authenticate(user=self.user)

#     def test_create_data_sheet(self):
#         url = reverse('create-data-sheet')
#         estimate = Estimate.objects.create(
#             due_date=datetime.now().strftime('%Y-%m-%d'),
#             created_by=self.user
#         )
#         quote = Quote.objects.create(estimate=estimate)
#         proposal = Proposal.objects.create(quote=quote)
#         project = Order.objects.create(proposal=proposal)

#         equipment = Equipment.objects.create(
#             name="New Equipment",
#             price=1000,
#         )
#         # data_sheet_1 = DataSheetFactory()
#         # data_sheet2 = DataSheetFactory()
#         data = {
#             "data": [
#                 {
#                     'name': 'New Data Sheet',
#                     'project': project.id,
#                     'sheet_date': '2021-05-01',
#                     'system': 'New System',
#                     'equipment_type': equipment.name,
#                     'equipment': equipment.name,
#                     # 'manufacturer': ManufacturerFactory().id,
#                 },
#                 {
#                     'name': 'New Data Sheet',
#                     'project': project.id,
#                     'sheet_date': '2021-05-01',
#                     'system': 'New System',
#                     'equipment_type': equipment.name,
#                     'equipment': equipment.name,
#                     # 'manufacturer': ManufacturerFactory().id,
#                 }
#         ]}
#         response = self.client.post(url, data, format='json')
#         assert response.status_code == status.HTTP_201_CREATED
#         assert response.data['system'] == 'New System'

#     # def test_retrieve_data_sheet(self):
#     #     # data_sheet = DataSheetFactory()
#     #     data_sheet = {
#     #         'name': 'New Data Sheet',
#     #         'project': OrderFactory().id,
#     #         'sheet_date': '2021-05-01',
#     #         'system': 'New System',
#     #         'equipment_type': EquipmentFactory().id,
#     #         'equipment': EquipmentFactory().id,
#     #         # 'manufacturer': ManufacturerFactory().id,
#     #     }
#     #     url = reverse('retrieve-data-sheet', args=[data_sheet.id])
#     #     response = self.client.get(url)
#     #     assert response.status_code == status.HTTP_200_OK
#     #     assert response.data['id'] == data_sheet.id

#     # def test_update_data_sheet(self):
#     #     # data_sheet = DataSheetFactory(name="Old Name")
#     #     data_sheet = {
#     #         'name': 'New Data Sheet',
#     #         'project': OrderFactory().id,
#     #         'sheet_date': '2021-05-01',
#     #         'system': 'New System',
#     #         'equipment_type': EquipmentFactory().id,
#     #         'equipment': EquipmentFactory().id,
#     #         # 'manufacturer': ManufacturerFactory().id,
#     #     }
#     #     url = reverse('update-data-sheet', args=[data_sheet.id])
#     #     data = {'name': 'New Name'}
#     #     response = self.client.patch(url, data, format='json')
#     #     assert response.status_code == status.HTTP_200_OK
#     #     assert response.data['name'] == 'New Name'

#     # def test_delete_data_sheet(self):
#     #     # data_sheet = DataSheetFactory()
#     #     data_sheet = {
#     #         'name': 'New Data Sheet',
#     #         'project': OrderFactory().id,
#     #         'sheet_date': '2021-05-01',
#     #         'system': 'New System',
#     #         'equipment_type': EquipmentFactory().id,
#     #         'equipment': EquipmentFactory().id,
#     #         # 'manufacturer': ManufacturerFactory().id,
#     #     }
#     #     url = reverse('delete-data-sheets', args=[data_sheet.id])
#     #     response = self.client.delete(url)
#     #     assert response.status_code == status.HTTP_204_NO_CONTENT
#     #     assert not DataSheet.objects.filter(id=data_sheet.id).exists()
