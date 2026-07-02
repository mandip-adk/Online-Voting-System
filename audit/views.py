from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import AuditRequest
from voting.models import Election


@login_required
def submit_audit_request(request, election_pk):
    election = get_object_or_404(Election, pk=election_pk)
    return render(request, 'audit/submit_audit_request.html', {'election': election})


@login_required
def audit_request_list(request):
    requests = AuditRequest.objects.all().order_by('-created_at')
    return render(request, 'audit/audit_request_list.html', {'requests': requests})


@login_required
def audit_request_review(request, pk):
    audit = get_object_or_404(AuditRequest, pk=pk)
    return render(request, 'audit/audit_request_review.html', {'audit': audit})


@login_required
def audit_report(request, pk):
    audit = get_object_or_404(AuditRequest, pk=pk)
    return render(request, 'audit/audit_report.html', {'audit': audit})


