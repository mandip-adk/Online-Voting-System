from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from voting.models import Election, Candidate
from .models import AuditRequest
from .forms import AuditRequestForm, AuditResponseForm


@login_required
def submit_audit_request(request, election_pk):
    if request.user.role != "candidate":
        return redirect('home')
    
    election = get_object_or_404(Election, pk=election_pk)

    try:
        candidate = Candidate.objects.get(user=request.user, election=election)
    except Candidate.DoesNotExist:
        # If the user is not a candidate in this election, block access
        return redirect('home')

    if request.method =="POST":
        form = AuditRequestForm(request.POST)
        if form.is_valid():
            audit_request = form.save(commit=False)
            audit_request.candidate = candidate
            audit_request.election = election
            audit_request.save()
            return redirect ('candidate_dashboard')
    else:
        form = AuditRequestForm()
    return render(request, 'audit/audit_request.html', {
        'form':form,
        'election': election,
    })

@login_required
def audit_request_list(request):
    if request.user.role != 'admin':
        return redirect('home')
    
    audit_requests = AuditRequest.objects.all()
    return render(request, 'audit/audit_list.html',{
        'audit_requests':audit_requests,
        'pending_count':   audit_requests.filter(status='pending').count(),
        'approved_count':  audit_requests.filter(status='approved').count(),
        'rejected_count':  audit_requests.filter(status='rejected').count(),
        })

@login_required
def audit_request_review(request, pk):
    if request.user.role != 'admin':
        return redirect ('home')
    
    audit_request =get_object_or_404(AuditRequest, pk=pk)
    if request.method == 'POST':
        form = AuditResponseForm(request.POST, instance=audit_request)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    else:
        form = AuditResponseForm(instance=audit_request)
    return render(request, 'audit/audit_review.html', {
        'form': form,
        'audit_request': audit_request,
    } )


@login_required
def audit_report(request, auditrequest_pk):
    if request.user.role != 'candidate':
        return redirect ('home')
    
    audit_request = get_object_or_404(AuditRequest, pk=auditrequest_pk)

    if audit_request.candidate.user != request.user:
        return redirect('home')

    return render(request, 'audit/audit_report.html', {
        'audit_request': audit_request,
    })

