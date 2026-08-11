from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView

from accounts.models import Profile, Notification
from accounts.validators import indian_mobile_validator
from conferences.models import Conference, Department
from submissions.models import Submission
from registrations.models import Registration
from payments.models import Payment


class SignUpForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    role = forms.ChoiceField(
        choices=[(Profile.Role.AUTHOR, 'Author / Participant'), (Profile.Role.COORDINATOR, 'Department Coordinator')],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    phone = forms.CharField(
        max_length=10, required=False, validators=[indian_mobile_validator],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '9876543210', 'maxlength': '10'}),
    )
    institution = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('password2'):
            raise forms.ValidationError('Passwords do not match.')
        if User.objects.filter(username=cleaned.get('username')).exists():
            raise forms.ValidationError('Username already taken.')
        return cleaned


def register_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data.get('first_name', ''),
                last_name=form.cleaned_data.get('last_name', ''),
            )
            profile = user.profile
            profile.role = form.cleaned_data['role']
            profile.phone = form.cleaned_data.get('phone', '')
            profile.institution = form.cleaned_data.get('institution', '')
            profile.department = form.cleaned_data.get('department')
            profile.save()
            messages.success(request, 'Account created. Please log in.')
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'register.html', {'form': form, 'departments': Department.objects.all()})


def custom_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect(redirect_dashboard(user))
        messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')


def home_view(request):
    from datetime import date
    conferences = Conference.objects.filter(is_published=True)
    today = date.today()
    upcoming = [c for c in conferences if c.status == Conference.Status.UPCOMING][:3]
    current = [c for c in conferences if c.status == Conference.Status.CURRENT][:3]
    ctx = {
        'stats': {
            'total_conferences': conferences.count(),
            'upcoming': sum(1 for c in conferences if c.status == Conference.Status.UPCOMING),
            'authors': User.objects.filter(profile__role=Profile.Role.AUTHOR).count(),
            'submissions': Submission.objects.count(),
        },
        'upcoming': upcoming,
        'current': current,
        'departments': Department.objects.all()[:8],
    }
    return render(request, 'home.html', ctx)


def redirect_dashboard(user):
    role = getattr(getattr(user, 'profile', None), 'role', None)
    if user.is_superuser or role == Profile.Role.ADMIN:
        return '/dashboard/admin/'
    if role == Profile.Role.COORDINATOR:
        return '/dashboard/coordinator/'
    return '/dashboard/author/'


@login_required
def role_redirect_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('/')


@login_required
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        if phone:
            try:
                indian_mobile_validator(phone)
            except forms.ValidationError as exc:
                messages.error(request, exc.message)
                return redirect('profile')
        profile.phone = phone
        profile.institution = request.POST.get('institution', '')
        dept_id = request.POST.get('department')
        if dept_id:
            profile.department_id = dept_id
        profile.save()
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')
    return render(request, 'accounts/profile.html', {'profile': profile, 'departments': Department.objects.all()})


@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully.')
            return redirect('profile')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
def notifications_view(request):
    notes = Notification.objects.filter(user=request.user)
    if request.method == 'POST' and request.POST.get('mark_read'):
        notes.filter(is_read=False).update(is_read=True)
        messages.success(request, 'All notifications marked as read.')
        return redirect('notifications')
    return render(request, 'accounts/notifications.html', {'notifications': notes})


# ---- Dashboards ----

@login_required
def dashboard_redirect(request):
    return redirect(redirect_dashboard(request.user))


@login_required
def admin_dashboard(request):
    if not (request.user.is_superuser or request.user.profile.role == Profile.Role.ADMIN):
        messages.error(request, 'Access denied.')
        return redirect('dashboard_redirect')
    ctx = _admin_dashboard_context()
    return render(request, 'dashboard/admin.html', ctx)


@login_required
def coordinator_dashboard(request):
    if request.user.profile.role != Profile.Role.COORDINATOR:
        messages.error(request, 'Access denied.')
        return redirect('dashboard_redirect')
    dept = request.user.profile.department
    conferences = Conference.objects.filter(department=dept) if dept else Conference.objects.none()
    ctx = {
        'total_conferences': conferences.count(),
        'upcoming': sum(1 for c in conferences if c.status == Conference.Status.UPCOMING),
        'current': sum(1 for c in conferences if c.status == Conference.Status.CURRENT),
        'past': sum(1 for c in conferences if c.status == Conference.Status.PAST),
        'submissions': Submission.objects.filter(conference__in=conferences).count(),
        'accepted': Submission.objects.filter(conference__in=conferences, status=Submission.Status.ACCEPTED).count(),
        'registrations': Registration.objects.filter(conference__in=conferences).count(),
        'department': dept,
        'recent_submissions': Submission.objects.filter(conference__in=conferences)[:5],
    }
    return render(request, 'dashboard/coordinator.html', ctx)


@login_required
def author_dashboard(request):
    if request.user.profile.role != Profile.Role.AUTHOR:
        messages.error(request, 'Access denied.')
        return redirect('dashboard_redirect')
    my_regs = Registration.objects.filter(user=request.user)
    my_subs = Submission.objects.filter(author=request.user)
    ctx = {
        'total_conferences': Conference.objects.count(),
        'my_registrations': my_regs.count(),
        'my_submissions': my_subs.count(),
        'accepted_papers': my_subs.filter(status=Submission.Status.ACCEPTED).count(),
        'recent_submissions': my_subs[:5],
        'my_registrations_list': my_regs[:5],
    }
    return render(request, 'dashboard/author.html', ctx)


def _admin_dashboard_context():
    conferences = Conference.objects.all()
    subs = Submission.objects.all()
    regs = Registration.objects.all()
    total_revenue = sum(float(p.amount) for p in Payment.objects.filter(status=Payment.PaymentStatus.PAID))
    status_counts = {}
    for s in Submission.Status.values:
        status_counts[s] = subs.filter(status=s).count()
    ctx = {
        'total_conferences': conferences.count(),
        'upcoming': sum(1 for c in conferences if c.status == Conference.Status.UPCOMING),
        'current': sum(1 for c in conferences if c.status == Conference.Status.CURRENT),
        'past': sum(1 for c in conferences if c.status == Conference.Status.PAST),
        'total_authors': User.objects.filter(profile__role=Profile.Role.AUTHOR).count(),
        'total_submissions': subs.count(),
        'accepted_papers': subs.filter(status=Submission.Status.ACCEPTED).count(),
        'total_registrations': regs.count(),
        'total_revenue': total_revenue,
        'departments': Department.objects.all(),
        'recent_submissions': subs[:6],
    }
    ctx.update({
        'status_submitted': status_counts.get('SUBMITTED', 0),
        'status_under_review': status_counts.get('UNDER_REVIEW', 0),
        'status_accepted': status_counts.get('ACCEPTED', 0),
        'status_rejected': status_counts.get('REJECTED', 0),
        'status_revision_required': status_counts.get('REVISION_REQUIRED', 0),
        'status_camera_ready': status_counts.get('CAMERA_READY', 0),
    })
    return ctx

