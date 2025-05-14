from django.contrib import admin
from .models import Schedule, Maintenance, ScheduleTech


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Schedule model.
    """

    list_display = (
        "id",
        "order",
        "schedule_start",
        "schedule_end",
        "pre_demo",
        "created_by",
        "created_on",
    )
    search_fields = ("order__project_number", "created_by__username")
    list_filter = ("pre_demo", "created_on")
    ordering = ("-created_on",)
    readonly_fields = (
        "created_on",
        "updated_at",
        "id",
    )


@admin.register(Maintenance)
class MaintenanceAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Maintenance model.
    """

    list_display = (
        "id",
        "order",
        "assigned_to",
        "schedule_start",
        "schedule_end",
        "maintenance_type",
        "settlement",
        "created_by",
        "created_on",
    )
    search_fields = ("order__project_number", "assigned_to__username")
    list_filter = ("maintenance_type", "settlement", "created_on")
    ordering = ("-created_on",)
    readonly_fields = (
        "created_on",
        "updated_at",
        "id",
    )


@admin.register(ScheduleTech)
class ScheduleTechAdmin(admin.ModelAdmin):
    """
    Admin configuration for the ScheduleTech model.
    """

    list_display = (
        "id",
        "schedule",
        "schedule_id",
        "assigned_to",
        "involvement_percentage",
        "settlement",
        "created_on",
    )
    search_fields = ("schedule__order__project_number", "assigned_to__username")
    list_filter = ("settlement", "created_on")
    ordering = ("-created_on",)
    readonly_fields = (
        "created_on",
        "updated_at",
        "id",
    )
