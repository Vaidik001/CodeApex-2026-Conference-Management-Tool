from django.db import models
from django.utils import timezone


def current_year():
    return timezone.now().year


class Payment(models.Model):
    class PaymentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PAID = 'PAID', 'Paid'
        FAILED = 'FAILED', 'Failed'

    transaction_id = models.CharField(max_length=20, unique=True, blank=True)
    registration = models.ForeignKey(
        'registrations.Registration',
        on_delete=models.CASCADE,
        related_name='payments',
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.transaction_id} - {self.amount} - {self.status}'

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            year = current_year()
            prefix = f'TXN-{year}-'
            last = Payment.objects.filter(transaction_id__startswith=prefix).order_by('-transaction_id').first()
            if last:
                try:
                    num = int(last.transaction_id.split('-')[-1]) + 1
                except ValueError:
                    num = 1
            else:
                num = 1
            self.transaction_id = f'{prefix}{num:06d}'
        super().save(*args, **kwargs)

    @property
    def status_badge_class(self):
        if self.status == self.PaymentStatus.PAID:
            return 'bg-success'
        if self.status == self.PaymentStatus.FAILED:
            return 'bg-danger'
        return 'bg-warning text-dark'
