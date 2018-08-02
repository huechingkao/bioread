# -*- coding: UTF-8 -*-
from django.db import models
from django.contrib.auth.models import User

# 班級
class Classroom(models.Model):
    # 班級名稱
    name = models.CharField(max_length=30)
    # 選課密碼
    password = models.CharField(max_length=30)
    # 授課教師
    teacher_id = models.IntegerField(default=0)
    
    @property
    def teacher(self):
        return User.objects.get(id=self.teacher_id) 
      
#匯入
class ImportUser(models.Model):
	  username = models.CharField(max_length=50, default="")
	  first_name = models.CharField(max_length=50, default="")
	  password = models.CharField(max_length=50, default="")
	  email = models.CharField(max_length=100, default="")
    
class ClassroomGroup(models.Model):
    # 班級
    classroom_id = models.IntegerField(default=0)
    #分組名稱
    title = models.CharField(max_length=250,null=True,blank=True)    
    #小組數目
    numbers = models.IntegerField(default=6)
    #開放分組
    opening = models.BooleanField(default=True)
		#分組方式
    assign = models.IntegerField(default=0)
       
    def __unicode__(self):
        return self.classroom_id
      
#班級助教
class Assistant(models.Model):
    classroom_id = models.IntegerField(default=0)
    user_id = models.IntegerField(default=0)