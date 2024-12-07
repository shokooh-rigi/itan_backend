from custom_user.models import User
from mysite.order.models import *


# Create your models here.


class Schedule(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, blank=False, null=False)
    schedule_start = models.DateTimeField(blank=False, null=False)
    schedule_end = models.DateTimeField(blank=False, null=False)
    archive = models.BooleanField(default=False)
    pre_demo = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=False)

    class Meta:
        ordering = ["-created_on"]
        verbose_name = "Schedule List"
        verbose_name_plural = "Schedule List"

    def __str__(self):
        return self.order.project_number


class Maintenance(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, blank=True, null=True)
    assigned_to_employee = models.ForeignKey(
        User,
        blank=True,
        null=True,
        related_name="maintenance_assigned_to_employee",
        on_delete=models.CASCADE,
    )
    assigned_to_contractor = models.ForeignKey(
        User,
        blank=True,
        null=True,
        related_name="maintenance_assigned_to_contractor",
        on_delete=models.CASCADE,
    )
    schedule_start = models.DateTimeField(blank=False, null=False)
    schedule_end = models.DateTimeField(blank=False, null=False)
    description = models.TextField(max_length=500, blank=True)
    MAINTENANCE_TYPE_CHOICES = (
        (1, "Maintenance"),
        (2, "Lost Time"),
        (3, "Off/Vacation"),
    )
    maintenance_type = models.PositiveSmallIntegerField(
        choices=MAINTENANCE_TYPE_CHOICES, default=1
    )
    archive = models.BooleanField(default=False)
    settlement = models.BooleanField(default=False)
    tech_upload = models.FileField(upload_to="uploads/techfiles", blank=True, null=True)
    note = models.TextField(max_length=1000, blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=False)

    class Meta:
        ordering = ["-created_on"]
        verbose_name = "Maintenance List"
        verbose_name_plural = "Maintenance List"

    def __str__(self):
        return self.order.project_number


class ScheduleTech(models.Model):
    schedule = models.ForeignKey(
        Schedule, on_delete=models.CASCADE, blank=False, null=False
    )
    assigned_to_employee = models.ForeignKey(
        User,
        blank=True,
        null=True,
        related_name="assigned_to_employee",
        on_delete=models.CASCADE,
    )
    assigned_to_contractor = models.ForeignKey(
        User, blank=True, null=True, on_delete=models.CASCADE
    )
    involvement_percentage = models.PositiveIntegerField(
        default=0, validators=[MaxValueValidator(100), MinValueValidator(0)]
    )
    settlement = models.BooleanField(default=False)
    tech_upload = models.FileField(upload_to="uploads/techfiles", blank=True, null=True)
    note = models.TextField(max_length=1000, blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_on"]
        verbose_name = "Schedule Technicians"
        verbose_name_plural = "Schedule Technicians"

    def __str__(self):
        return (
            str(self.assigned_to_employee)
            + str(self.assigned_to_contractor)
            + " "
            + str(self.schedule.order.project_number)
        )
