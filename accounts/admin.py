from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User

from .models import Profile, Notification


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    fk_name = 'user'


class ExtendedUserAdmin(DjangoUserAdmin):
    inlines = [ProfileInline]


admin.site.unregister(User)
admin.site.register(User, ExtendedUserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone', 'institution', 'department')
    list_filter = ('role', 'department')
    search_fields = ('user__username', 'user__email', 'phone', 'institution')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'message')
