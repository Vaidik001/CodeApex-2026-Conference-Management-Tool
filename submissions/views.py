from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect

from accounts.models import Profile, Notification
from conferences.models import Conference
from .models import Submission

ALLOWED_PAPER_EXT = ['.pdf']
ALLOWED_POSTER_EXT = ['.pdf', '.jpg', '.jpeg', '.png']


def _validate_file(file, allowed_ext, label):
    if not file:
        return None, None
    import os
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in allowed_ext:
        return None, f'{label} must be one of {", ".join(allowed_ext)}'
    if file.size > 10 * 1024 * 1024:
        return None, f'{label} must be under 10 MB.'
    return file, None


class SubmissionForm(forms.Form):
    conference = forms.ModelChoiceField(queryset=Conference.objects.filter(is_published=True), widget=forms.Select(attrs={'class': 'form-select'}))
    title = forms.CharField(max_length=300, widget=forms.TextInput(attrs={'class': 'form-control'}))
    abstract_text = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 6}))
    keywords = forms.CharField(max_length=300, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    presentation_type = forms.ChoiceField(choices=Submission.PresentationType.choices, widget=forms.Select(attrs={'class': 'form-select'}))
    paper_file = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    poster_file = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))


@login_required
def my_submissions(request):
    qs = Submission.objects.filter(author=request.user)
    return render(request, 'submissions/my_submissions.html', {'submissions': qs})


@login_required
def submission_create(request):
    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            paper, perr = _validate_file(form.cleaned_data.get('paper_file'), ALLOWED_PAPER_EXT, 'Paper file')
            poster, derr = _validate_file(form.cleaned_data.get('poster_file'), ALLOWED_POSTER_EXT, 'Poster file')
            if perr or derr:
                if perr: messages.error(request, perr)
                if derr: messages.error(request, derr)
            else:
                sub = Submission.objects.create(
                    author=request.user,
                    conference=form.cleaned_data['conference'],
                    title=form.cleaned_data['title'],
                    abstract_text=form.cleaned_data['abstract_text'],
                    keywords=form.cleaned_data.get('keywords', ''),
                    presentation_type=form.cleaned_data['presentation_type'],
                    paper_file=paper,
                    poster_file=poster,
                )
                Notification.objects.create(user=request.user, message=f'Submission {sub.abstract_id} received and is under review.')
                messages.success(request, f'Submission created. Abstract ID: {sub.abstract_id}')
                return redirect('submission_detail', pk=sub.pk)
    else:
        form = SubmissionForm()
    return render(request, 'submissions/submission_form.html', {'form': form, 'form_title': 'New Submission'})


@login_required
def submission_detail(request, pk):
    sub = get_object_or_404(Submission, pk=pk)
    if sub.author != request.user and not _can_review(request):
        messages.error(request, 'Access denied.')
        return redirect('conference_list')
    return render(request, 'submissions/submission_detail.html', {'sub': sub, 'can_review': _can_review(request)})


@login_required
def submission_update(request, pk):
    sub = get_object_or_404(Submission, pk=pk)
    if sub.author != request.user:
        messages.error(request, 'Access denied.')
        return redirect('conference_list')
    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES, initial={'conference': sub.conference})
        if form.is_valid():
            paper, perr = _validate_file(form.cleaned_data.get('paper_file'), ALLOWED_PAPER_EXT, 'Paper file')
            poster, derr = _validate_file(form.cleaned_data.get('poster_file'), ALLOWED_POSTER_EXT, 'Poster file')
            if perr or derr:
                if perr: messages.error(request, perr)
                if derr: messages.error(request, derr)
            else:
                sub.conference = form.cleaned_data['conference']
                sub.title = form.cleaned_data['title']
                sub.abstract_text = form.cleaned_data['abstract_text']
                sub.keywords = form.cleaned_data.get('keywords', '')
                sub.presentation_type = form.cleaned_data['presentation_type']
                if paper: sub.paper_file = paper
                if poster: sub.poster_file = poster
                sub.save()
                messages.success(request, 'Submission updated.')
                return redirect('submission_detail', pk=sub.pk)
    else:
        form = SubmissionForm(initial={
            'conference': sub.conference, 'title': sub.title, 'abstract_text': sub.abstract_text,
            'keywords': sub.keywords, 'presentation_type': sub.presentation_type,
        })
    return render(request, 'submissions/submission_form.html', {'form': form, 'form_title': 'Edit Submission', 'sub': sub})


def _can_review(request):
    return request.user.is_authenticated and (
        request.user.is_superuser or request.user.profile.role in (Profile.Role.ADMIN, Profile.Role.COORDINATOR)
    )


@login_required
def all_submissions(request):
    if not _can_review(request):
        messages.error(request, 'Access denied.')
        return redirect('dashboard_redirect')
    qs = Submission.objects.all()
    q = request.GET.get('q', '').strip()
    conf = request.GET.get('conference', '')
    status = request.GET.get('status', '')
    ptype = request.GET.get('ptype', '')
    if q:
        qs = qs.filter(Q(abstract_id__icontains=q) | Q(title__icontains=q) | Q(author__username__icontains=q))
    if conf: qs = qs.filter(conference_id=conf)
    if status: qs = qs.filter(status=status)
    if ptype: qs = qs.filter(presentation_type=ptype)
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'submissions/all_submissions.html', {
        'page_obj': page_obj,
        'conferences': Conference.objects.all(),
        'q': q, 'conf': conf, 'status': status, 'ptype': ptype,
        'status_choices': Submission.Status.choices,
        'ptype_choices': Submission.PresentationType.choices,
    })


@login_required
def submission_change_status(request, pk):
    if not _can_review(request):
        messages.error(request, 'Access denied.')
        return redirect('dashboard_redirect')
    sub = get_object_or_404(Submission, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        remarks = request.POST.get('remarks', '')
        if new_status in dict(Submission.Status.choices):
            sub.status = new_status
            sub.remarks = remarks
            sub.save()
            Notification.objects.create(
                user=sub.author,
                message=f'Your submission {sub.abstract_id} status is now {sub.get_status_display()}.',
            )
            messages.success(request, 'Submission status updated.')
    return redirect('submission_detail', pk=sub.pk)
