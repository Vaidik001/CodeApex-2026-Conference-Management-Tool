from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'registration', 'amount', 'status', 'paid_at', 'created_at')
    list_filter = ('status', 'created_at', 'paid_at')
    search_fields = ('transaction_id', 'registration__registration_id')
    date_hierarchy = 'created_at'
