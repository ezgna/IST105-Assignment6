from django.urls import path
from . import views

urlpatterns = [
    # Input form and result display
    path('', views.index, name='index'),
    # Saved entries history (MongoDB)
    path('history/', views.history, name='history'),
]
