from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models
from django.db.models import Q

from custom_user.models import User
from mysite.core.base_model import BaseModelWithCreatedByUser, BaseModel
from mysite.core.models import UserTypeChoices, Profile
from mysite.order.models import Order


class Schedule(BaseModelWithCreatedByUser):
    """
    Represents a scheduled event related to an order.
    Includes information about the start and end times of the schedule.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        help_text="The order associated with this schedule."
    )
    schedule_start = models.DateTimeField(
        blank=False,
        null=False,
        help_text="The start time of the schedule."
    )
    schedule_end = models.DateTimeField(
        blank=False,
        null=False,
        help_text="The end time of the schedule."
    )
    pre_demo = models.BooleanField(
        default=False,
        help_text="Indicates whether the schedule is for a pre-demonstration."
    )

    class Meta:
        ordering = ["-created_on"]
        verbose_name = "Schedule List"
        verbose_name_plural = "Schedule List"

    def __str__(self):
        """
        Returns the project number of the associated order as the string representation.
        """
        return self.order.project_number

class Maintenance(BaseModelWithCreatedByUser):
    """
    Represents a maintenance activity related to an order.
    Includes details about the maintenance type, assigned personnel, and additional notes.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        help_text="The order associated with this maintenance activity."
    )
    assigned_to_employee = models.ForeignKey(
        User,
        blank=True,
        null=True,
        related_name="maintenance_assigned_to_employee",
        on_delete=models.CASCADE,
        help_text="The employee assigned to this maintenance task."
    )
    assigned_to_contractor = models.ForeignKey(
        User,
        blank=True,
        null=True,
        related_name="maintenance_assigned_to_contractor",
        on_delete=models.CASCADE,
        help_text="The contractor assigned to this maintenance task."
    )
    schedule_start = models.DateTimeField(
        blank=False,
        null=False,
        help_text="The start time of the maintenance schedule."
    )
    schedule_end = models.DateTimeField(
        blank=False,
        null=False,
        help_text="The end time of the maintenance schedule."
    )
    description = models.TextField(
        max_length=500,
        blank=True,
        help_text="A brief description of the maintenance task."
    )
    MAINTENANCE_TYPE_CHOICES = (
        (1, "Maintenance"),
        (2, "Lost Time"),
        (3, "Off/Vacation"),
    )
    maintenance_type = models.PositiveSmallIntegerField(
        choices=MAINTENANCE_TYPE_CHOICES,
        default=1,
        help_text="The type of maintenance task."
    )
    settlement = models.BooleanField(
        default=False,
        help_text="Indicates whether the task has been settled."
    )
    tech_upload = models.FileField(
        upload_to="uploads/techfiles",
        blank=True,
        null=True,
        help_text="File upload related to the maintenance task."
    )
    note = models.TextField(
        max_length=1000,
        blank=True,
        null=True,
        help_text="Additional notes related to the maintenance task."
    )

    class Meta:
        ordering = ["-created_on"]
        verbose_name = "Maintenance List"
        verbose_name_plural = "Maintenance List"

    def __str__(self):
        """
        Returns the project number of the associated order as the string representation.
        """
        return self.order.project_number


class ScheduleTech(BaseModel):
    """
    Represents a technician's involvement in a schedule.
    Includes details about assigned personnel, involvement percentage, and additional notes.
    """

    schedule = models.ForeignKey(
        Schedule,
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        help_text="The schedule associated with this technician."
    )
    assigned_to_employee = models.ForeignKey(
        User,
        blank=True,
        null=True,
        related_name="assigned_to_employee",
        on_delete=models.CASCADE,
        help_text="The employee assigned to this schedule."
    )
    assigned_to_contractor = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        help_text="The contractor assigned to this schedule."
    )
    involvement_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(100), MinValueValidator(0)],
        help_text="The percentage of involvement of the technician."
    )
    settlement = models.BooleanField(
        default=False,
        help_text="Indicates whether the task has been settled."
    )
    tech_upload = models.FileField(
        upload_to="uploads/techfiles",
        blank=True,
        null=True,
        help_text="File upload related to the technician's task."
    )
    note = models.TextField(
        max_length=1000,
        blank=True,
        null=True,
        help_text="Additional notes related to the technician's task."
    )

    class Meta:
        ordering = ["-created_on"]
        verbose_name = "Schedule Technicians"
        verbose_name_plural = "Schedule Technicians"

    def __str__(self):
        """
        Returns a string representation of the assigned technician and the associated schedule order.
        """
        return (
            str(self.assigned_to_employee)
            + str(self.assigned_to_contractor)
            + " "
            + str(self.schedule.order.project_number)
        )

    def get_users_and_tech(self):
        """
        Retrieve profiles of users with user_type as TECH or SUPER_TECH.
        """

        return Profile.objects.filter(
            Q(user_type=UserTypeChoices.TECH) | Q(user_type=UserTypeChoices.SUPER_TECH)
        )

    def save(self, *args, **kwargs):
        """
        Override the save method to calculate the involvement percentage
        based on the number of technicians assigned to the same schedule.
        """
        # Count the number of technicians already assigned to this schedule
        total_technicians = ScheduleTech.objects.filter(
            schedule=self.schedule).count() + 1  # Include the current instance

        # Calculate the involvement percentage
        self.involvement_percentage = 100 // total_technicians

        # Save the instance
        super().save(*args, **kwargs)

        # Update involvement percentage for other technicians
        ScheduleTech.objects.filter(schedule=self.schedule).exclude(id=self.id).update(
            involvement_percentage=100 // total_technicians
        )