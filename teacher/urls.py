# -*- coding: utf8 -*-
from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from . import views

urlpatterns = [
    path('classroom/', views.ClassroomList.as_view()),
    path('classroom/create/', views.ClassroomCreate.as_view()),    
    path('classroom/<int:pk>/update/', views.ClassroomUpdate.as_view()), 
    path('announce/<int:classroom_id>/create/', views.AnnounceCreate.as_view()),   
    #列出所有學生帳號
    path('student/list/', views.StudentList.as_view()),    	
	  #大量匯入帳號
    path('import/upload/', views.StudentUpload.as_view()),   	
    path('import/student/', views.StudentImport.as_view()),   
]