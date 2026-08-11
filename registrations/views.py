from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect

from accounts.models import Profile, Notification
from accounts.validators import indian_mobile_validator
from conferences.models import Conference
from .models import Registration


class RegistrationForm(forms.Form):
    conference = forms.ModelChoiceField(queryset=Conference.objects.filter(is_published=True), widget=forms.Select(attrs={'class': 'form-select'}))
    participant_type = forms.ChoiceField(choices=Registration.ParticipantType.choices, widget=forms.Select(attrs={'class': 'form-select'}))
    phone = forms.CharField(
        max_length=10, required=False, validators=[indian_mobile_validator],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '9876543210', 'maxlength': '10'}),
    )
    institution = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    city = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Ahmedabad'}))
    state = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Gujarat'}))


def _can_manage(request):
    return request.user.is_authenticated and (
        request.user.is_superuser or request.user.profile.role in (Profile.Role.ADMIN, Profile.Role.COORDINATOR)
    )


@login_required
def my_registrations(request):
    qs = Registration.objects.filter(user=request.user)
    return render(request, 'registrations/my_registrations.html', {'registrations': qs})


@login_required
def registration_create(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            conference = form.cleaned_data['conference']
            if Registration.objects.filter(user=request.user, conference=conference).exists():
                messages.error(request, 'You are already registered for this conference.')
                return redirect('my_registrations')
            reg = Registration.objects.create(
                user=request.user,
                conference=conference,
                participant_type=form.cleaned_data['participant_type'],
                phone=form.cleaned_data.get('phone', ''),
                institution=form.cleaned_data.get('institution', ''),
                city=form.cleaned_data.get('city', ''),
                state=form.cleaned_data.get('state', ''),
                registration_fee=conference.registration_fee,
            )
            Notification.objects.create(user=request.user, message=f'Registration {reg.registration_id} confirmed for {conference.title}. Pending payment.')
            messages.success(request, f'Registration created. ID: {reg.registration_id}. Please complete payment.')
            return redirect('payment_create', reg_id=reg.pk)
    else:
        pre_conf = request.GET.get('conference')
        initial = {}
        if pre_conf:
            initial['conference'] = pre_conf
        form = RegistrationForm(initial=initial)
    return render(request, 'registrations/registration_form.html', {'form': form})


@login_required
def all_registrations(request):
    if not _can_manage(request):
        messages.error(request, 'Access denied.')
        return redirect('dashboard_redirect')
    qs = Registration.objects.all()
    conf = request.GET.get('conference', '')
    status = request.GET.get('status', '')
    if conf: qs = qs.filter(conference_id=conf)
    if status: qs = qs.filter(payment_status=status)
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'registrations/all_registrations.html', {
        'page_obj': page_obj,
        'conferences': Conference.objects.all(),
        'conf': conf, 'status': status,
        'status_choices': Registration.PaymentStatus.choices,
    })
