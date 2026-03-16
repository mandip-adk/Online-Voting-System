from django.urls import path
from .views import register, login_view, logout_view, home



urlpatterns = [
    path('register/', register , name='register' ),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('', home, name='home'),
    
]
