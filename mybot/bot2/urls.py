from django.urls import path
from . import views

urlpatterns = [
    path('messages/', views.messages, name='messages'),
    path('health/', views.health_check, name='health_check'),
    path('test/', views.test_bot, name='test_bot'),
] 