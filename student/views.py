from django.shortcuts import render
from teacher.models import *
from student.models import *
from student.forms import EnrollForm
from django.views import generic
from django.contrib.auth.models import User, Group
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, RedirectView
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import IntegrityError
from django.contrib.auth.mixins import LoginRequiredMixin

class ClassroomList(generic.ListView):
    model = Classroom
    paginate_by = 3   
    template_name = 'student/classroom_list.html'
       
    def get_context_data(self, **kwargs):
        context = super(ClassroomList, self).get_context_data(**kwargs)
        queryset = []
        enrolls = Enroll.objects.filter(student_id=self.request.user.id)
        classroom_ids = list(map(lambda a: a.classroom_id, enrolls))        
        classroom_dict = dict((f.classroom_id, f) for f in enrolls)
        classrooms = Classroom.objects.filter(id__in=classroom_ids)
        for classroom in classrooms:
            queryset.append([classroom, classroom_dict[classroom.id]])
        context['queryset'] = queryset 
        return context 

class ClassroomJoinList(generic.ListView):
    model = Classroom
    template_name = 'student/classroom_join.html'    
    
    def get_context_data(self, **kwargs):
        context = super(ClassroomJoinList, self).get_context_data(**kwargs)
        queryset = []
        enrolls = Enroll.objects.filter(student_id=self.request.user.id)
        classroom_ids = list(map(lambda a: a.classroom_id, enrolls))        
        classrooms = Classroom.objects.all().order_by("-id")
        for classroom in classrooms:
            if classroom.id in classroom_ids:
                queryset.append([classroom, True])
            else:
                queryset.append([classroom, False])
        context['queryset'] = queryset 
        return context 

class ClassroomEnrollCreate(CreateView):
    model = Enroll
    form_class = EnrollForm    
    success_url = "/student/classroom"  
    template_name = "form.html"
    
    def form_valid(self, form):
        valid = super(ClassroomEnrollCreate, self).form_valid(form)
        if form.cleaned_data['password'] == Classroom.objects.get(id=self.kwargs['pk']).password:
            enrolls = Enroll.objects.filter(student_id=self.request.user.id, classroom_id=self.kwargs['pk'])
            if not enrolls.exists():
                enroll = Enroll(student_id=self.request.user.id, classroom_id=self.kwargs['pk'], seat=form.cleaned_data['seat'])
                enroll.save()
        return valid

class ClassmateList(generic.ListView):
    model = Enroll   
    template_name = 'student/classmate.html'
    
    def get_queryset(self):
        enrolls = Enroll.objects.filter(classroom_id=self.kwargs['pk']).order_by("seat")
        return enrolls    
      
class ClassroomSeatUpdate(UpdateView):
    model = Enroll
    fields = ['seat']
    success_url = "/student/classroom/"      
    template_name = "form.html"
    
# 列出組別
class GroupList(ListView):
    model = ClassroomGroup
    context_object_name = 'groups'
    paginate_by = 30
    template_name = 'student/group.html'
    
    def get_queryset(self):
        queryset = ClassroomGroup.objects.filter(classroom_id=self.kwargs['classroom_id']).order_by("-id")
        return queryset         			

    def get_context_data(self, **kwargs):
        context = super(GroupList, self).get_context_data(**kwargs)        
        context['classroom_id'] = self.kwargs['classroom_id']
        return context	    			
			
# 選組所有組別
class GroupPanel(ListView):
    model = ClassroomGroup
    context_object_name = 'groups'
    template_name = 'student/group_panel.html'
    
    def get_queryset(self):  
        group_id = self.kwargs['group_id']
        groups = []
        student_groups = {}
        enroll_list = []
        group_list = {}
        group_ids = []
        group = ClassroomGroup.objects.get(id=group_id)
        numbers = group.numbers
        enrolls = Enroll.objects.filter(classroom_id=group.classroom_id).order_by("seat")
        for enroll in enrolls:
            enroll_list.append(enroll.id)
        enroll_groups = StudentGroup.objects.filter(enroll_id__in=enroll_list, group_id=group_id)
        for enroll_group in enroll_groups:
            group_ids.append(enroll_group.enroll_id)
            group_list[enroll_group.enroll_id] = enroll_group.group
            enroll = Enroll.objects.get(id=enroll_group.enroll_id)
            if enroll_group.group in student_groups:
                student_groups[enroll_group.group].append(enroll)
            else:
                student_groups[enroll_group.group]=[enroll]	            
        for i in range(numbers):
            if i in student_groups:
                groups.append([i, student_groups[i]])
            else:
                groups.append([i, []])
					
        return groups


    def get_context_data(self, **kwargs):
        context = super(GroupPanel, self).get_context_data(**kwargs)        
        group_id = self.kwargs['group_id']
        group = ClassroomGroup.objects.get(id=group_id)   
        context['group'] = group
        enroll_user = Enroll.objects.get(student_id=self.request.user.id, classroom_id=group.classroom_id)        
        context['enroll_id'] = enroll_user.id
        student_groups = {}        
        group_list = {}        
        enroll_list = []        
        group_ids = []        
        enrolls = Enroll.objects.filter(classroom_id=group.classroom_id).order_by("seat")
        for enroll in enrolls:
            enroll_list.append(enroll.id)
        enroll_groups = StudentGroup.objects.filter(enroll_id__in=enroll_list, group_id=group_id)
        for enroll_group in enroll_groups:
            group_ids.append(enroll_group.enroll_id)
            group_list[enroll_group.enroll_id] = enroll_group.group
            enroll = Enroll.objects.get(id=enroll_group.enroll_id)
            if enroll_group.group in student_groups:
                student_groups[enroll_group.group].append(enroll)
            else:
                student_groups[enroll_group.group]=[enroll]	  
        #找出尚未分組的學生
        no_group = []
        for enroll in enrolls:
            if not enroll.id in group_ids:
                no_group.append([enroll.seat, enroll.student])
        context['student_groups'] = student_groups                
        context['no_group'] = no_group 
        context['classroom_id'] = group.classroom_id
        return context

#加入某一組
class GroupJoin(LoginRequiredMixin, RedirectView):

    def get(self, request, *args, **kwargs):
        group_id = self.kwargs['group_id'] 
        enroll_id = self.kwargs['enroll_id']
        number = self.kwargs['number']
        try:
            group = StudentGroup.objects.get(group_id=group_id, enroll_id=enroll_id)
            group.group = number
        except ObjectDoesNotExist:
            group = StudentGroup(group_id=group_id, enroll_id=enroll_id, group=number)
        if ClassroomGroup.objects.get(id=group_id).opening:
            group.save()	
        return super(GroupJoin, self).get(self, request, *args, **kwargs)        
        
    def get_redirect_url(self, *args, **kwargs):
        #TaxRate.objects.get(id=int(kwargs['pk'])).delete()   
        return '/student/group/panel/'+str(self.kwargs['group_id'])     

	