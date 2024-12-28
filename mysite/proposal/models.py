from django.db import models

from mysite.core.base_model import BaseModelWithCreatedByUser
from mysite.estimator.models import Estimate, estimate_number_generator


class Proposal(BaseModelWithCreatedByUser):
    """Model representing a proposal related to an estimate."""

    estimate = models.OneToOneField(
        Estimate,
        on_delete=models.CASCADE,
        blank=False,
    )
    validity = models.IntegerField(blank=False, default=180)
    note = models.TextField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ["-estimate"]
        verbose_name = 'Proposal List'
        verbose_name_plural = 'Proposal Lists'

    def __str__(self):
        return estimate_number_generator(self.estimate.id) + "Proposal"
