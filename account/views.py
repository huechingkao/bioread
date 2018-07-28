# -*- coding: utf8 -*-
from django.shortcuts import render
from django.views import generic
from django.contrib.auth.models import User, Group
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.http import is_safe_url
from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login, logout as auth_logout
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import FormView, RedirectView
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from .forms import LoginForm, UserRegistrationForm, UserUpdateForm, UserPasswordForm, UserTeacherForm, RegistrationSchoolForm
from account.models import County, Zone, School, Profile, PointHistory, Message, MessageContent, MessagePoll, Visitor, VisitorLog, LessonCounter
from account.zone import *
from django.utils import timezone
from django.utils.timezone import localtime

class Login(FormView):
    success_url = '/account/dashboard/0'
    form_class = LoginForm
    redirect_field_name = REDIRECT_FIELD_NAME
    template_name = "login.html"

    @method_decorator(sensitive_post_parameters('password'))
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        # Sets a test cookie to make sure the user has cookies enabled
        request.session.set_test_cookie()

        return super(Login, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = User.objects.get(username=form.cleaned_data['username'])
        auth_login(self.request, user)
        if user.id == 1 and user.first_name == "":
            user.first_name = "管理員"
            user.save()
            
            zones = Zone.objects.all()
            if len(zones) == 0:
                for city_name, zones, mapx, mapy in county:
                    city = County(name=city_name, mapx=mapx, mapy=mapy)
                    city.save()
                    for zone_name in zones:
                        zone = Zone(name=zone_name, county=city.id)
                        zone.save()
                school = School(county=1, zone=9, system=3, name="南港高中")
                school.save()
                user.last_name = "1"
                user.save()
                try :
                    group = Group.objects.get(name="apply")	
                except ObjectDoesNotExist :
                    group = Group(name="apply")
                    group.save()                                         
                group.user_set.add(user)														
                # create Message
                title = "請修改您的姓名"
                url = "/account/realname"
                message = Message(title=title, url=url, time=timezone.now())
                message.save()                        
                    
                # message for group member
                messagepoll = MessagePoll(message_id = message.id,reader_id=1)
                messagepoll.save() 														
        # 記錄訪客資訊
        admin_user = User.objects.get(id=1)
        try:
            profile = Profile.objects.get(user=admin_user)
        except ObjectDoesNotExist:
            profile = Profile(user=admin_user)
            profile.save()
        profile.visitor_count = profile.visitor_count + 1
        profile.save()
                                    
        year = localtime(timezone.now()).year
        month =  localtime(timezone.now()).month
        day =  localtime(timezone.now()).day
        date_number = year * 10000 + month*100 + day
        try:
            visitor = Visitor.objects.get(date=date_number)
        except ObjectDoesNotExist:
            visitor = Visitor(date=date_number)
        visitor.count = visitor.count + 1
        visitor.save()
                                        
        visitorlog = VisitorLog(visitor_id=visitor.id, user_id=user.id, IP=self.request.META.get('REMOTE_ADDR'))
        visitorlog.save()                 
          
        # If the test cookie worked, go ahead and
        # delete it since its no longer needed
        if self.request.session.test_cookie_worked():
            self.request.session.delete_test_cookie()

        return super(Login, self).form_valid(form)

    def get_success_url(self):
        redirect_to = self.request.GET.get(self.redirect_field_name)
        if not is_safe_url(url=redirect_to, host=self.request.get_host()):
            redirect_to = self.success_url
        return redirect_to

class Logout(RedirectView):
    url = '/account/login/'

    def get(self, request, *args, **kwargs):
        auth_logout(request)
        return super(Logout, self).get(request, *args, **kwargs)
              
class SuperUserRequiredMixin(object):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect("/account/login")
        return super(SuperUserRequiredMixin, self).dispatch(request,
            *args, **kwargs)

class UserList(SuperUserRequiredMixin, generic.ListView):
    model = User
    ordering = ['-id']
    paginate_by = 3    

class UserDetail(LoginRequiredMixin, generic.DetailView):
    model = User
    
class UserCreate(CreateView):
    model = User
    form_class = UserRegistrationForm
    success_url = "/account/login"   
    #template_name = 'form.html'
      
    def form_valid(self, form):
        valid = super(UserCreate, self).form_valid(form)
        new_user = form.save(commit=False)
        new_user.set_password(form.cleaned_data.get('password'))
        new_user.save()  
        return valid

class UserUpdate(SuperUserRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    success_url = "/account/user"   
    template_name = 'form.html'
    
class UserPasswordUpdate(SuperUserRequiredMixin, UpdateView):
    model = User
    form_class = UserPasswordForm
    success_url = "/account/user"   
    template_name = 'form.html'
    
    def form_valid(self, form):
        valid = super(UserPasswordUpdate, self).form_valid(form)
        new_user = form.save(commit=False)
        new_user.set_password(form.cleaned_data.get('password'))
        new_user.save()  
        return valid   

class UserTeacher(SuperUserRequiredMixin, FormView):
    success_url = '/account/user'
    form_class = UserTeacherForm
    template_name = "form.html"
      
    def form_valid(self, form):
        valid = super(UserTeacherView, self).form_valid(form)
        user = User.objects.get(id=self.kwargs['pk'])
        try :
            group = Group.objects.get(name="teacher")	
        except ObjectDoesNotExist :
            group = Group(name="teacher")
            group.save()        
        if form.cleaned_data.get('teacher') :
            group.user_set.add(user)
        else: 
            group.user_set.remove(user)
        return valid  
      
    def get_form_kwargs(self):
        kwargs = super(UserTeacher, self).get_form_kwargs()
        kwargs.update({'pk': self.kwargs['pk']})
        return kwargs
      
# 訊息
class MessageList(ListView):
    context_object_name = 'messages'
    paginate_by = 20
    template_name = 'dashboard.html'

    def get_queryset(self):             
        query = []
        #公告
        if self.kwargs['action'] == "1":
            messagepolls = MessagePoll.objects.filter(reader_id=self.request.user.id, message_type=1).order_by('-message_id')
        #私訊
        elif self.kwargs['action'] == "2":
            messagepolls = MessagePoll.objects.filter(reader_id=self.request.user.id, message_type=2).order_by('-message_id')
        #系統
        elif self.kwargs['action'] == "3":
            messagepolls = MessagePoll.objects.filter(reader_id=self.request.user.id, message_type=3).order_by('-message_id')						
        else :
            messagepolls = MessagePoll.objects.filter(reader_id=self.request.user.id).order_by('-message_id')
        for messagepoll in messagepolls:
            query.append([messagepoll, messagepoll.message])
        return query
        
    def get_context_data(self, **kwargs):
        context = super(MessageList, self).get_context_data(**kwargs)
        context['action'] = self.kwargs['action']
        return context

class SchoolCreate(CreateView):
    model = School
    form_class = RegistrationSchoolForm
    success_url = "/account/create"   
    template_name = 'school_create.html'
      
    def form_valid(self, form):
        valid = super(SchoolCreate, self).form_valid(form)
        school = form.save() 
        return valid
      
    def get_success_url(self):
        redirect_to = self.request.GET.get(self.redirect_field_name)
        if not is_safe_url(url=redirect_to, host=self.request.get_host()):
            redirect_to = self.success_url
        return redirect_to
