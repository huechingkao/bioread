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
    # 討論區
    #path('forum/<int:categroy>/<int:categroy_id>', views.ForumAllListView.as_view()),  
    #url(r'^forum/show/(?P<forum_id>\d+)/$', login_required(views.forum_show), name='forum-show'),    
    path('forum/<int:classroom_id>/', views.ForumListView.as_view()),
    path('forum/add/<int:classroom_id>/', views.ForumCreateView.as_view()),
    path('forum/edit/<int:classroom_id>/<int:pk>/', views.ForumEditUpdate.as_view()),     
    path('forum/class/<int:forum_id>/', views.ForumClassList.as_view()),      
    path('forum/class/switch/', views.forum_switch),      
    path('forum/deadline/<int:classroom_id>/<int:pk>/', views.ForumDeadlineUpdate.as_view()),  
    path('forum/deadline/set/', views.forum_deadline_set), 
    path('forum/deadline/date/', views.forum_deadline_date),   
    path('forum/content/<int:forum_id>/', views.ForumContentList.as_view()), 
    path('forum/content/add/<int:forum_id>/', views.ForumContentCreate.as_view()),
    path('forum/content/delete/<int:forum_id>/<int:content_id>/', views.forum_delete),   
    #url(r'^forum/content/edit/(?P<forum_id>\d+)/(?P<content_id>\d+)/$', login_required(views.forum_edit), name='forum-content-edit'),      
    path('forum/download/<int:content_id>/', views.forum_download),  


    #url(r'^forum/export/(?P<classroom_id>\d+)/(?P<forum_id>\d+)/$', login_required(views.forum_export), name='forum-export'),   
    #url(r'^forum/grade/(?P<classroom_id>\d+)/(?P<action>\d+)/$', login_required(views.forum_grade), name='forum-grade'),   
  
]