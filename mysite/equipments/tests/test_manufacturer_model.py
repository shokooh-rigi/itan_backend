# # In your tests directory, create a file factories.py

# import factory
# import pytest
# from ..models import Manufacturer
# from factory.django import DjangoModelFactory

# class ManufacturerFactory(DjangoModelFactory):
#     class Meta:
#         model = Manufacturer

#     name = factory.Faker('company')
#     tel = factory.Faker('phone_number')
#     fax = factory.Faker('phone_number')
#     mail = factory.Faker('email')
#     web = factory.Faker('url')
#     address_line_1 = factory.Faker('street_address')
#     address_line_2 = factory.Faker('street_address')
#     city = factory.Faker('city')
#     state = factory.Faker('state')
#     zip = factory.Faker('zipcode')
#     flag = True


# @pytest.mark.django_db
# class TestManufacturerCRUD:
#     def test_create_manufacturer(self):
#         """ Test creation of Manufacturer instance. """
#         manufacturer_data = ManufacturerFactory.build()
#         manufacturer = Manufacturer.objects.create(**manufacturer_data)
#         assert Manufacturer.objects.count() == 1
#         assert manufacturer.name == manufacturer_data.name

#     def test_read_manufacturer(self):
#         """ Test reading Manufacturer instances. """
#         manufacturer = ManufacturerFactory()
#         retrieved = Manufacturer.objects.get(id=manufacturer.id)
#         assert retrieved == manufacturer

#     def test_update_manufacturer(self):
#         """ Test updating Manufacturer instance. """
#         manufacturer = ManufacturerFactory()
#         Manufacturer.objects.filter(id=manufacturer.id).update(name="Updated Name")
#         manufacturer.refresh_from_db()
#         assert manufacturer.name == "Updated Name"

#     def test_delete_manufacturer(self):
#         """ Test deleting Manufacturer instance. """
#         manufacturer = ManufacturerFactory()
#         manufacturer_id = manufacturer.id
#         manufacturer.delete()
#         with pytest.raises(Manufacturer.DoesNotExist):
#             Manufacturer.objects.get(id=manufacturer_id)
