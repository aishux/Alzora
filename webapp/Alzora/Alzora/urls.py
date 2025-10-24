"""
URL configuration for Alzora project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path
from alzoraapp.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', mainpage, name="mainpage"),
    path('login/',handleLogin, name="login"),
    path('signup/',handleSignup, name="signup"),
    path('logout/',handleLogout, name="logout"),
    path('addpatient/', addPatient, name="addPatient"),
    path('chat/', chat, name="chat"),
    path('dashboard/', dashboard, name="dashboard"),
    path('patientinfo/<str:patient_id>', patientInfo, name="patientInfo"),
    path('updatepatientinfo/', updatePatientInfo, name="updatePatientInfo"),
    path('chartdata/<str:patient_id>', chartData, name="chartData"),
]