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

#作業
class SFWork(models.Model):
    student_id = models.IntegerField(default=0)
    index = models.IntegerField()
    memo = models.TextField(default='')
    memo_e =  models.IntegerField(default=0)
    memo_c = models.IntegerField(default=0)		
    publish = models.BooleanField(default=False)
    publication_date = models.DateTimeField(default=timezone.now)
    reply_date = models.DateTimeField(default=timezone.now)
    score = models.IntegerField(default=0)
    scorer = models.IntegerField(default=0)
    comment = models.TextField(default='',null=True,blank=True)
    comment_publication_date = models.DateTimeField(default=timezone.now)		
    likes = models.TextField(default='')
    like_count = models.IntegerField(default=0)	
    reply = models.IntegerField(default=0)
		
    def __unicode__(self):
        user = User.objects.filter(id=self.student_id)[0]
        index = self.index
        return user.first_name+"("+str(index)+")"

class SFContent(models.Model):
    index =  models.IntegerField(default=0)
    student_id = models.IntegerField(default=0)
    work_id = models.IntegerField(default=0)
    title =  models.CharField(max_length=250,null=True,blank=True)
    filename = models.CharField(max_length=60,null=True,blank=True)    
    publication_date = models.DateTimeField(default=timezone.now)
    delete_date = models.DateTimeField(default=timezone.now)		
    visible = models.BooleanField(default=True)

#討論留言
class SFReply(models.Model):
    index = models.IntegerField(default=0)
    work_id =  models.IntegerField(default=0)
    user_id = models.IntegerField(default=0)
    memo =  models.TextField(default='')
    publication_date = models.DateTimeField(default=timezone.now)        