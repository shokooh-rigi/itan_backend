from mysite.core.models import *
from mysite.estimator.models import *
from mysite.order.models import *
import datetime

# Create your models here.


class TestSheetColumn(models.Model):
    test_sheet = models.ForeignKey(TestSheet, on_delete=models.CASCADE, blank=False, null=False)
    column_title = models.CharField(max_length=50, blank=False)

    def __str__(self):
        return self.test_sheet.name + " " + self.column_title


class Sheet(models.Model):
    test_sheet_type = models.ForeignKey(TestSheet, on_delete=models.CASCADE, blank=False, null=False)
    project = models.ForeignKey(Order, on_delete=models.CASCADE, blank=False, null=False)
    sheet_date = models.DateField(default=datetime.datetime.now().strftime("%m/%d/%Y"), blank=False, null=True)
    system = models.CharField(max_length=50, blank=False)

    def __str__(self):
        return self.test_sheet_type.name + " " + self.project.project_number


class SheetEquipment(models.Model):
    sheet = models.ForeignKey(Sheet, on_delete=models.CASCADE, blank=False, null=False)
    equipment_type = models.ForeignKey(Equipment, on_delete=models.CASCADE, blank=False, null=False)
    equipment = models.ForeignKey(EquipmentDb, on_delete=models.CASCADE, blank=True, null=True)
    main_data_entry_completed = models.BooleanField(default=False)
    actual_data_entry_completed = models.BooleanField(default=False)

    def __str__(self):
        return str(self.sheet) + ": " + self.equipment_type.name


class SheetEquipmentCommonData(models.Model):
    sheet_equipment = models.ForeignKey(SheetEquipment, on_delete=models.CASCADE, blank=False, null=False)
    key = models.ForeignKey(TestSheetColumn, on_delete=models.CASCADE, blank=False, null=False)
    value = models.CharField(max_length=50, blank=False)

    def __str__(self):
        return str(self.sheet_equipment) + " " + self.key.column_title


class SheetEquipmentActualData(models.Model):
    sheet_equipment = models.ForeignKey(SheetEquipment, on_delete=models.CASCADE, blank=False, null=False)
    key = models.ForeignKey(EquipmentCustomField, on_delete=models.CASCADE, blank=False, null=False)
    value = models.CharField(max_length=50, blank=False)

    def __str__(self):
        return str(self.sheet_equipment) + " " + self.key.equipment_value_name
