# -*- coding: UTF-8 -*-
from django.db import models
from django.contrib.auth.models import User
from teacher.models import Classroom
from django.utils import timezone

# 學生選課資料
class Enroll(models.Model):
    # 學生序號
    student_id = models.IntegerField(default=0)
    # 班級序號
    classroom_id = models.IntegerField(default=0)
    # 座號
    seat = models.IntegerField(default=0)
	
    @property
    def classroom(self):
        return Classroom.objects.get(id=self.classroom_id)  

    @property        
    def student(self):
        return User.objects.get(id=self.student_id)   
      
class StudentGroup(models.Model):
    group_id = models.IntegerField(default=0)
    enroll_id = models.IntegerField(default=0)
    group = models.IntegerField(default=0)		

    class Meta:
        unique_together = ('enroll_id', 'group_id',)				
