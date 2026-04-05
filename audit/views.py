from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from voting.models import Election
from .models import Auditrequest
from .forms import AuditRequestForm


@login_required
def submit_audit_request(request, election_pk):
    if request.user.role != "candidate":
        return redirect('home')
    
    election = get_object_or_404(Election, pk=election_pk)

    if request.method =="POST":
        form = AuditRequestForm(request.POST)
        if form.is_valid():
            audit_request = form.save(commit=False)
            audit_request.candidate = request.user.candidate

            audit_request.election = election
            audit_request.save()
            

