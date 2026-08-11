from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect

from accounts.models import Profile, Notification
from .models import Department, Conference, ConferenceMaterial


def _can_manage(request):
    return request.user.is_authenticated and (
        request.user.is_superuser or request.user.profile.role in (Profile.Role.ADMIN, Profile.Role.COORDINATOR)
    )


def materials_list(request):
    qs = ConferenceMaterial.objects.select_related('conference', 'conference__department').all()
    conf = request.GET.get('conference', '')
    mtype = request.GET.get('type', '')
    q = request.GET.get('q', '').strip()
    if conf:
        qs = qs.filter(conference_id=conf)
    if mtype:
        qs = qs.filter(material_type=mtype)
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(conference__title__icontains=q))
    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'conferences/materials_list.html', {
        'page_obj': page_obj,
        'conferences': Conference.objects.all(),
        'material_types': ConferenceMaterial.MaterialType.choices,
        'conf': conf, 'mtype': mtype, 'q': q,
    })


def conference_list(request):
    qs = Conference.objects.filter(is_published=True)
    q = request.GET.get('q', '').strip()
    dept = request.GET.get('department', '')
    status = request.GET.get('status', '')
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')

    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(venue__icontains=q) | Q(organizer__icontains=q))
    if dept:
        qs = qs.filter(department_id=dept)
    if status:
        today = date.today()
        if status == Conference.Status.UPCOMING:
            qs = qs.filter(start_date__gt=today)
        elif status == Conference.Status.CURRENT:
            qs = qs.filter(start_date__lte=today, end_date__gte=today)
        elif status == Conference.Status.PAST:
            qs = qs.filter(end_date__lt=today)
    if from_date:
        qs = qs.filter(start_date__gte=from_date)
    if to_date:
        qs = qs.filter(start_date__lte=to_date)

    paginator = Paginator(qs, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'conferences/conference_list.html', {
        'page_obj': page_obj,
        'departments': Department.objects.all(),
        'q': q, 'dept': dept, 'status': status, 'from_date': from_date, 'to_date': to_date,
    })


def conference_detail(request, pk):
    conference = get_object_or_404(Conference, pk=pk)
    is_registered = False
    if request.user.is_authenticated:
        from registrations.models import Registration
        is_registered = Registration.objects.filter(user=request.user, conference=conference).exists()
    return render(request, 'conferences/conference_detail.html', {
        'conference': conference,
        'materials': conference.materials.all(),
        'is_registered': is_registered,
        'can_manage': _can_manage(request),
    })


@login_required
def conference_create(request):
    if not _can_manage(request):
        messages.error(request, 'Access denied.')
        return redirect('conference_list')
    if request.method == 'POST':
        conf = _save_conference_from_post(request, None)
        messages.success(request, 'Conference created successfully.')
        return redirect('conference_detail', pk=conf.pk)
    return render(request, 'conferences/conference_form.html', {
        'departments': Department.objects.all(),
        'form_title': 'Create Conference',
    })


@login_required
def conference_update(request, pk):
    if not _can_manage(request):
        messages.error(request, 'Access denied.')
        return redirect('conference_list')
    conference = get_object_or_404(Conference, pk=pk)
    if request.method == 'POST':
        _save_conference_from_post(request, conference)
        messages.success(request, 'Conference updated successfully.')
        return redirect('conference_detail', pk=conference.pk)
    return render(request, 'conferences/conference_form.html', {
        'conference': conference,
        'departments': Department.objects.all(),
        'form_title': 'Edit Conference',
    })


def _save_conference_from_post(request, conference):
    data = request.POST
    if conference is None:
        conference = Conference()
    conference.title = data.get('title', '')
    conference.description = data.get('description', '')
    conference.department_id = data.get('department') or None
    conference.start_date = data.get('start_date') or date.today()
    conference.end_date = data.get('end_date') or date.today()
    conference.venue = data.get('venue', '')
    conference.organizer = data.get('organizer', '')
    conference.contact_email = data.get('contact_email', '')
    conference.contact_phone = data.get('contact_phone', '')
    conference.registration_deadline = data.get('registration_deadline') or None
    conference.abstract_deadline = data.get('abstract_deadline') or None
    conference.paper_deadline = data.get('paper_deadline') or None
    conference.registration_fee = data.get('registration_fee', 0) or 0
    conference.is_published = bool(data.get('is_published'))
    if request.FILES.get('banner'):
        conference.banner = request.FILES['banner']
    conference.save()
    return conference


@login_required
def conference_delete(request, pk):
    if not _can_manage(request):
        messages.error(request, 'Access denied.')
        return redirect('conference_list')
    conference = get_object_or_404(Conference, pk=pk)
    if request.method == 'POST':
        conference.delete()
        messages.success(request, 'Conference deleted.')
        return redirect('conference_list')
    return render(request, 'conferences/conference_confirm_delete.html', {'conference': conference})


@login_required
def material_upload(request, pk):
    if not _can_manage(request):
        messages.error(request, 'Access denied.')
        return redirect('conference_detail', pk=pk)
    conference = get_object_or_404(Conference, pk=pk)
    if request.method == 'POST':
        ConferenceMaterial.objects.create(
            conference=conference,
            title=request.POST.get('title', ''),
            material_type=request.POST.get('material_type', ConferenceMaterial.MaterialType.BROCHURE),
            file=request.FILES.get('file'),
            uploaded_by=request.user,
        )
        messages.success(request, 'Material uploaded.')
    return redirect('conference_detail', pk=pk)


@login_required
def material_download(request, pk):
    material = get_object_or_404(ConferenceMaterial, pk=pk)
    if not material.file:
        raise Http404('File not found')
    try:
        with open(material.file.path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{material.file.name.split("/")[-1]}"'
            return response
    except FileNotFoundError:
        raise Http404('File not found')


@login_required
def material_delete(request, pk):
    if not _can_manage(request):
        messages.error(request, 'Access denied.')
        return redirect('conference_list')
    material = get_object_or_404(ConferenceMaterial, pk=pk)
    conf_pk = material.conference.pk
    if request.method == 'POST':
        material.file.delete(save=False)
        material.delete()
        messages.success(request, 'Material deleted.')
    return redirect('conference_detail', pk=conf_pk)


# ---- Departments ----

def department_list(request):
    departments = Department.objects.all()
    return render(request, 'conferences/department_list.html', {'departments': departments})


def department_detail(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    confs = dept.conferences.filter(is_published=True)
    today = date.today()
    return render(request, 'conferences/department_detail.html', {
        'department': dept,
        'upcoming': confs.filter(start_date__gt=today),
        'current': confs.filter(start_date__lte=today, end_date__gte=today),
        'past': confs.filter(end_date__lt=today),
    })


@login_required
def department_create(request):
    if not _can_manage(request):
        messages.error(request, 'Access denied.')
        return redirect('department_list')
    if request.method == 'POST':
        Department.objects.create(
            name=request.POST.get('name', ''),
            description=request.POST.get('description', ''),
            coordinator_id=request.POST.get('coordinator') or None,
        )
        messages.success(request, 'Department created.')
        return redirect('department_list')
    from django.contrib.auth.models import User
    coordinators = User.objects.filter(profile__role=Profile.Role.COORDINATOR)
    return render(request, 'conferences/department_form.html', {
        'coordinators': coordinators,
        'form_title': 'Create Department',
    })


@login_required
def department_update(request, pk):
    if not _can_manage(request):
        messages.error(request, 'Access denied.')
        return redirect('department_list')
    dept = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        dept.name = request.POST.get('name', dept.name)
        dept.description = request.POST.get('description', dept.description)
        dept.coordinator_id = request.POST.get('coordinator') or None
        dept.save()
        messages.success(request, 'Department updated.')
        return redirect('department_detail', pk=dept.pk)
    from django.contrib.auth.models import User
    coordinators = User.objects.filter(profile__role=Profile.Role.COORDINATOR)
    return render(request, 'conferences/department_form.html', {
        'department': dept,
        'coordinators': coordinators,
        'form_title': 'Edit Department',
    })
