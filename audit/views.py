from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from .models import AuditRequest
from .forms import AuditRequestForm, AuditResponseForm
from voting.models import Election


def is_admin(user):
    return user.is_authenticated and (user.role == 'admin' or user.is_superuser)


@login_required
def submit_audit_request(request, election_pk):
    election = get_object_or_404(Election, pk=election_pk, created_by=request.user)

    if request.method == 'POST':
        form = AuditRequestForm(request.POST)
        if form.is_valid():
            audit_request = form.save(commit=False)
            audit_request.election = election
            audit_request.save()
            messages.success(request, 'Your audit request has been submitted.')
            return redirect('organizer_dashboard')
    else:
        form = AuditRequestForm()

    return render(request, 'audit/audit_request.html', {
        'election': election,
        'form': form,
        'total_votes': election.electoral_roll.filter(used=True).count(),
        'total_contests': election.contests.count(),
    })


@login_required
@user_passes_test(is_admin)
def audit_request_list(request):
    audit_requests = AuditRequest.objects.select_related('election').order_by('-created_at')

    context = {
        'audit_requests': audit_requests,
        'pending_count': audit_requests.filter(status='pending').count(),
        'approved_count': audit_requests.filter(status='approved').count(),
        'rejected_count': audit_requests.filter(status='rejected').count(),
    }
    return render(request, 'audit/audit_list.html', context)


@login_required
@user_passes_test(is_admin)
def audit_request_review(request, pk):
    audit_request = get_object_or_404(AuditRequest, pk=pk)

    if request.method == 'POST':
        form = AuditResponseForm(request.POST, instance=audit_request)
        if form.is_valid():
            form.save()
            messages.success(request, 'Audit request has been reviewed.')
            return redirect('audit:audit_list')
    else:
        form = AuditResponseForm(instance=audit_request)

    return render(request, 'audit/audit_review.html', {
        'audit_request': audit_request,
        'form': form,
        'total_votes': audit_request.election.electoral_roll.filter(used=True).count(),
        'total_contests': audit_request.election.contests.count(),
    })


@login_required
def audit_report(request, pk):
    audit_request = get_object_or_404(AuditRequest, pk=pk)
    return render(request, 'audit/audit_report.html', {
        'audit_request': audit_request,
        'total_votes': audit_request.election.electoral_roll.filter(used=True).count(),
        'total_contests': audit_request.election.contests.count(),
    })

