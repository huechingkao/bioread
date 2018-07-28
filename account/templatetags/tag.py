from django import template
from django.contrib.auth.models import User, Group
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

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