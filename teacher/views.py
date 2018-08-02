from django.shortcuts import render
from teacher.models import *
from student.models import *
from account.models import *
from account.forms import LineForm
from teacher.forms import *
from django.views import generic
from django.contrib.auth.models import User, Group
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, View, RedirectView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
import django_excel as excel
from django.http import JsonResponse
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

#from django.urls import reverse

# 判斷是否為授課教師
def is_teacher(user, classroom_id):
    return user.groups.filter(name='teacher').exists() and Classroom.objects.filter(teacher_id=user.id, id=classroom_id).exists()

def is_assistant(user, classroom_id):
    assistants = Assistant.objects.filter(classroom_id=classroom_id, user_id=user.id)
    if len(assistants)>0 :
        return True
    return False	

class ClassroomList(generic.ListView):
    model = Classroom
    ordering = ['-id']
    paginate_by = 3   
    
class ClassroomCreate(CreateView):
    model =Classroom
    fields = ["name", "password"]
    success_url = "/teacher/classroom"   
    template_name = 'form.html'
      
    def form_valid(self, form):
        valid = super(ClassroomCreate, self).form_valid(form)
        classroom = form.save(commit=False)
        classroom.teacher_id = self.request.user.id
        classroom.save() 
        enroll = Enroll(classroom_id=classroom.id, student_id=classroom.teacher_id, seat=0)
        enroll.save()
        return valid
    
class ClassroomUpdate(UpdateView):
    model = Classroom
    fields = ["name", "password"]
    success_url = "/teacher/classroom"   
    template_name = 'form.html'
    
#新增一個公告
class AnnounceCreate(LoginRequiredMixin, CreateView):
    model = Message
    form_class = LineForm
    success_url = '/account/dashboard/0'    
    template_name = 'teacher/announce_form.html'     

    def form_valid(self, form):
        valid = super(AnnounceCreate, self).form_valid(form)
        self.object = form.save(commit=False)
        classroom = Classroom.objects.get(id=self.kwargs['classroom_id'])
        self.object.title = u"[公告]" + classroom.name + ":" + self.object.title
        self.object.author_id = self.request.user.id
        self.object.save()
        # 訊息
        enrolls = Enroll.objects.filter(classroom_id=self.kwargs['classroom_id'])
        for enroll in enrolls :
            messagepoll = MessagePoll(message_id=self.object.id, reader_id=enroll.student_id)
            messagepoll.save()              
        return valid
      
    # 限本班教師
    def render_to_response(self, context):
        teacher_id = Classroom.objects.get(id=self.kwargs['classroom_id']).teacher_id
        if not teacher_id == self.request.user.id:
            return redirect('/')
        return super(AnnounceCreate, self).render_to_response(context)       
      
    def get_context_data(self, **kwargs):
        context = super(AnnounceCreate, self).get_context_data(**kwargs)
        context['classroom'] = Classroom.objects.get(id=self.kwargs['classroom_id'])
        return context	
      
# 教師可以查看所有帳號
class StudentList(ListView):
    context_object_name = 'users'
    paginate_by = 50
    template_name = 'teacher/student_list.html'

    def get_queryset(self):
        username = username__icontains=self.request.user.username+"_"
        if self.request.GET.get('account') != None:
            keyword = self.request.GET.get('account')
            queryset = User.objects.filter(Q(username__icontains=username+keyword) | (Q(first_name__icontains=keyword) & Q(username__icontains=username))).order_by('-id')
        else :
            queryset = User.objects.filter(username__icontains=username).order_by('-id')
        return queryset

    def get_context_data(self, **kwargs):
        context = super(StudentList, self).get_context_data(**kwargs)
        account = self.request.GET.get('account')
        context.update({'account': account})
        return context
      
#匯入帳號檔案
class StudentUpload(View):
    form_class = UploadFileForm
    success_url = 'import_student'
    template_name = 'teacher/student_upload.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            ImportUser.objects.all().delete()
            request.FILES['file'].save_to_database(
                name_columns_by_row=0,
                model=ImportUser,
                mapdict=['username', 'first_name', 'password'])
            users = ImportUser.objects.all()
            return render(self.request, 'teacher/student_import.html',{'users':users})
        else:
            return HttpResponseBadRequest()
          
#建立學生帳號
class StudentImport(LoginRequiredMixin, RedirectView):

    def get(self, request, *args, **kwargs):
        users = ImportUser.objects.all()
        username_list = [request.user.username+"_"+user.username for user in users]
        exist_users = [user.username for user in User.objects.filter(username__in=username_list)]
        create_list = []
        for user in users:
            username = request.user.username+"_"+user.username
            if username in exist_users:
                continue
            new_user = User(username=username, first_name=user.first_name, last_name=request.user.last_name, password=user.password, email=username+"@edu.tw")
            new_user.set_password(user.password)
            create_list.append(new_user)

        User.objects.bulk_create(create_list)
        new_users = User.objects.filter(username__in=[user.username for user in create_list])

        profile_list = []
        message_list = []
        poll_list = []
        title = "請洽詢任課教師課程名稱及選課密碼"
        url = "/student/classroom/add"
        message = Message(title=title, url=url, time=timezone.now())
        message.save()
        for user in new_users:
            profile = Profile(user=user)
            profile_list.append(profile)
            poll = MessagePoll(message_id=message.id, reader_id=user.id)
            poll_list.append(poll)

        Profile.objects.bulk_create(profile_list)
        MessagePoll.objects.bulk_create(poll_list)
        return super(StudentImport, self).get(self, request, *args, **kwargs)        
        
    def get_redirect_url(self, *args, **kwargs):
        #TaxRate.objects.get(id=int(kwargs['pk'])).delete()   
        return '/teacher/student/list'

# 列出所有課程
class GroupList(ListView):
    model = Group
    context_object_name = 'groups'
    template_name = 'teacher/group.html'
    paginate_by = 25
    def get_queryset(self):      
        queryset = ClassroomGroup.objects.filter(classroom_id=self.kwargs['classroom_id']).order_by("-id")
        return queryset
			
    def get_context_data(self, **kwargs):
        context = super(GroupList, self).get_context_data(**kwargs)
        context['classroom_id'] = self.kwargs['classroom_id']
        return context				
			
#新增一個分組
class GroupCreate(CreateView):
    model = ClassroomGroup
    form_class = GroupForm
    template_name = 'teacher/group_form.html'    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.classroom_id = self.kwargs['classroom_id']
        if is_teacher(self.request.user, self.kwargs['classroom_id']) or is_assistant(self.request.user, self.kwargs['classroom_id']):
            self.object.save()
            # 隨機分組
            if form.cleaned_data['assign'] == 1:
                enrolls = Enroll.objects.filter(classroom_id=self.kwargs['classroom_id'], seat__gt=0).order_by('?')
                number = 0
                for enroll in enrolls:
                    group = StudentGroup(group_id=self.object.id, enroll_id=enroll.id, group=(number % self.object.numbers))
                    group.save()
                    number += 1
                self.object.opening=False
                self.object.save()
                
        return redirect("/student/group/panel/"+ str(self.object.id))   
			
    def get_context_data(self, **kwargs):
        context = super(GroupCreate, self).get_context_data(**kwargs)
        return context	
			
class GroupUpdate(UpdateView):
    model = ClassroomGroup
    form_class = GroupForm2		
    template_name = 'form.html'
    def get_success_url(self):
        succ_url =  '/student/group/list/'+self.kwargs['pk']
        return succ_url
			
    def form_valid(self, form):
        if is_teacher(self.request.user, self.kwargs['classroom_id']) or is_assistant(self.request.user, self.kwargs['classroom_id']):
            group = ClassroomGroup.objects.get(id=self.kwargs['pk'])
            reduce = group.numbers - form.cleaned_data['numbers']
            if reduce > 0:
                for i in range(reduce):
                    StudentGroup.objects.filter(group_id=self.kwargs['pk'], group=group.numbers-i).delete()
            form.save()
        return HttpResponseRedirect(self.get_success_url())
			

# 分組
def make(request):
    group_id = request.POST.get('groupid')
    action = request.POST.get('action')
    if group_id and action :      
        group = ClassroomGroup.objects.get(id=group_id)	
        if is_teacher(request.user, group.classroom_id) or is_assistant(request.user, group.classroom_id):
            if action == 'open':            
                group.opening = True   
            else : 
                group.opening = False
            group.save()      
        return JsonResponse({'status':'ok'}, safe=False)
    else:
        return JsonResponse({'status':'fail'}, safe=False) 
			
# 分組
def make2(request, group_id, action):
        group = ClassroomGroup.objects.get(id=group_id)	
        if is_teacher(request.user, group.classroom_id) or is_assistant(request.user, group.classroom_id):
            if action == 1:            
                group.opening = True   
            else : 
                group.opening = False
            group.save()      
        return redirect("/student/group/panel/"+str(group.id))
			
# 列出某班級助教
class ClassroomAssistant(ListView):
    context_object_name = 'assistants'
    template_name = 'teacher/assistant.html'
    
    def get_queryset(self):         
        classroom_id = self.kwargs['classroom_id']
        # 限本班任課教師
        if not is_teacher(self.request.user, classroom_id):
           return redirect("/")
        assistants = Assistant.objects.filter(classroom_id=classroom_id).order_by("-id")
        return assistants
      
    def get_context_data(self, **kwargs):
        context = super(ClassroomAssistant, self).get_context_data(**kwargs)
        context['classroom'] = Classroom.objects.get(id=self.kwargs['classroom_id'])
        return context	      

# 教師可以查看所有帳號
class AssistantList(ListView):
    context_object_name = 'users'
    paginate_by = 20
    template_name = 'teacher/assistant_user.html'
    
    def get_queryset(self):        
        if self.request.GET.get('account') != None:
            keyword = self.request.GET.get('account')
            queryset = User.objects.filter(Q(groups__name='apply'), Q(username__icontains=keyword) | Q(first_name__icontains=keyword)).order_by('-id')
        else :
            queryset = User.objects.filter(groups__name='apply').order_by('-id')				
        return queryset

    def get_context_data(self, **kwargs):
        context = super(AssistantList, self).get_context_data(**kwargs)
        context['classroom'] = Classroom.objects.get(id=self.kwargs['classroom_id'])
        assistant_list = []
        assistants = Assistant.objects.filter(classroom_id=self.kwargs['classroom_id'])
        for assistant in assistants:
            assistant_list.append(assistant.user_id)
        context['assistants'] = assistant_list
        return context	

# 列出所有助教課程
class AssistantClassroomList(ListView):
    model = Classroom
    context_object_name = 'classrooms'
    template_name = 'teacher/assistant_list.html'
    paginate_by = 20
    def get_queryset(self):      
        assistants = Assistant.objects.filter(user_id=self.request.user.id)
        classroom_list = []
        for assistant in assistants:
            classroom_list.append(assistant.classroom_id)
        queryset = Classroom.objects.filter(id__in=classroom_list).order_by("-id")
        return queryset
            
# Ajax 設為助教、取消助教
def assistant_make(request):
    classroom_id = request.POST.get('classroomid')	
    user_id = request.POST.get('userid')
    action = request.POST.get('action')
    if user_id and action :
        if action == 'set':            
            try :
                assistant = Assistant.objects.get(classroom_id=classroom_id, user_id=user_id) 	
            except ObjectDoesNotExist :
                assistant = Assistant(classroom_id=classroom_id, user_id=user_id) 
                assistant.save()
            # 將教師設為0號學生
            enroll = Enroll(classroom_id=classroom_id, student_id=user_id, seat=0)
            enroll.save() 
        else : 
            try :
                assistant = Assistant.objects.get(classroom_id=classroom_id, user_id=user_id)
                assistant.delete()
                enroll = Enroll.objects.filter(classroom_id=classroom_id, student_id=user_id)
                enroll.delete()								
            except ObjectDoesNotExist :
                pass             
        return JsonResponse({'status':'ok'}, safe=False)
    else:
        return JsonResponse({'status':'fail'}, safe=False)
	