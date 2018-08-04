# -*- coding: utf8 -*-
from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from . import views

urlpatterns = [
    path('classroom/', views.ClassroomList.as_view()),
    path('classroom/join/', views.ClassroomJoinList.as_view()),    
    path('classroom/<int:pk>/enroll/', views.ClassroomEnrollCreate.as_view()), 
    path('classroom/<int:pk>/classmate/', views.ClassmateList.as_view()),    
    path('classroom/<int:pk>/seat/', views.ClassroomSeatUpdate.as_view()),   
    #組別
    path('group/<int:classroom_id>/', views.GroupList.as_view()),
    path('group/panel/<int:group_id>/', views.GroupPanel.as_view()),
    path('group/join/<int:group_id>/<int:number>/<int:enroll_id>/', views.GroupJoin.as_view()),	
    #討論區
    path('forum/<int:classroom_id>/<int:bookmark>/', views.ForumList.as_view()),  
    path('forum/show/<int:index>/<int:user_id>/<int:classroom_id>/', views.ForumShow.as_view()),   
    path('forum/submit/<int:classroom_id>/<int:index>/', views.ForumSubmit.as_view()),    
	  path('forum/publish/<int:classroom_id>/<int:index>/', views.ForumPublish.as_view()),
  	path('forum/publish/done/<int:classroom_id>/<int:index>/', views.ForumPublishDone.as_view()),
    path('forum/memo/<int:classroom_id>/<int:index>/<int:action>/', views.ForumMemo.as_view()),  
    #url(r'^forum/file_delete/$', login_required(views.forum_file_delete)), 	
	
    path('forum/history/<int:user_id>/<int:index>/<int:classroom_id>/', views.ForumHistory.as_view()),  
    path('forum/like/', views.forum_like),    
    path('forum/reply/', views.forum_reply),    	
    path('forum/people/', views.forum_people), 
    path('forum/guestbook/', views.forum_guestbook), 	
    path('forum/score/', views.forum_score),   
    #url(r'^forum/jieba/(?P<classroom_id>\d+)/(?P<index>\d+)/$', login_required(views.forum_jieba)), 	
    #url(r'^forum/word/(?P<classroom_id>\d+)/(?P<index>\d+)/(?P<word>[^/]+)/$', login_required(views.forum_word)),  
	  #url(r'^forum/download/(?P<file_id>\d+)/$', views.forum_download, name='forum-download'), 
	  #path('forum/showpic/<int:file_id>/', views.ForumShowPic.as_view()), 	
]