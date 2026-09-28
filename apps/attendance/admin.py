from django.contrib import admin

from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ["user", "date", "shift_start", "shift_end", "worked_display", "status"]
    list_filter = ["date"]
    search_fields = ["user__username", "user__first_name", "user__last_name"]
    # Managers can fix a forgotten End Shift from here.
