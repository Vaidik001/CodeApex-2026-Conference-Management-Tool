from django.contrib import admin

from .models import Department, Conference, ConferenceMaterial


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'coordinator', 'conference_count_display', 'created_at')
    search_fields = ('name',)
    list_filter = ('coordinator',)

    def conference_count_display(self, obj):
        return obj.conferences.count()
    conference_count_display.short_description = 'Conferences'


@admin.register(Conference)
class ConferenceAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'department', 'start_date', 'end_date', 'venue', 'registration_fee', 'is_published', 'status_display')
    list_filter = ('department', 'is_published', 'start_date')
    search_fields = ('title', 'code', 'venue', 'organizer')
    readonly_fields = ('code',)
    filter_horizontal = ()
    date_hierarchy = 'start_date'

    def status_display(self, obj):
        return obj.status
    status_display.short_description = 'Status'


@admin.register(ConferenceMaterial)
class ConferenceMaterialAdmin(admin.ModelAdmin):
    list_display = ('conference', 'title', 'material_type', 'uploaded_by', 'uploaded_at')
    list_filter = ('material_type', 'uploaded_at')
    search_fields = ('title', 'conference__title')
