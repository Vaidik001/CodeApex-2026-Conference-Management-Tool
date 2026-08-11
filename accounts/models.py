from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        COORDINATOR = 'COORDINATOR', 'Coordinator'
        AUTHOR = 'AUTHOR', 'Author'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.AUTHOR)
    phone = models.CharField(max_length=20, blank=True)
    institution = models.CharField(max_length=200, blank=True)
    department = models.ForeignKey(
        'conferences.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['user__username']

    def __str__(self):
        return f'{self.user.username} ({self.role})'


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=500)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username}: {self.message[:50]}'


def get_user_role(user):
    if not user.is_authenticated:
        return None
    try:
        return user.profile.role
    except Profile.DoesNotExist:
        return None


def is_admin(user):
    return user.is_authenticated and (user.is_superuser or get_user_role(user) == Profile.Role.ADMIN)


def is_coordinator(user):
    return user.is_authenticated and get_user_role(user) == Profile.Role.COORDINATOR


def is_author(user):
    return user.is_authenticated and get_user_role(user) == Profile.Role.AUTHOR
