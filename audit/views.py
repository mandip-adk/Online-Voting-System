from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from voting.models import Election, Candidate
from .models import AuditRequest
from .forms import AuditRequestForm, AuditResponseForm
from django.contrib import messages


@login_required
def submit_audit_request(request, election_pk):
    # Only voters who are approved candidates can submit audit requests
    if request.user.role != 'voter':
        return redirect('home')

    election = get_object_or_404(Election, pk=election_pk)

    # Check if this voter is an approved candidate in this election
    try:
        candidate = Candidate.objects.get(
            user=request.user,
            election=election,
            status='approved'       # ← must be approved candidate
        )
    except Candidate.DoesNotExist:
        messages.error(request, "You are not an approved candidate in this election.")
        return redirect('voter_dashboard')

    # Prevent duplicate audit requests
    already_requested = AuditRequest.objects.filter(
        candidate=candidate,
        election=election
    ).exists()

    if already_requested:
        messages.error(request, "You have already submitted an audit request for this election.")
        return redirect('voter_dashboard')

    if request.method == "POST":
        form = AuditRequestForm(request.POST)
        if form.is_valid():
            audit_request          = form.save(commit=False)
            audit_request.candidate = candidate
            audit_request.election  = election
            audit_request.save()
            messages.success(request, "Audit request submitted successfully.")
            return redirect('voter_dashboard')     # ← was candidate_dashboard
    else:
        form = AuditRequestForm()

    return render(request, 'audit/audit_request.html', {
        'form':     form,
        'election': election,
    })


@login_required
def audit_request_list(request):
    # Only organizers can review audit requests
    if request.user.role != 'organizer':          # ← was 'admin'
        return redirect('home')

    # Organizer only sees audit requests for THEIR elections
    audit_requests = AuditRequest.objects.filter(
        election__created_by=request.user          # ← scoped to organizer
    ).select_related('candidate', 'election')

    return render(request, 'audit/audit_list.html', {
        'audit_requests': audit_requests,
        'pending_count':  audit_requests.filter(status='pending').count(),
        'approved_count': audit_requests.filter(status='approved').count(),
        'rejected_count': audit_requests.filter(status='rejected').count(),
    })


@login_required
def audit_request_review(request, pk):
    if request.user.role != 'organizer':          # ← was 'admin'
        return redirect('home')

    audit_request = get_object_or_404(AuditRequest, pk=pk)

    # Make sure this organizer owns the election
    if audit_request.election.created_by != request.user:
        messages.error(request, "You do not have permission to review this audit request.")
        return redirect('organizer_dashboard')

    if request.method == 'POST':
        form = AuditResponseForm(request.POST, instance=audit_request)
        if form.is_valid():
            form.save()
            messages.success(request, "Audit request reviewed successfully.")
            return redirect('organizer_dashboard')  # ← was admin_dashboard
    else:
        form = AuditResponseForm(instance=audit_request)

    return render(request, 'audit/audit_review.html', {
        'form':          form,
        'audit_request': audit_request,
    })


@login_required
def audit_report(request, auditrequest_pk):
    # Only voters (who are candidates) can view their own audit report
    if request.user.role != 'voter':              # ← was 'candidate'
        return redirect('home')

    audit_request = get_object_or_404(AuditRequest, pk=auditrequest_pk)

    # Block if this report doesn't belong to this user
    if audit_request.candidate.user != request.user:
        messages.error(request, "You do not have permission to view this report.")
        return redirect('voter_dashboard')

    return render(request, 'audit/audit_report.html', {
        'audit_request': audit_request,
    })

