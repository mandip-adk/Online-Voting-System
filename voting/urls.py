from django.urls import path
from .views import (
    election_details, election_list, election_result,
    cast_vote, create_election, apply_candidate,
    approve_candidate, reject_candidate,
    edit_election, delete_election
)

app_name = "voting"

urlpatterns = [
    path("", election_list, name='elections'),
    path("election/create/", create_election,   name="create_election"),
    path("election/<int:pk>/", election_details,  name="election_detail"),
    path("election/<int:pk>/vote/", cast_vote, name="vote"),
    path("election/<int:pk>/results/", election_result,   name="result"),
    path("election/<int:pk>/apply/",  apply_candidate,   name="apply_candidate"),
    path("election/<int:pk>/edit/",  edit_election,     name="edit_election"),
    path("election/<int:pk>/delete/", delete_election,   name="delete_election"),
    path("candidate/<int:pk>/approve/", approve_candidate, name="approve_candidate"),
    path("candidate/<int:pk>/reject/",  reject_candidate,  name="reject_candidate"),

    
]