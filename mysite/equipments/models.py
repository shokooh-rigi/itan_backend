from django.db import models
from mysite.core.models import Service
from mysite.order.models import Order
from mysite.dbmanagement.models import EquipmentManufacturer as Manufacturer
# from mysite.dbmanagement.models import TestSheet


class TestSheet(models.Model):
    name = models.CharField(max_length=255, blank=False)
    inheritance = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)
    priority = models.IntegerField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    sheet_generator = models.BooleanField(default=False)
    flag = models.BooleanField(default=True)
    form_fields = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ["priority"]
        verbose_name = 'Test Sheet'
        verbose_name_plural = 'Test Sheet'

    def __str__(self):
        return self.name


# class Manufacturer(models.Model):
#     name = models.CharField(max_length=255, blank=False, unique=True)
#     tel = models.CharField(max_length=15, blank=True)
#     fax = models.CharField(max_length=15, blank=True)
#     mail = models.EmailField(max_length=55, blank=True)
#     web = models.CharField(max_length=55, blank=True)
#     address_line_1 = models.CharField(max_length=255, blank=True)
#     address_line_2 = models.CharField(max_length=255, blank=True)
#     city = models.CharField(max_length=55, blank=True)
#     state = models.CharField(max_length=55, blank=True)
#     zip = models.CharField(max_length=10, blank=True, null=True)
#     created_on = models.DateTimeField(auto_now_add=True)
#     flag = models.BooleanField(default=True)

#     def __str__(self):
#         return self.name




class Equipment(models.Model):
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, blank=False, null=True, related_name='equipments')
    test_sheet = models.ForeignKey(TestSheet, on_delete=models.SET_NULL, blank=True, null=True, related_name='equipments')
    name = models.CharField(max_length=255, blank=False)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    estimate_work = models.IntegerField(default=10, blank=False, null=False, verbose_name='Estimate Work in Minutes')
    created_on = models.DateTimeField(auto_now_add=True)
    flag = models.BooleanField(default=True)
    form_fields = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ["name"]
        verbose_name = 'Equipment'
        verbose_name_plural = 'Equipments'

    def __str__(self):
        return self.name + ' (' + self.service.name + ')'


class DataSheet(models.Model):
    name = models.CharField(max_length=255, blank=False)
    project = models.ForeignKey(Order, on_delete=models.CASCADE, blank=False, null=True, related_name='data_sheets')
    sheet_date = models.DateField(blank=False, null=True)
    system = models.CharField(max_length=50, blank=False)
    # number_of_equipment_groups = models.IntegerField(default=1, blank=False)
    archive = models.BooleanField(default=False)

    rogue_design_data_entry_completed = models.BooleanField(default=False)
    rogue_actual_data_entry_completed = models.BooleanField(default=False)

    main_data_entry_confirmed = models.BooleanField(default=False)
    design_data_entry_confirmed = models.BooleanField(default=False)
    actual_data_entry_confirmed = models.BooleanField(default=False)

    main_data_entry_completed = models.BooleanField(default=False)
    design_data_entry_completed = models.BooleanField(default=False)
    actual_data_entry_completed = models.BooleanField(default=False)
    terminal_design_data_entry_completed = models.BooleanField(default=False)
    terminal_actual_data_entry_completed = models.BooleanField(default=False)

    form_fields = models.JSONField(blank=True, null=True)
    info = models.JSONField(blank=True, null=True)

    # EQDB
    equipment_type = models.ForeignKey(Equipment, on_delete=models.CASCADE, blank=False, null=False, related_name='data_sheets')
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.SET_NULL, blank=True, null=True, related_name='data_sheets')
    model_number = models.CharField(max_length=50, blank=True, null=True)
    equipment_submittal = models.FileField(upload_to='uploads/equipmentDb/equipment_submittal', blank=True, null=True)
    image = models.FileField(upload_to='uploads/equipmentDb/image', blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    flag = models.BooleanField(default=True)


    # EQ
    equipment_group = models.CharField(max_length=50, default='A', blank=False)
    number_of_supply_air_terminal = models.SmallIntegerField(default=0, blank=False, null=False)
    number_of_return_air_terminal = models.SmallIntegerField(default=0, blank=False, null=False)
    number_of_outside_air_terminal = models.SmallIntegerField(default=0, blank=False, null=False)
    number_of_exhaust_air_terminal = models.SmallIntegerField(default=0, blank=False, null=False)

    # Air terminal
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)
    code = models.CharField(max_length=128, blank=True, null=True)
    _default = models.CharField(max_length=10, blank=True)
    size_type = models.PositiveSmallIntegerField(default=2, null=False, verbose_name='No. of Size Fields')
    is_custom = models.BooleanField(default=False)

    outlet_no = models.SmallIntegerField(blank=False, null=False, default=0)
    _type = models.PositiveSmallIntegerField(default=1, null=False)
    other_group = models.SmallIntegerField(blank=True, null=True)

    fan_no = models.CharField(max_length=30, blank=True, null=True)
    location = models.CharField(max_length=30, blank=True, null=True)
    area_served = models.CharField(max_length=30, blank=True, null=True)
    serial_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.equipment_type.test_sheet.name + " " + self.project.project_number

    class Meta:
        verbose_name = 'Data Sheet'
        verbose_name_plural = 'Data Sheets'
    