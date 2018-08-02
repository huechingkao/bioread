# -*- coding: utf8 -*-
from django.shortcuts import render
from django.views import generic
from django.contrib.auth.models import User, Group
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, FormView
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
from account.forms import *
from account.models import *
from account.zone import *
from django.utils import timezone
from django.utils.timezone import localtime
from student.models import *
from django.contrib.auth import authenticate, login

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
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']         
        if self.kwargs['role'] == 0:	
            user = authenticate(username=username, password=password)
        else:
            teacher = form.cleaned_data['teacher']					
            user = authenticate(username=teacher+"_"+username, password=password)   
        if user is not None:
            auth_login(self.request, user)
        else :
            return redirect("/account/login/"+str(self.kwargs['role']))
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
                school = School(county=2, zone=38, system=3, name="南港高中")
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

    def get_form_class(self):
        if self.kwargs['role'] == 0:
            return LoginForm
        else :
            return LoginStudentForm
      
class Logout(RedirectView):
    url = '/account/login/0'

    def get(self, request, *args, **kwargs):
        auth_logout(request)
        return super(Logout, self).get(request, *args, **kwargs)
              
class SuperUserRequiredMixin(object):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect("/account/login/0")
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
    success_url = "/account/login/0"   
    #template_name = 'user_create.html'
      
    def form_valid(self, form):
        valid = super(UserCreate, self).form_valid(form)
        new_user = form.save(commit=False)
        new_user.set_password(form.cleaned_data.get('password'))
        new_user.save()  
        profile = Profile(user=new_user)
        profile.save()        
        return valid
      
    def get_context_data(self, **kwargs):
        context = super(UserCreate, self).get_context_data(**kwargs)
        context['schools'] = School.objects.all()
        return context

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
        valid = super(UserTeacher, self).form_valid(form)
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
    redirect_field_name = REDIRECT_FIELD_NAME    
    success_url = "/account/user/create"   
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
      
    def get_context_data(self, **kwargs):
        context = super(SchoolCreate, self).get_context_data(**kwargs)
        context['schools'] = School.objects.all()
        return context

# 判斷是否為本班同學
def is_classmate(user_id, classroom_id):
    return Enroll.objects.filter(student_id=user_id, classroom_id=classroom_id).exists()

# 判斷可否觀看訊息
def line_can_read(message_id, user_id):
    if MessagePoll.objects.filter(message_id=message_id, reader_id=user_id).exists():
        return True
    elif Message.objects.filter(id=message_id, author_id=user_id).exists():
        return True
    else:
        return False
      
# 列出同學以私訊
class LineClassmateList(LoginRequiredMixin, generic.ListView):
    model = Enroll
    template_name = 'account/line_classmate.html'   
    
    def get_queryset(self):     
        queryset = Enroll.objects.filter(classroom_id=self.kwargs['classroom_id']).order_by("seat")
        return queryset
        
    # 限本班同學
    def render_to_response(self, context):
        if not is_classmate(self.request.user.id, self.kwargs['classroom_id']):
            return redirect('/')
        return super(LineClassmateList, self).render_to_response(context)            
                
#新增一個私訊
class LineCreate(LoginRequiredMixin, CreateView):
    model = Message
    form_class = LineForm
    success_url = '/account/dashboard/0'    
    template_name = 'account/line_form.html'     

    def form_valid(self, form):
        valid = super(LineCreate, self).form_valid(form)
        self.object = form.save(commit=False)
        user_name = User.objects.get(id=self.request.user.id).first_name
        self.object.title = u"[私訊]" + user_name + ":" + self.object.title
        self.object.author_id = self.request.user.id
        self.object.save()
        # 訊息
        messagepoll = MessagePoll(message_id=self.object.id, reader_id=self.kwargs['user_id'])
        messagepoll.save()              
        return valid
      
    # 限本班同學
    def render_to_response(self, context):
        if not is_classmate(self.request.user.id, self.kwargs['classroom_id']):
            return redirect('/')
        return super(LineCreate, self).render_to_response(context)       
      
    def get_context_data(self, **kwargs):
        context = super(LineCreate, self).get_context_data(**kwargs)
        context['user_id'] = self.kwargs['user_id']
        messagepolls = MessagePoll.objects.filter(reader_id=self.kwargs['user_id'])
        message_ids = list(map(lambda a: a.message_id, messagepolls))
        context['messages']  = Message.objects.filter(id__in=message_ids, author_id=self.request.user.id).order_by("-id")
        return context	       

# 訊息內容
class LineDetail(generic.DetailView):
    model = Message
    template_name = "account/line_detail.html"
    
    def get_context_data(self, **kwargs):
        context = super(LineDetail, self).get_context_data(**kwargs)
        try: 
            messagepoll = MessagePoll.objects.get(message_id=self.kwargs['pk'], reader_id=self.request.user.id)
            messagepoll.read = True
            messagepoll.save()
        except ObjectDoesNotExist:
            pass
        context['can_read'] = line_can_read(self.kwargs['pk'], self.request.user.id)      
        return context
    
class UserDetail(LoginRequiredMixin, generic.DetailView):
    model = User
    
    def get_context_data(self, **kwargs):
        context = super(UserDetail, self).get_context_data(**kwargs)
        user = User.objects.get(id=self.kwargs['pk'])
        try:
            profile = Profile.objects.get(user=user)
        except ObjectDoesNotExist:
            profile = Profile(user=user)
            profile.save()
        context['profile'] = profile
        return context