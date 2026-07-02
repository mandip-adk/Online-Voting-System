from django.urls import path
from .views import (
    submit_audit_request,
    audit_request_list,
    audit_request_review,
    audit_report,
)

app_name = 'audit'

urlpatterns = [
    path('request/<int:election_pk>/', submit_audit_request,  name='audit_request'),
    path('requests/',  audit_request_list,    name='audit_list'),
    path('request/review/<int:pk>/',   audit_request_review,  name='audit_review'),
    path('report/<int:pk>/',    audit_report,   name='audit_report'),
]

