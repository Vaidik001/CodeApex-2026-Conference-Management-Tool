from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from accounts.models import Profile, Notification
from registrations.models import Registration
from .models import Payment


def _can_manage(request):
    return request.user.is_authenticated and (
        request.user.is_superuser or request.user.profile.role in (Profile.Role.ADMIN, Profile.Role.COORDINATOR)
    )


@login_required
def payment_create(request, reg_id):
    reg = get_object_or_404(Registration, pk=reg_id)
    if reg.user != request.user and not _can_manage(request):
        messages.error(request, 'Access denied.')
        return redirect('dashboard_redirect')
    if reg.payment_status == Registration.PaymentStatus.PAID:
        messages.info(request, 'This registration is already paid.')
        return redirect('payment_receipt', reg_id=reg.pk)
    if request.method == 'POST':
        payment = Payment.objects.create(
            registration=reg,
            amount=reg.registration_fee,
            status=Payment.PaymentStatus.PAID,
            paid_at=timezone.now(),
        )
        reg.payment_status = Registration.PaymentStatus.PAID
        reg.save()
        Notification.objects.create(
            user=reg.user,
            message=f'Payment {payment.transaction_id} of {payment.amount} confirmed for {reg.conference.title}.',
        )
        messages.success(request, 'Payment successful.')
        return redirect('payment_receipt', reg_id=reg.pk)
    return render(request, 'payments/payment_form.html', {'reg': reg})


@login_required
def payment_receipt(request, reg_id):
    reg = get_object_or_404(Registration, pk=reg_id)
    if reg.user != request.user and not _can_manage(request):
        messages.error(request, 'Access denied.')
        return redirect('dashboard_redirect')
    payment = reg.payments.filter(status=Payment.PaymentStatus.PAID).first()
    return render(request, 'payments/payment_receipt.html', {'reg': reg, 'payment': payment})


@login_required
def all_payments(request):
    if not _can_manage(request):
        messages.error(request, 'Access denied.')
        return redirect('dashboard_redirect')
    qs = Payment.objects.all()
    status = request.GET.get('status', '')
    if status: qs = qs.filter(status=status)
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'payments/all_payments.html', {
        'page_obj': page_obj,
        'status': status,
        'status_choices': Payment.PaymentStatus.choices,
    })
