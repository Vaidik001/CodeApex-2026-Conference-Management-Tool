from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


def current_year():
    return timezone.now().year


class SubmissionQuerySet(models.QuerySet):
    def accepted(self):
        return self.filter(status=Submission.Status.ACCEPTED)


class Submission(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = 'SUBMITTED', 'Submitted'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        REJECTED = 'REJECTED', 'Rejected'
        REVISION_REQUIRED = 'REVISION_REQUIRED', 'Revision Required'
        CAMERA_READY = 'CAMERA_READY', 'Camera Ready'

    class PresentationType(models.TextChoices):
        PAPER = 'PAPER', 'Paper'
        POSTER = 'POSTER', 'Poster'

    abstract_id = models.CharField(max_length=20, unique=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    conference = models.ForeignKey(
        'conferences.Conference',
        on_delete=models.CASCADE,
        related_name='submissions',
    )
    title = models.CharField(max_length=300)
    abstract_text = models.TextField()
    keywords = models.CharField(max_length=300, blank=True)
    presentation_type = models.CharField(
        max_length=10, choices=PresentationType.choices, default=PresentationType.PAPER
    )
    paper_file = models.FileField(upload_to='papers/', blank=True, null=True)
    poster_file = models.FileField(upload_to='posters/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    remarks = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = SubmissionQuerySet.as_manager()

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f'{self.abstract_id} - {self.title}'

    @property
    def status_badge_class(self):
        mapping = {
            self.Status.SUBMITTED: 'bg-info text-dark',
            self.Status.UNDER_REVIEW: 'bg-warning text-dark',
            self.Status.ACCEPTED: 'bg-success',
            self.Status.REJECTED: 'bg-danger',
            self.Status.REVISION_REQUIRED: 'bg-warning text-dark',
            self.Status.CAMERA_READY: 'bg-primary',
        }
        return mapping.get(self.status, 'bg-secondary')

    def save(self, *args, **kwargs):
        if not self.abstract_id:
            year = current_year()
            prefix = f'CMT-{year}-'
            last = Submission.objects.filter(abstract_id__startswith=prefix).order_by('-abstract_id').first()
            if last:
                try:
                    num = int(last.abstract_id.split('-')[-1]) + 1
                except ValueError:
                    num = 1
            else:
                num = 1
            self.abstract_id = f'{prefix}{num:05d}'
        super().save(*args, **kwargs)
