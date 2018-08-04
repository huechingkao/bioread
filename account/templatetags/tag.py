from django import template
from django.contrib.auth.models import User, Group
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from account.models import *
from teacher.models import *
from student.models import *
import json
import re

register = template.Library()

@register.filter(name='assistant') 
def assistant(user_id):
    assistants = Assistant.objects.filter(user_id=user_id)
    if assistants:
      return True
    return False

@register.filter
def teacher_group(user):
    return user.groups.filter(name='teacher').exists()
  
@register.filter
def teacher_classroom(user_id, classroom_id):
    classroom = Classroom.object.get(id=classroom_id)
    if classroom.teacher_id == user_id:
        return True
    else:
        return False

@register.filter(takes_context=True)
def realname(user_id):
    try: 
        user = User.objects.get(id=user_id)
        return user.first_name
    except :
        pass
    return ""
  
@register.filter(takes_context=True)
def read_already(message_id, user_id):
    try:
        messagepoll = MessagePoll.objects.get(message_id=message_id, reader_id=user_id)
    except ObjectDoesNotExist:
        messagepoll = MessagePoll()
    return messagepoll.read      
  
@register.filter(name="img")
def img(title):
    if title.startswith(u'[私訊]'):
        return "line"
    elif title.startswith(u'[公告]'):
        return "announce"
    elif u'擔任小老師' in title:
        return "assistant"
    elif u'設您為教師' in title:
        return "teacher"
    elif u'核發了一張證書給你' in title:
        return "certificate"
    else :
        return ""
      
@register.filter
def teacher_group(user):
    return user.groups.filter(name='teacher').exists()
  
@register.filter
def teacher_classroom(user_id, classroom_id):
    classroom = Classroom.object.get(id=classroom_id)
    if classroom.teacher_id == user_id:
        return True
    else:
        return Fals

@register.filter
def student_username(name):
    start = "_"
    student = name[name.find(start)+1:]
    return student    
  
@register.filter()
def int_to_str(number):   
    return str(number)

@register.filter
def classname(classroom_id):
    try: 
        classroom = Classroom.objects.get(id=classroom_id)
        return classroom.name
    except ObjectDoesNotExist:
        pass
        return ""  
      
@register.filter()
def memo(text):
  memo = re.sub(r"\n", r"<br/>", re.sub(r"\[m_(\d+)#(\d\d:\d\d:\d\d)\]", r"<button class='btn btn-default btn-xs btn-marker' data-mid='\1' data-time='\2'><span class='badge'>\1</span> \2</button>",text))
  return memo

@register.filter()
def number(youtube):
    number_pos = youtube.find("v=")
    number = youtube[number_pos+2:number_pos+13]
    return number
  
@register.filter
def alert(deadline):
    if (deadline - timezone.now()).days < 2 and deadline > timezone.now():
        return True
    else:
        return False
      
@register.filter
def due(deadline):
    return str(deadline-timezone.now()).split('.')[0]
  
@register.filter
def in_deadline(forum_id, classroom_id):
    try:
        fclass = FClass.objects.get(forum_id=forum_id, classroom_id=classroom_id)
    except ObjectDoesNotExist:
        fclass = FClass(forum_id=forum_id, classroom_id=classroom_id)
    if fclass.deadline:
        if timezone.now() > fclass.deadline_date:
            return fclass.deadline_date
    return ""
  
@register.filter()
def is_teacher(user_id, classroom_id):
    classroom = Classroom.objects.get(id=classroom_id)
    if user_id == classroom.teacher_id :
      return True
    else:
      return False  

@register.filter()
def is_assistant(user_id, classroom_id):
    assistants = Assistant.objects.filter(classroom_id=classroom_id, user_id=user_id)
    if len(assistants) > 0 :
      return True
    else:
      return False  
    
@register.filter()
def is_pic(title):   
    if title[-3:].upper() == "PNG":
        return True
    if title[-3:].upper() == "JPG":
        return True   
    if title[-3:].upper() == "GIF":
        return True            
    return False    
  
@register.filter()
def likes(work_id):
    sfwork = SFWork.objects.get(id=work_id)
    jsonDec = json.decoder.JSONDecoder()    
    if sfwork.likes:
        like_ids = jsonDec.decode(sfwork.likes)
        return like_ids
    return []  