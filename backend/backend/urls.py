"""
URL configuration for backend project.

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
from django.urls import path, re_path
from django.views.generic.base import RedirectView

from higherstudiesportal import views

favicon_view = RedirectView.as_view(url='/static/favicon.ico', permanent=True)

urlpatterns = [
    path('', views.index, name='index'),
    # Django admin
    path('admin/', admin.site.urls),
    # Favicon
    re_path(r'^favicon\.ico$', favicon_view),
    # Login page
    path('login/', views.login_view, name='login'),
    # Student Routes
    path('student/dashboard/', views.dashboard_student, name='student_dashboard'),
    path('student/lor/', views.lor_application_student, name='student_lor'),
    path('student/lor-tracking/', views.lor_tracking_student, name='student_lor-tracking'),
    path('student/letter-upload', views.letter_upload, name='student_letter-upload'),
    # Faculty routes
    path('faculty/dashboard/', views.dashboard_faculty, name='faculty_dashboard'),
]

