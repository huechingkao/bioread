# -*- coding: utf8 -*-
from django.urls import path
from . import views
from django.views.generic import TemplateView

urlpatterns = [
    path('dashboard/<int:action>',  views.MessageList.as_view()),
    path('login/<int:role>', views.Login.as_view()),
    path('logout/', views.Logout.as_view()),  
    path('user/', views.UserList.as_view()),
    path('user/create/', views.UserCreate.as_view()),    
    path('user/<int:pk>', views.UserDetail.as_view()),
    path('user/<int:pk>/update/', views.UserUpdate.as_view()), 
    path('user/<int:pk>/password/', views.UserPasswordUpdate.as_view()), 
    path('user/<int:pk>/teacher/', views.UserTeacher.as_view()),    
    #註冊學校
    path('school/create/', views.SchoolCreate.as_view()), 
    #私訊
    path('line/classmate/<int:classroom_id>/', views.LineClassmateList.as_view()),      
    path('line/<int:user_id>/<int:classroom_id>/create/', views.LineCreate.as_view()), 
    path('line/<int:pk>/', views.LineDetail.as_view()),    
]