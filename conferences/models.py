from datetime import date

from django.contrib.auth.models import User
from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    coordinator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='coordinated_departments',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def conference_count(self):
        return self.conferences.count()


class Conference(models.Model):
    class Status(models.TextChoices):
        PAST = 'PAST', 'Past'
        CURRENT = 'CURRENT', 'Current'
        UPCOMING = 'UPCOMING', 'Upcoming'

    title = models.CharField(max_length=300)
    code = models.CharField(max_length=30, unique=True, blank=True, help_text='Auto-generated conference code, e.g. CMT-2026-CSE-001')
    description = models.TextField()
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conferences',
    )
    start_date = models.DateField()
    end_date = models.DateField()
    venue = models.CharField(max_length=300)
    organizer = models.CharField(max_length=200, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    registration_deadline = models.DateField(null=True, blank=True)
    abstract_deadline = models.DateField(null=True, blank=True)
    paper_deadline = models.DateField(null=True, blank=True)
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    banner = models.ImageField(upload_to='banners/', blank=True, null=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.code:
            year = self.start_date.year if self.start_date else date.today().year
            dept_code = ''.join(w[0] for w in (self.department.name.split() if self.department else ['G', 'E', 'N']))[:4].upper() or 'GEN'
            prefix = f'CMT-{year}-{dept_code}-'
            last = Conference.objects.filter(code__startswith=prefix).order_by('-code').first()
            if last:
                try:
                    num = int(last.code.split('-')[-1]) + 1
                except ValueError:
                    num = 1
            else:
                num = 1
            self.code = f'{prefix}{num:03d}'
        super().save(*args, **kwargs)

    @property
    def status(self):
        today = date.today()
        if today < self.start_date:
            return self.Status.UPCOMING
        if today > self.end_date:
            return self.Status.PAST
        return self.Status.CURRENT

    @property
    def status_badge_class(self):
        s = self.status
        if s == self.Status.UPCOMING:
            return 'bg-primary'
        if s == self.Status.CURRENT:
            return 'bg-success'
        return 'bg-secondary'


class ConferenceMaterial(models.Model):
    class MaterialType(models.TextChoices):
        BROCHURE = 'BROCHURE', 'Brochure'
        FLYER = 'FLYER', 'Flyer'
        CALL_FOR_PAPERS = 'CALL_FOR_PAPERS', 'Call for Papers'
        SCHEDULE = 'SCHEDULE', 'Schedule'
        GUIDELINES = 'GUIDELINES', 'Guidelines'

    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=200)
    material_type = models.CharField(max_length=30, choices=MaterialType.choices)
    file = models.FileField(upload_to='materials/')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f'{self.conference.title} - {self.title}'
