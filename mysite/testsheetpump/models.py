import datetime
from mysite.sheetcreator.models import *

# Create your models here.


class PumpEquipment(models.Model):
    sheet = models.ForeignKey(DataSheet, on_delete=models.CASCADE, blank=False, null=False)
    equipment_type = models.ForeignKey(Equipment, on_delete=models.CASCADE, blank=True, null=True)
    equipment = models.ForeignKey(EquipmentDb, on_delete=models.CASCADE, blank=True, null=True)
    pump_number = models.CharField(max_length=20, blank=True, null=True)
    manufacturer = models.CharField(max_length=50, blank=True, null=True)
    main_data_entry_completed = models.BooleanField(default=False)
    design_data_entry_completed = models.BooleanField(default=False)
    actual_data_entry_completed = models.BooleanField(default=False)
    field_order = models.PositiveIntegerField(default=0, blank=False, null=False)

    def __str__(self):
        return str(self.sheet) + ": " + self.equipment_type.name

    class Meta(object):
        ordering = ['field_order']


class PumpSheetData(models.Model):
    data_type = models.PositiveSmallIntegerField(choices=DataTypeChoices.get_items(), default=1, null=False)
    pump_equipment = models.ForeignKey(PumpEquipment, on_delete=models.CASCADE, blank=False, null=False)
    sheet_field = models.ForeignKey(TestSheetField, on_delete=models.CASCADE, blank=False, null=False)
    value = models.CharField(max_length=500, blank=False)

    def __str__(self):
        return str(self.sheet_field) + ' ' + str(self.pump_equipment)

