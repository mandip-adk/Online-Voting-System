from django.urls import path
from .views import register, login_view, logout_view, home, organizer_dashboard, admin_dashboard

urlpatterns = [
    path('',                     home,                 name='home'),
    path('register/',            register,             name='register'),
    path('login/',               login_view,           name='login'),
    path('logout/',              logout_view,          name='logout'),
    path('organizer/dashboard/', organizer_dashboard,  name='organizer_dashboard'),
    path('admin-dashboard/',     admin_dashboard,      name='admin_dashboard'),
]


