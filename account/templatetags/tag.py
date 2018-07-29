from django import template
from django.contrib.auth.models import User, Group
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from account.models import MessagePoll

register = template.Library()

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