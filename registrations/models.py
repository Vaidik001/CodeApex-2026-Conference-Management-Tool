from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


def current_year():
    return timezone.now().year


class Registration(models.Model):
    class ParticipantType(models.TextChoices):
        AUTHOR = 'AUTHOR', 'Author'
        STUDENT = 'STUDENT', 'Student'
        FACULTY = 'FACULTY', 'Faculty'
        PARTICIPANT = 'PARTICIPANT', 'Participant'

    class PaymentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PAID = 'PAID', 'Paid'
        FAILED = 'FAILED', 'Failed'

    registration_id = models.CharField(max_length=20, unique=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registrations')
    conference = models.ForeignKey(
        'conferences.Conference',
        on_delete=models.CASCADE,
        related_name='registrations',
    )
    participant_type = models.CharField(
        max_length=15, choices=ParticipantType.choices, default=ParticipantType.AUTHOR
    )
    phone = models.CharField(max_length=20, blank=True)
    institution = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(
        max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.PENDING
    )
    registration_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-registration_date']
        unique_together = ('user', 'conference')

    def __str__(self):
        return f'{self.registration_id} - {self.user.username} - {self.conference.title}'

    def save(self, *args, **kwargs):
        if not self.registration_id:
            year = current_year()
            prefix = f'REG-{year}-'
            last = Registration.objects.filter(registration_id__startswith=prefix).order_by('-registration_id').first()
            if last:
                try:
                    num = int(last.registration_id.split('-')[-1]) + 1
                except ValueError:
                    num = 1
            else:
                num = 1
            self.registration_id = f'{prefix}{num:05d}'
        super().save(*args, **kwargs)
