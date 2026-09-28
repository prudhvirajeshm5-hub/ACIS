from django.contrib import admin

from .models import Conversation


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ["__str__", "kind", "created_at"]
    list_filter = ["kind"]
