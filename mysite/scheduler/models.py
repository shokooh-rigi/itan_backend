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
        help_text="The order associated with this schedule.",
    )
    schedule_start = models.DateTimeField(
        blank=False, null=False, help_text="The start time of the schedule."
    )
    schedule_end = models.DateTimeField(
        blank=False, null=False, help_text="The end time of the schedule."
    )
    pre_demo = models.BooleanField(
        default=False,
        help_text="Indicates whether the schedule is for a pre-demonstration.",
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
        help_text="The order associated with this maintenance activity.",
    )
    assigned_to = models.ForeignKey(
        User,
        blank=True,
        null=True,
        related_name="maintenance_assigned_to",
        on_delete=models.CASCADE,
        help_text="The user assigned to this maintenance task.",
    )
    schedule_start = models.DateTimeField(
        blank=False, null=False, help_text="The start time of the maintenance schedule."
    )
    schedule_end = models.DateTimeField(
        blank=False, null=False, help_text="The end time of the maintenance schedule."
    )
    description = models.TextField(
        max_length=500,
        blank=True,
        help_text="A brief description of the maintenance task.",
    )
    MAINTENANCE_TYPE_CHOICES = (
        (1, "Maintenance"),
        (2, "Lost Time"),
        (3, "Off/Vacation"),
    )
    maintenance_type = models.PositiveSmallIntegerField(
        choices=MAINTENANCE_TYPE_CHOICES,
        default=1,
        help_text="The type of maintenance task.",
    )
    settlement = models.BooleanField(
        default=False, help_text="Indicates whether the task has been settled."
    )
    tech_upload = models.FileField(
        upload_to="uploads/techfiles",
        blank=True,
        null=True,
        help_text="File upload related to the maintenance task.",
    )
    note = models.TextField(
        max_length=1000,
        blank=True,
        null=True,
        help_text="Additional notes related to the maintenance task.",
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
        help_text="The schedule associated with this technician.",
    )
    assigned_to = models.ForeignKey(
        User,
        blank=False,
        null=False,
        related_name="assigned_to",
        on_delete=models.CASCADE,
        help_text="User assigned to this schedule.",
    )
    involvement_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(100), MinValueValidator(0)],
        help_text="The percentage of involvement of the technician.",
    )
    settlement = models.BooleanField(
        default=False, help_text="Indicates whether the task has been settled."
    )
    tech_upload = models.FileField(
        upload_to="uploads/techfiles",
        blank=True,
        null=True,
        help_text="File upload related to the technician's task.",
    )
    note = models.TextField(
        max_length=1000,
        blank=True,
        null=True,
        help_text="Additional notes related to the technician's task.",
    )

    class Meta:
        ordering = ["-created_on"]
        verbose_name = "Schedule Technician"
        verbose_name_plural = "Schedule Technicians"
        unique_together = ["schedule", "assigned_to"]

    def __str__(self):
        return (
            str(self.assigned_to)
            + " assigned to #"
            + str(self.schedule.order.project_number)
        )

    def get_techs(self):
        """
        Retrieve profiles of users with user_type as TECH or SUPER_TECH.
        """

        return Profile.objects.filter(
            Q(user_type=UserTypeChoices.TECH) | Q(user_type=UserTypeChoices.SUPER_TECH)
        )

    def save(self, *args, **kwargs):
        """
        Override the save method to calculate the involvement percentage
        based on the number of unique technicians (employees or contractors)
        assigned to the same schedule.
        """
        # get users assigned_to this schedule
        all_technicians = (
            ScheduleTech.objects.filter(schedule=self.schedule)
            .values("assigned_to")
            .distinct()
        )

        # Include the current instance's assigned_to if it's not already in the list
        all_technicians = list(all_technicians)
        all_technicians.append({"assigned_to": self.assigned_to.id})

        # Avoid division by zero
        if len(all_technicians) > 0:
            self.involvement_percentage = 100 // len(all_technicians)
        else:
            self.involvement_percentage = 0

        # Save the instance
        super().save(*args, **kwargs)

        # Update involvement percentage for technicians
        ScheduleTech.objects.filter(schedule=self.schedule).exclude(id=self.id).update(
            involvement_percentage=100 // len(all_technicians)
        )
