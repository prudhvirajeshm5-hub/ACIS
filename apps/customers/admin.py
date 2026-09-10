from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["name", "mobile", "email", "district", "created_at"]
    search_fields = ["name", "mobile", "email"]
    list_filter = ["district"]
    autocomplete_fields = ["state", "district", "city"]
