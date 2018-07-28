# -*- coding: utf8 -*-
from django.urls import path
from . import views
from django.views.generic import TemplateView

urlpatterns = [
    path('dashboard/<int:action>',  views.MessageList.as_view()),
    path('login/', views.Login.as_view()),
    path('logout/', views.Logout.as_view()),  
    path('user/', views.UserList.as_view()),
    path('user/create/', views.UserCreate.as_view()),    
    path('user/<int:pk>', views.UserDetail.as_view()),
    path('user/<int:pk>/update/', views.UserUpdate.as_view()), 
    path('user/<int:pk>/password/', views.UserPasswordUpdate.as_view()), 
    path('user/<int:pk>/teacher/', views.UserTeacher.as_view()),    
    #註冊學校
    path('school/create/', views.SchoolCreate.as_view()), 
]