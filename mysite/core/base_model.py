from django.conf import settings
from django.db import models
from django.utils.timezone import now


class BaseModel(models.Model):
    """
    Abstract basic model that includes common fields for other models.
    Fields:
        created_at (DateTime): Automatically stores when the record was created.
        updated_at (DateTime): Automatically updates to the current timestamp when the record is modified.
        is_deleted (Boolean): Soft delete flag.
        archive (Boolean): Archive flag.
    """
    created_on = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    archive = models.BooleanField(default=False, help_text="Archive flag.")
    is_deleted = models.BooleanField(default=False, help_text="Soft delete flag.")

    class Meta:
        abstract = True

    def soft_delete(self):
        """Marks the record as deleted without actually removing it from the database."""
        self.is_deleted = True
        self.save(update_fields=['is_deleted', 'updated_at'])

    def archive_record(self):
        """Marks the record as archived."""
        self.archive = True
        self.save(update_fields=['archive', 'updated_at'])

    def unarchive_record(self):
        """Marks the record as unarchived."""
        self.archive = False
        self.save(update_fields=['archive', 'updated_at'])


class BaseModelWithCreatedByUser(BaseModel):
    """
    Abstract base model that includes common fields for other models.
    Fields:
        created_by (ForeignKey): Stores the user who created the record.
    """
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created_by",
        help_text="User who created this record."
    )

    class Meta:
        abstract = True
