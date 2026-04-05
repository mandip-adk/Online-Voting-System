from django.urls import path
from .views import submit_audit_request,  audit_request_list, audit_request_review, audit_report

app_name = 'audit'
urlpatterns=[
    path("audit/request/<int:election_pk>/", submit_audit_request, name='audit_submit'),
    path("audit/request/", audit_request_list, name='audit_list'),
    path("audit/request_review/<int:pk>/", audit_request_review, name='audit_review'),
    path("audit/audit_report/<int:auditrequest_pk>/", audit_report, name='audit_report'),

]