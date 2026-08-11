from django.contrib import admin

from .models import Registration


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('registration_id', 'user', 'conference', 'participant_type', 'registration_fee', 'payment_status', 'registration_date')
    list_filter = ('payment_status', 'participant_type', 'conference', 'registration_date')
    search_fields = ('registration_id', 'user__username', 'conference__title', 'institution')
    date_hierarchy = 'registration_date'
