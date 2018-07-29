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