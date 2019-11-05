"""drchrono_hackathon URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from drchrono import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('accounts/', include('accounts.urls')),
    path('authorize', views.authorize, name='authorize'),
    path('drchrono_login', views.drchrono_login, name='drchrono_login'),
    path('appointments', views.appointments, name='appointments'),
    path('patients', views.get_all_patients, name='patients'),
    path('checkin', views.checkin, name='checkin'),
    path('checkin_complete/<path:id>/', views.checkin_complete, name='checkin_complete'),
    path('patients_checkin', views.patients_checkin, name='patients_checkin'),
    #path('update_demographics', views.update_demographics, name='update_demographics'),
    path('status_change/<path:id>/', views.status_change),
    path('demographics/<path:id>/', views.demographics),
]
