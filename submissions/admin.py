from django.contrib import admin

from .models import Submission


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('abstract_id', 'title', 'author', 'conference', 'presentation_type', 'status', 'submitted_at')
    list_filter = ('status', 'presentation_type', 'conference', 'submitted_at')
    search_fields = ('abstract_id', 'title', 'author__username', 'keywords')
    date_hierarchy = 'submitted_at'
