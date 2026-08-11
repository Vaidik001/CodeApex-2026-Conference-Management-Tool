import csv
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from accounts.models import Profile, User
from conferences.models import Department, Conference
from submissions.models import Submission
from registrations.models import Registration
from payments.models import Payment


def _can_view_reports(request):
    return request.user.is_authenticated and (
        request.user.is_superuser or request.user.profile.role in (Profile.Role.ADMIN, Profile.Role.COORDINATOR)
    )


@login_required
def reports_home(request):
    if not _can_view_reports(request):
        messages.error(request, 'Access denied.')
        return redirect('dashboard_redirect')
    confs = Conference.objects.all()
    subs = Submission.objects.all()
    regs = Registration.objects.all()
    pays = Payment.objects.filter(status=Payment.PaymentStatus.PAID)
    revenue = pays.aggregate(t=Sum('amount'))['t'] or 0

    dept_stats = []
    for d in Department.objects.all():
        cset = d.conferences.all()
        ds = subs.filter(conference__in=cset)
        dept_stats.append({
            'name': d.name,
            'conferences': cset.count(),
            'submissions': ds.count(),
            'accepted': ds.filter(status=Submission.Status.ACCEPTED).count(),
            'rejected': ds.filter(status=Submission.Status.REJECTED).count(),
            'pending': ds.exclude(status__in=[Submission.Status.ACCEPTED, Submission.Status.REJECTED]).count(),
        })

    return render(request, 'reports/reports_home.html', {
        'total_conferences': confs.count(),
        'total_submissions': subs.count(),
        'accepted': subs.filter(status=Submission.Status.ACCEPTED).count(),
        'rejected': subs.filter(status=Submission.Status.REJECTED).count(),
        'pending': subs.exclude(status__in=[Submission.Status.ACCEPTED, Submission.Status.REJECTED]).count(),
        'total_registrations': regs.count(),
        'total_revenue': revenue,
        'dept_stats': dept_stats,
        'status_counts': _status_counts(subs),
        'dept_labels': [d.name for d in Department.objects.all()],
        'dept_counts': [d.conferences.count() for d in Department.objects.all()],
    })


def _status_counts(subs):
    out = {}
    for s in Submission.Status.values:
        out[s] = subs.filter(status=s).count()
    return out


def _csv_response(filename, header, rows):
    resp = HttpResponse(content_type='text/csv')
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.writer(resp)
    writer.writerow(header)
    for r in rows:
        writer.writerow(r)
    return resp


@login_required
def conference_report_csv(request):
    if not _can_view_reports(request):
        return HttpResponse('Forbidden', status=403)
    rows = []
    for c in Conference.objects.all():
        rows.append([c.title, c.department.name if c.department else '', c.start_date, c.end_date,
                     c.venue, c.organizer, c.status, float(c.registration_fee),
                     c.registrations.count(), c.submissions.count()])
    return _csv_response('conference_report.csv',
                         ['Title', 'Department', 'Start', 'End', 'Venue', 'Organizer', 'Status', 'Fee', 'Registrations', 'Submissions'],
                         rows)


@login_required
def submission_report_csv(request):
    if not _can_view_reports(request):
        return HttpResponse('Forbidden', status=403)
    rows = []
    for s in Submission.objects.all():
        rows.append([s.abstract_id, s.title, s.author.username, s.conference.title,
                     s.get_presentation_type_display(), s.get_status_display(),
                     s.submitted_at.strftime('%Y-%m-%d'), s.remarks])
    return _csv_response('submission_report.csv',
                         ['Abstract ID', 'Title', 'Author', 'Conference', 'Type', 'Status', 'Submitted', 'Remarks'],
                         rows)


@login_required
def registration_report_csv(request):
    if not _can_view_reports(request):
        return HttpResponse('Forbidden', status=403)
    rows = []
    for r in Registration.objects.all():
        rows.append([r.registration_id, r.user.username, r.user.email, r.conference.title,
                     r.get_participant_type_display(), float(r.registration_fee),
                     r.get_payment_status_display(), r.registration_date.strftime('%Y-%m-%d')])
    return _csv_response('registration_report.csv',
                         ['Reg ID', 'Username', 'Email', 'Conference', 'Type', 'Fee', 'Payment', 'Date'],
                         rows)


@login_required
def payment_report_csv(request):
    if not _can_view_reports(request):
        return HttpResponse('Forbidden', status=403)
    rows = []
    for p in Payment.objects.all():
        rows.append([p.transaction_id, p.registration.registration_id, p.registration.user.username,
                     p.registration.conference.title, float(p.amount), p.get_status_display(),
                     p.paid_at.strftime('%Y-%m-%d') if p.paid_at else ''])
    return _csv_response('payment_report.csv',
                         ['Txn ID', 'Reg ID', 'User', 'Conference', 'Amount', 'Status', 'Paid At'],
                         rows)


@login_required
def department_report_csv(request):
    if not _can_view_reports(request):
        return HttpResponse('Forbidden', status=403)
    rows = []
    for d in Department.objects.all():
        cset = d.conferences.all()
        ds = Submission.objects.filter(conference__in=cset)
        revenue = Payment.objects.filter(
            status=Payment.PaymentStatus.PAID,
            registration__conference__in=cset,
        ).aggregate(t=Sum('amount'))['t'] or 0
        rows.append([d.name, cset.count(), ds.count(),
                     ds.filter(status=Submission.Status.ACCEPTED).count(),
                     ds.filter(status=Submission.Status.REJECTED).count(),
                     ds.exclude(status__in=[Submission.Status.ACCEPTED, Submission.Status.REJECTED]).count(),
                     float(revenue)])
    return _csv_response('department_report.csv',
                         ['Department', 'Conferences', 'Submissions', 'Accepted', 'Rejected', 'Pending', 'Revenue'],
                         rows)
