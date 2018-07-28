# -*- coding: utf8 -*-
from django.urls import path
from . import views
from django.views.generic import TemplateView

urlpatterns = [
    path('', TemplateView.as_view(template_name="dashboard.html")),
    path('login/', views.Login.as_view()),
    path('logout/', views.Logout.as_view()),  
    path('user/', views.UserList.as_view()),
    path('user/create/', views.UserCreate.as_view()),    
    path('user/<int:pk>', views.UserDetail.as_view()),
    path('user/<int:pk>/update/', views.UserUpdate.as_view()), 
    path('user/<int:pk>/password/', views.UserPasswordUpdate.as_view()), 
    path('user/<int:pk>/teacher/', views.UserTeacher.as_view()),    

]