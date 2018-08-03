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
    #url(r'^forum/submit/(?P<classroom_id>\d+)/(?P<index>\d+)/$', login_required(views.forum_submit)),    
    #url(r'^forum/file_delete/$', login_required(views.forum_file_delete)), 	
    #url(r'^forum/memo/(?P<classroom_id>\d+)/(?P<index>\d+)/(?P<action>\d+)/$', login_required(views.forum_memo)),  
	
    #url(r'^forum/history/(?P<user_id>\d+)/(?P<index>\d+)/(?P<classroom_id>\d+)/$', login_required(views.forum_history)),  
    #url(r'^forum/like/$', login_required(views.forum_like), name='like'),    
    #url(r'^forum/reply/$', login_required(views.forum_reply), name='reply'),    	
    #url(r'^forum/people/$', login_required(views.forum_people), name='people'), 
    #url(r'^forum/guestbook/$', login_required(views.forum_guestbook), name='guestbook'), 	
    #url(r'^forum/score/$', login_required(views.forum_score), name='score'),   
    #url(r'^forum/jieba/(?P<classroom_id>\d+)/(?P<index>\d+)/$', login_required(views.forum_jieba)), 	
    #url(r'^forum/word/(?P<classroom_id>\d+)/(?P<index>\d+)/(?P<word>[^/]+)/$', login_required(views.forum_word)),  
	  #url(r'^forum/download/(?P<file_id>\d+)/$', views.forum_download, name='forum-download'), 
	  #url(r'^forum/showpic/(?P<file_id>\d+)/$', login_required(views.forum_showpic), name='forum-showpic'), 	
	  #url(r'^forum/publish/(?P<classroom_id>\d+)/(?P<index>\d+)/(?P<action>\d+)/$', login_required(views.forum_publish), name='forum-publish'), 	  
]