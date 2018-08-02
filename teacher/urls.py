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
    # 分組
    path('group/<int:classroom_id>/', views.GroupList.as_view()),
    path('group/add/<int:classroom_id>/', views.GroupCreate.as_view()),  
    path('group/edit/<int:classroom_id>/<int:pk>/', views.GroupUpdate.as_view()),    
    path('group/make/',views.make),   
    path('group/make2/<int:group_id>/<int:action>/', views.make2),  
    #設定助教
    path('classroom/assistant/<int:classroom_id>/', views.ClassroomAssistant.as_view()),  
    path('classroom/assistant/add/<int:classroom_id>/', views.AssistantList.as_view()),    
    path('assistant/', views.AssistantClassroomList.as_view()),  
    path('assistant/make/', views.assistant_make),  
]