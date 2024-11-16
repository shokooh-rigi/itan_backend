import datetime

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from custom_user.models import User
from mysite.bidfilemgm.models import BidFile
from .enums import ControlSystemChoices, HoursChoices
from mysite.core.base_model import BaseModel
from mysite.core.models import Person, Project, Service
from mysite.equipments.models import Equipment


def estimate_number_generator(estimate_id: int):
    """
    Generates a unique estimate number based on the user ID, date created, and estimate ID.

    Args:
        estimate_id (int): The ID of the estimate.

    Returns:
        str: The generated estimate number.
    """
    estimate = Estimate.objects.get(id=estimate_id)
    estimator_long_id = estimate.created_by.id + 100
    estimate_date_created = str(estimate.created_on).replace('-', '')[2:8]
    return estimate_date_created + str(estimator_long_id) + str(estimate.id).zfill(3)


class Estimate(BaseModel):
    """Model representing an estimate."""

    bfm = models.OneToOneField(
        BidFile,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    customer = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        blank=False,
        null=True,
        related_name='cu_person',
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        blank=False,
        null=True,
    )
    engineer = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        blank=False,
        null=True,
        related_name='en_person',
    )
    service = models.ManyToManyField(
        Service,
        related_name='estimates',
        blank=False,
    )
    due_date = models.DateField(
        default=datetime.datetime.now().strftime("%m/%d/%Y"),
        blank=False,
        null=True,
    )
    drawing_date = models.DateField(blank=True, null=True)
    confirm_date = models.DateTimeField(blank=True, null=True)
    note = models.TextField(max_length=255, blank=True, null=True)
    flag = models.BooleanField(default=True)

    class Meta:
        ordering = ["-due_date"]
        verbose_name = 'Estimate List'
        verbose_name_plural = 'Estimate Lists'

    def __str__(self):
        return estimate_number_generator(self.id)


class EstimateHistory(models.Model):
    """Model for tracking history of an estimate."""

    estimate = models.ForeignKey(
        Estimate,
        on_delete=models.CASCADE,
        blank=False,
    )
    # todo : import it : MinValueValidator
    total = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        blank=False,
        null=False,
    )
    version = models.IntegerField(blank=False, null=False)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_on"]
        verbose_name = 'Estimate History'
        verbose_name_plural = 'Estimate Histories'

    def __str__(self):
        return str(self.estimate) + ': History ' + str(self.version)


class EstimateEquipment(models.Model):
    """Model representing equipment used in an estimate."""

    estimate = models.ForeignKey(
        Estimate,
        on_delete=models.CASCADE,
        blank=False,
        null=True,
    )
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        blank=False,
    )
    price_override = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
    )
    quantity = models.FloatField(blank=False)
    created_on = models.DateTimeField(auto_now_add=True)
    # if flag is True means it counts in estimate price (its service is in the estimate services)
    # todo: ENHANCEMENT: differentiate between Quantity (integer) and Number of Days (float) (flag)
    flag = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False, help_text="Soft delete flag.")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Estimated Equipment List'
        verbose_name_plural = 'Estimated Equipment Lists'

    def __str__(self):
        return estimate_number_generator(self.estimate.id) + " " + self.equipment.name

    def soft_delete(self):
        """Marks the record as deleted without actually removing it from the database."""
        self.is_deleted = True
        self.save(update_fields=['is_deleted', 'updated_at'])


class EstimateDetails(models.Model):
    """Model for additional details of an estimate."""

    estimate = models.OneToOneField(
        Estimate,
        on_delete=models.CASCADE,
    )
    control_system = models.PositiveSmallIntegerField(
        choices=[(choice.value[0], choice.value[1]) for choice in ControlSystemChoices],
        default=ControlSystemChoices.ZERO.value[0],
    )

    hours = models.PositiveSmallIntegerField(
        choices=[(choice.value[0], choice.value[1]) for choice in HoursChoices],
        default=HoursChoices.REGULAR_HOURS.value[0],
    )
    customer_adjustment = models.DecimalField(
        default=0,
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
    )
    adjustment = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
    )
    pre_demo = models.FloatField(default=0)
    remark = models.TextField(max_length=500, blank=True)
    validity = models.IntegerField(blank=False, default=30)
    saved_flag = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    flag = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Estimated Additional info'
        verbose_name_plural = 'Estimated Additional infos'

    def __str__(self):
        return estimate_number_generator(self.estimate.id)


@receiver(post_save, sender=Estimate)
def create_estimate_details(sender, instance, created, **kwargs):
    """
    Signal to automatically create EstimateDetails when a new Estimate is created.
    """
    if created:
        EstimateDetails.objects.create(estimate=instance)
