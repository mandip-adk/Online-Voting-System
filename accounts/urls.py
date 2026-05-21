from django.urls import path
from .views import register, login_view, logout_view, home, voter_dashboard, organizer_dashboard, admin_dashboard


urlpatterns = [
    path('register/',  register,  name='register'),
    path('login/',   login_view,  name='login'),
    path('logout/',  logout_view, name='logout'),
    path('',   home, name='home'),
    path('voter/dashboard/',  voter_dashboard, name='voter_dashboard'),
    path('organizer/dashboard/',organizer_dashboard, name='organizer_dashboard'),
    path('admin-dashboard/',    admin_dashboard, name='admin_dashboard'),
]

