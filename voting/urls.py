from django.urls import path
from .views import election_details,election_list,election_result,cast_vote

app_name = "voting"

urlpatterns = [
   path("", election_list, name='elections'),
   path("election/<int:pk>/", election_details, name="election_detail"),
   path("election/<int:pk>/vote/", cast_vote, name="vote"),
   path("election/<int:pk>/results/", election_result, name="result"),

]