# -*- coding: utf8 -*-
from django.shortcuts import render
from django.views import generic
from django.contrib.auth.models import User, Group
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.http import is_safe_url
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login, logout as auth_logout
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import FormView, RedirectView
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from .forms import UserRegistrationForm, UserUpdateForm, UserPasswordForm, UserTeacherForm

class Login(FormView):
    success_url = '/'
    form_class = AuthenticationForm
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
        auth_login(self.request, form.get_user())
        if form.get_user().id == 1 and form.get_user().first_name == "":
            user = User.objects.get(id=1)
            user.first_name = "管理員"
            user.save()
          
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
    template_name = 'form.html'
      
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