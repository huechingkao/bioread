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
from django.core.files.storage import FileSystemStorage
import os
from uuid import uuid4
from django.conf import settings
from wsgiref.util import FileWrapper
from io import StringIO
from shutil import copyfile
from django.http import HttpResponse
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
    model = Classroom
    fields = ["levels", "domains", "name", "password"]
    success_url = "/teacher/classroom"   
    template_name = 'teacher/classroom_form.html'
      
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.teacher_id = self.request.user.id
        self.object.domains = self.request.POST.getlist('domains')
        self.object.levels = self.request.POST.getlist('levels')	
        self.object.save()
        # 將教師設為0號學生
        enroll = Enroll(classroom_id=self.object.id, student_id=self.request.user.id, seat=0)
        enroll.save()   
        return redirect("/teacher/classroom")   
			
    def get_context_data(self, **kwargs):
        context = super(ClassroomCreate, self).get_context_data(**kwargs)
        context['domains'] = Domain.objects.all()
        context['levels'] = Level.objects.all()
        return context
    
class ClassroomUpdate(UpdateView):
    model = Classroom
    fields = ["levels", "domains", "name", "password"]
    success_url = "/teacher/classroom"   
    template_name = 'teacher/classroom_form.html'
    
    def get_context_data(self):
        context = super(ClassroomUpdate, self).get_context_data()
        context['domains'] = Domain.objects.all()
        context['levels'] = Level.objects.all()
        return context    
    
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
      
# 列出所有討論主題
class ForumListView(ListView):
    model = FWork
    context_object_name = 'forums'
    template_name = "teacher/forum_list.html"		
    paginate_by = 20
    def get_queryset(self):        
        fclasses = FClass.objects.filter(classroom_id=self.kwargs['classroom_id']).order_by("-publication_date", "-forum_id")
        forums = []
        for fclass in fclasses:
            forum = FWork.objects.get(id=fclass.forum_id)
            forums.append([forum, fclass])
        return forums
			
    def get_context_data(self, **kwargs):
        context = super(ForumListView, self).get_context_data(**kwargs)
        classroom = Classroom.objects.get(id=self.kwargs['classroom_id'])
        context['classroom'] = classroom
        return context	
        
#新增一個討論主題
class ForumCreateView(CreateView):
    model = FWork
    form_class = ForumForm
    template_name = "teacher/forum_form.html"
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.teacher_id = self.request.user.id
        self.object.classroom_id = self.kwargs['classroom_id']
        self.object.domains = self.request.POST.getlist('domains')
        self.object.levels = self.request.POST.getlist('levels')	        
        self.object.save()  
        classrooms = self.request.POST.getlist('classrooms')
        for classroom in classrooms:
          forum_class = FClass(forum_id=self.object.id, classroom_id=classroom)
          forum_class.save()
        
        return redirect("/teacher/forum/"+str(self.kwargs['classroom_id']))           
        
    def get_context_data(self, **kwargs):
        context = super(ForumCreateView, self).get_context_data(**kwargs)
        classroom_list = []
        classrooms = Classroom.objects.filter(teacher_id=self.request.user.id)
        for classroom in classrooms:
            classroom_list.append(classroom.id)
        assistants = Assistant.objects.filter(user_id=self.request.user.id)
        for assistant in assistants:
            if not assistant.classroom_id in classroom_list:
                classroom_list.append(assistant.classroom_id)
        classrooms = Classroom.objects.filter(id__in=classroom_list).order_by("-id")
        context['classrooms'] = classrooms
        context['classroom_id'] = int(self.kwargs['classroom_id'])
        context['classroom'] = Classroom.objects.get(id=self.kwargs['classroom_id'])
        context['domains'] = Domain.objects.all()
        context['levels'] = Level.objects.all()
        return context	
  
        return redirect("/teacher/forum/"+self.kwargs['classroom_id'])        
	
def forum_categroy(request, classroom_id, forum_id):
    forum = FWork.objects.get(id=forum_id)
    domains = Domain.objects.all()
    levels = Level.objects.all()		
    if request.method == 'POST':
        form = ForumCategroyForm(request.POST)
        if form.is_valid():
            forum.domains = request.POST.getlist('domains')
            forum.levels = request.POST.getlist('levels')	
            forum.save()
            return redirect('/teacher/forum/'+classroom_id+'/#'+str(forum.id))
    else:
        form = CategroyForm(instance=forum)
        
    return render_to_response('teacher/forum_categroy_form.html',{'domains': domains, 'levels':levels, 'classroom_id': classroom_id, 'forum':forum}, context_instance=RequestContext(request))

	
# 列出所有討論主題
class ForumAllListView(ListView):
    model = FWork
    context_object_name = 'forums'
    template_name = "teacher/forum_all.html"		
    paginate_by = 20
		
    def get_queryset(self):
      # 年級
      if self.kwargs['categroy'] == "1":
        queryset = FWork.objects.filter(levels__contains=self.kwargs['categroy_id']).order_by("-id")
      # 學習領域
      elif self.kwargs['categroy'] == "2":
        queryset = FWork.objects.filter(domains__contains=self.kwargs['categroy_id']).order_by("-id")   
      else:
        queryset = FWork.objects.all().order_by("-id")
      if self.request.GET.get('account') != None:
        keyword = self.request.GET.get('account')
        users = User.objects.filter(Q(username__icontains=keyword) | Q(first_name__icontains=keyword)).order_by('-id')
        user_list = []
        for user in users:
            user_list.append(user.id)
        forums = queryset.filter(teacher_id__in=user_list)
        return forums
      else:				
        return queryset
			
    def get_context_data(self, **kwargs):
        context = super(ForumAllListView, self).get_context_data(**kwargs)
        context['categroy'] = self.kwargs['categroy']							
        context['categroy_id'] = self.kwargs['categroy_id']							
        context['levels'] = Level.objects.all()				
        context['domains'] = Domain.objects.all()
        return context	

# 展示討論素材
def forum_show(request, forum_id):
    forum = FWork.objects.get(id=forum_id)
    domains = Domain.objects.all()
    domain_dict = {}
    for domain in domains :
        key = domain.id
        domain_dict[key] = domain
    levels = Level.objects.all()	
    level_dict = {}
    for level in levels :
        key = level.id
        level_dict[key] = level
    contents = FContent.objects.filter(forum_id=forum_id)
    domains = []		
    if forum.domains:
        forum_domains = ast.literal_eval(forum.domains)
        for domain in forum_domains:
            key = int(domain)
            domains.append(domain_dict[key])
    levels = []						
    if forum.levels:
        forum_levels = ast.literal_eval(forum.levels)
        for level in forum_levels:
            key = int(level)			
            levels.append(level_dict[key])
    return render_to_response('teacher/forum_show.html',{'domains':domains, 'levels':levels, 'contents':contents, 'forum':forum}, context_instance=RequestContext(request))

		
# 列出某討論主題的班級
class ForumClassList(ListView):
    model = FWork
    context_object_name = 'classrooms'
    template_name = "teacher/forum_class.html"		
    paginate_by = 20
	
    def get_queryset(self):        		
        fclass_dict = dict(((fclass.classroom_id, fclass) for fclass in FClass.objects.filter(forum_id=self.kwargs['forum_id'])))		
        classroom_list = []
        classroom_ids = []
        classrooms = Classroom.objects.filter(teacher_id=self.request.user.id).order_by("-id")
        for classroom in classrooms:
            if classroom.id in fclass_dict:
                classroom_list.append([classroom, True, fclass_dict[classroom.id].deadline, fclass_dict[classroom.id].deadline_date])
            else :
                classroom_list.append([classroom, False, False, timezone.now()])
            classroom_ids.append(classroom.id)
        assistants = Assistant.objects.filter(user_id=self.request.user.id)
        for assistant in assistants:
            classroom = Classroom.objects.get(id=assistant.classroom_id)
            if not classroom.id in classroom_ids:
                if classroom.id in fclass_dict:
                    classroom_list.append([classroom, True, fclass_dict[classroom.id].deadline, fclass_dict[classroom.id].deadline_date])
                else :
                    classroom_list.append([classroom, False, False, timezone.now()])
        return classroom_list
			
    def get_context_data(self, **kwargs):
        context = super(ForumClassList, self).get_context_data(**kwargs)				
        fwork = FWork.objects.get(id=self.kwargs['forum_id'])
        context['fwork'] = fwork
        context['forum_id'] = self.kwargs['forum_id']
        return context	
	
# Ajax 開放班取、關閉班級
def forum_switch(request):
    forum_id = request.POST.get('forumid')
    classroom_id = request.POST.get('classroomid')		
    status = request.POST.get('status')
    try:
        fwork = FClass.objects.get(forum_id=forum_id, classroom_id=classroom_id)
        if status == 'false' :
    	      fwork.delete()
    except ObjectDoesNotExist:
        if status == 'true':
            fwork = FClass(forum_id=forum_id, classroom_id=classroom_id)
            fwork.save()
    return JsonResponse({'status':status}, safe=False)        
	
# 列出某作業所有同學名單
def forum_class(request, classroom_id, work_id):
    enrolls = Enroll.objects.filter(classroom_id=classroom_id)
    classroom_name = Classroom.objects.get(id=classroom_id).name
    classmate_work = []
    scorer_name = ""
    for enroll in enrolls:
        try:    
            work = SWork.objects.get(student_id=enroll.student_id, index=work_id)
            if work.scorer > 0 :
                scorer = User.objects.get(id=work.scorer)
                scorer_name = scorer.first_name
            else :
                scorer_name = "1"
        except ObjectDoesNotExist:
            work = SWork(index=work_id, student_id=1)
        try:
            group_name = EnrollGroup.objects.get(id=enroll.group).name
        except ObjectDoesNotExist:
            group_name = "沒有組別"
        assistant = Assistant.objects.filter(classroom_id=classroom_id, student_id=enroll.student_id, lesson=work_id)
        if assistant.exists():
            classmate_work.append([enroll,work,1, scorer_name, group_name])
        else :
            classmate_work.append([enroll,work,0, scorer_name, group_name])   
    def getKey(custom):
        return custom[0].seat
	
    classmate_work = sorted(classmate_work, key=getKey)
   
    return render_to_response('teacher/twork_class.html',{'classmate_work': classmate_work, 'classroom_id':classroom_id, 'index': work_id}, context_instance=RequestContext(request))

# 列出所有討論主題素材
class ForumContentList(ListView):
    model = FContent
    context_object_name = 'contents'
    template_name = "teacher/forum_content.html"		
    def get_queryset(self):
        queryset = FContent.objects.filter(forum_id=self.kwargs['forum_id']).order_by("-id")
        return queryset
			
    def get_context_data(self, **kwargs):
        context = super(ForumContentList, self).get_context_data(**kwargs)
        fwork = FWork.objects.get(id=self.kwargs['forum_id'])
        fclasses = FClass.objects.filter(forum_id=self.kwargs['forum_id'])				
        context['fwork']= fwork
        context['forum_id'] = self.kwargs['forum_id']
        context['fclasses'] = fclasses
        return context	
			
#新增一個課程
class ForumContentCreate(CreateView):
    model = FContent
    form_class = ForumContentForm
    template_name = "teacher/forum_content_form.html"
    def form_valid(self, form):
        self.object = form.save(commit=False)
        work = FContent(forum_id=self.object.forum_id)
        if self.object.types == 1:
            work.types = 1
            work.title = self.object.title
            work.link = self.object.link
        if self.object.types  == 2:
            work.types = 2					
            work.youtube = self.object.youtube
        if self.object.types  == 3:
            work.types = 3
            myfile = self.request.FILES['content_file']
            fs = FileSystemStorage()
            filename = uuid4().hex
            work.title = myfile.name
            work.filename = str(self.request.user.id)+"/"+filename
            fs.save("static/upload/"+str(self.request.user.id)+"/"+filename, myfile)
        if self.object.types  == 4:
            work.types = 4
        work.memo = self.object.memo
        work.save()         
  
        return redirect("/teacher/forum/content/"+str(self.kwargs['forum_id']))

    def get_context_data(self, **kwargs):
        context = super(ForumContentCreate, self).get_context_data(**kwargs)
        context['forum'] = FWork.objects.get(id=self.kwargs['forum_id'])
        return context

def forum_delete(request, forum_id, content_id):
    instance = FContent.objects.get(id=content_id)
    instance.delete()

    return redirect("/teacher/forum/content/"+forum_id)  
	
def forum_edit(request, forum_id, content_id):
    try:
        instance = FContent.objects.get(id=content_id)
    except:
        pass
    if request.method == 'POST':
            content_id = request.POST.get("id", "")
            try:
                content = FContent.objects.get(id=content_id)
            except ObjectDoesNotExist:
	              content = FContent(forum_id= request.POST.get("forum_id", ""), types=form.cleaned_data['types'])
            if content.types == 1:
                content.title = request.POST.get("title", "")
                content.link = request.POST.get("link", "")
            elif content.types == 2:
                content.youtube = request.POST.get("youtube", "")
            elif content.types == 3:
                myfile =  request.FILES.get("content_file", "")
                fs = FileSystemStorage()
                filename = uuid4().hex
                content.title = myfile.name
                content.filename = str(request.user.id)+"/"+filename
                fs.save("static/upload/"+str(request.user.id)+"/"+filename, myfile)
            content.memo = request.POST.get("memo", "")
            content.save()
            return redirect('/teacher/forum/content/'+forum_id)   
    return render_to_response('teacher/forum_edit.html',{'content': instance, 'forum_id':forum_id, 'content_id':content_id}, context_instance=RequestContext(request))		
	
def forum_download(request, content_id):
    content = FContent.objects.get(id=content_id)
    filename = content.title
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))		
    download =  BASE_DIR + "/static/upload/" + content.filename
    wrapper = FileWrapper(open( download, "rb" ))
    response = HttpResponse(wrapper, content_type = 'application/force-download')
    #response = HttpResponse(content_type='application/force-download')
    response['Content-Disposition'] = 'attachment; filename={0}'.format(filename)
    # It's usually a good idea to set the 'Content-Length' header too.
    # You can also set any other required headers: Cache-Control, etc.
    return response
    #return render_to_response('student/download.html', {'download':download})
		
class ForumEditUpdate(UpdateView):
    model = FWork
    fields = ["levels", "domains", "title"]        
    template_name = 'teacher/forum_form.html'
    
    def get_success_url(self):
        succ_url =  '/teacher/forum/'+str(self.kwargs['classroom_id'])
        return succ_url       

    def get_context_data(self):
        context = super(ForumEditUpdate, self).get_context_data()        
        context['domains'] = Domain.objects.all()
        context['levels'] = Level.objects.all()
        context['classroom'] = Classroom.objects.get(id=self.kwargs['classroom_id'])        
        context['classroom_id'] =self.kwargs['classroom_id']
        context['classrooms'] = Classroom.objects.filter(teacher_id=self.request.user.id)
        return context        
      
  
def forum_export(request, classroom_id, forum_id):
	if not is_teacher(request.user, classroom_id):
		return redirect("/")
	classroom = Classroom.objects.get(id=classroom_id)
	try:
		fwork = FWork.objects.get(id=forum_id)
		enrolls = Enroll.objects.filter(classroom_id=classroom_id)
		datas = []
		contents = FContent.objects.filter(forum_id=forum_id).order_by("-id")
		fwork = FWork.objects.get(id=forum_id)
		works_pool = SFWork.objects.filter(index=forum_id).order_by("-id")
		reply_pool = SFReply.objects.filter(index=forum_id).order_by("-id")	
		file_pool = SFContent.objects.filter(index=forum_id, visible=True).order_by("-id")	
		for enroll in enrolls:
			works = filter(lambda w: w.student_id==enroll.student_id, works_pool)
			if len(works)>0:
				replys = filter(lambda w: w.work_id==works[0].id, reply_pool)
			else:
				replys = []
			files = filter(lambda w: w.student_id==enroll.student_id, file_pool)
			if enroll.seat > 0:
				datas.append([enroll, works, replys, files])
		def getKey(custom):
			return -custom[0].seat
		datas = sorted(datas, key=getKey, reverse=True)	
		#word
		document = Document()
		docx_title=u"討論區-" + classroom.name + "-"+ str(timezone.localtime(timezone.now()).date())+".docx"
		document.add_paragraph(request.user.first_name + u'的討論區作業')
		document.add_paragraph(u'主題：'+fwork.title)		
		document.add_paragraph(u"班級：" + classroom.name)		
		
		for enroll, works, replys, files in datas:
			user = User.objects.get(id=enroll.student_id)
			run = document.add_paragraph().add_run(str(enroll.seat)+")"+user.first_name)
			font = run.font
			font.color.rgb = RGBColor(0xFA, 0x24, 0x00)
			if len(works)>0:
				#p = document.add_paragraph(str(works[0].publication_date)[:19]+'\n'+works[0].memo)
				p = document.add_paragraph(str(localtime(works[0].publication_date))[:19]+'\n')
				# 將 memo 以時間標記為切割點，切分為一堆 tokens
				tokens = re.split('(\[m_\d+#\d+:\d+:\d+\])', works[0].memo)
				# 依續比對 token 格式
				for token in tokens:
					m = re.match('\[m_(\d+)#(\d+):(\d+):(\d+)\]', token)
					if m: # 若為時間標記，則插入連結
						vid = filter(lambda material: material.id == int(m.group(1)), contents)[0]
						add_hyperlink(document, p, vid.youtube+"&t="+m.group(2)+"h"+m.group(3)+"m"+m.group(4)+"s", "["+m.group(2)+":"+m.group(3)+":"+m.group(4)+"]")
					else: # 以一般文字插入
						p.add_run(token)
			if len(replys)>0:
				for reply in replys:
					user = User.objects.get(id=reply.user_id)
					run = document.add_paragraph().add_run(user.first_name+u'>'+str(localtime(reply.publication_date))[:19]+u'>留言:\n'+reply.memo)
					font = run.font
					font.color.rgb = RGBColor(0x42, 0x24, 0xE9)		
			if len(files)>0:
				for file in files:
					if file.visible:
						if file.title[-3:].upper() == "PNG" or file.title[-3:].upper() == "JPG":
							filename = 'static/upload/'+file.filename
							if os.path.exists(filename):
								copyfile(filename, 'static/upload/file.png')					
								document.add_picture('static/upload/file.png',width=Inches(6.0))
						else:
							p = document.add_paragraph()
							full_url = request.build_absolute_uri()
							index = full_url.find("/",9)
							url = full_url[:index] + "/student/forum/download/" + str(file.id) 
							add_hyperlink(document, p, url, file.title)
		# Prepare document for download        
		f = StringIO.StringIO()
		document.save(f)
		length = f.tell()
		f.seek(0)
		response = HttpResponse(
			f.getvalue(),
			content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
		)
		response['Content-Disposition'] = 'attachment; filename={0}'.format(docx_title.encode('utf8')) 
		response['Content-Length'] = length
		return response

	except ObjectDoesNotExist:
		pass
	return True

def add_hyperlink(document, paragraph, url, name):
    """
    Add a hyperlink to a paragraph.
    :param document: The Document being edited.
    :param paragraph: The Paragraph the hyperlink is being added to.
    :param url: The url to be added to the link.
    :param name: The text for the link to be displayed in the paragraph
    :return: None
    """

    part = document.part
    rId = part.relate_to(url, RT.HYPERLINK, is_external=True)

    init_hyper = OxmlElement('w:hyperlink')
    init_hyper.set(qn('r:id'), rId, )
    init_hyper.set(qn('w:history'), '1')

    new_run = OxmlElement('w:r')

    rPr = OxmlElement('w:rPr')

    rStyle = OxmlElement('w:rStyle')
    rStyle.set(qn('w:val'), 'Hyperlink')

    rPr.append(rStyle)
    new_run.append(rPr)
    new_run.text = name
    init_hyper.append(new_run)

    r = paragraph.add_run()
    r._r.append(init_hyper)
    r.font.color.theme_color = MSO_THEME_COLOR_INDEX.HYPERLINK
    r.font.underline = True

    return None

def forum_grade(request, classroom_id, action):
	classroom = Classroom.objects.get(id=classroom_id)
	forum_ids = []
	forums = []
	fclasses = FClass.objects.filter(classroom_id=classroom_id).order_by("publication_date", "forum_id")
	for fclass in fclasses:
		forum_ids.append(fclass.forum_id)
		forum = FWork.objects.get(id=fclass.forum_id)
		forums.append(forum.title)
	enrolls = Enroll.objects.filter(classroom_id=classroom_id).order_by("seat")
	datas = {}
	for enroll in enrolls:
			sfworks = SFWork.objects.filter(index__in=forum_ids, student_id=enroll.student_id).order_by("id")
			if len(sfworks) > 0:
				for fclass in fclasses:
						works = filter(lambda w: w.index==fclass.forum_id, sfworks)
						if enroll.student_id in datas:
							if len(works) > 0 :
								datas[enroll.student_id].append(works[0])
							else :
								datas[enroll.student_id].append(SFWork())
						else:
							if len(works) > 0:
								datas[enroll.student_id] = [works[0]]
							else :
								datas[enroll.student_id] = [SFWork()]
			else :
				datas[enroll.student_id] = [SFWork()]
	results = []
	for enroll in enrolls:
		student_name = User.objects.get(id=enroll.student_id).first_name
		results.append([enroll, student_name, datas[enroll.student_id]])
	
	#下載Excel
	if action == "1":
		classroom = Classroom.objects.get(id=classroom_id)       
		output = StringIO.StringIO()
		workbook = xlsxwriter.Workbook(output)    
		worksheet = workbook.add_worksheet(classroom.name)
		date_format = workbook.add_format({'num_format': 'yy/mm/dd'})
		
		row = 1
		worksheet.write(row, 1, u'座號')
		worksheet.write(row, 2, u'姓名')
		index = 3
		for forum in forums:
			worksheet.write(row, index, forum)
			index += 1
		
		row += 1
		index = 3
		for fclass in fclasses:
			worksheet.write(row, index, datetime.strptime(str(fclass.publication_date)[:19],'%Y-%m-%d %H:%M:%S'), date_format)
			index += 1			

		for enroll, student_name, works in results:
			row += 1
			worksheet.write(row, 1, enroll.seat)
			worksheet.write(row, 2, student_name)
			index = 3
			for work in works:
				if work.id:
					worksheet.write(row, index, work.score)
				else:
					worksheet.write(row, index, '')
				index +=1 

		workbook.close()
		# xlsx_data contains the Excel file
		response = HttpResponse(content_type='application/vnd.ms-excel')
		filename = classroom.name + '-' + str(localtime(timezone.now()).date()) + '.xlsx'
		response['Content-Disposition'] = 'attachment; filename={0}'.format(filename.encode('utf8'))
		xlsx_data = output.getvalue()
		response.write(xlsx_data)
		return response
	else :
		return render_to_response('teacher/forum_grade.html',{'results':results, 'forums':forums, 'classroom_id':classroom_id, 'fclasses':fclasses}, context_instance=RequestContext(request))

class ForumDeadlineUpdate(UpdateView):
    model = FWork
    fields = ['title']
    template_name = "teacher/forum_deadline_form.html"		   
	
    def form_valid(self, form):
        if is_teacher(self.request.user, self.kwargs['classroom_id']) or is_assistant(self.request.user, self.kwargs['classroom_id']):
            #fclass = .objects.get(id=self.kwargs['pk'])
            reduce = group.numbers - form.cleaned_data['numbers']
            if reduce > 0:
                for i in range(reduce):
                    StudentGroup.objects.filter(group_id=self.kwargs['pk'], group=group.numbers-i).delete()
            form.save()
        return HttpResponseRedirect(self.get_success_url())   
      
    def get_context_data(self):
        context = super(ForumDeadlineUpdate, self).get_context_data()
        classroom_id = self.kwargs['classroom_id']
        forum_id = self.kwargs['pk']
        context['domains'] = Domain.objects.all()
        context['levels'] = Level.objects.all()
        context['classroom_id'] = classroom_id
        context['fclass'] = FClass.objects.get(classroom_id=classroom_id, forum_id=forum_id)
        context['fclasses'] = FClass.objects.filter(forum_id=forum_id)
        return context    

	
# Ajax 設定期限、取消期限
def forum_deadline_set(request):
    forum_id = request.POST.get('forumid')
    classroom_id = request.POST.get('classroomid')		
    status = request.POST.get('status')
    try:
        fclass = FClass.objects.get(forum_id=forum_id, classroom_id=classroom_id)
    except ObjectDoesNotExist:
        fclass = Fclass(forum_id=forum_id, classroom_id=classroom_id)
    if status == 'True':
        fclass.deadline = True
    else :
        fclass.deadline = False
    fclass.save()
    return JsonResponse({'status':status}, safe=False)        

# Ajax 設定期限日期
def forum_deadline_date(request):
    forum_id = request.POST.get('forumid')
    classroom_id = request.POST.get('classroomid')		
    deadline_date = request.POST.get('deadlinedate')
    try:
        fclass = FClass.objects.get(forum_id=forum_id, classroom_id=classroom_id)
    except ObjectDoesNotExist:
        fclass = FClass(forum_id=forum_id, classroom_id=classroom_id)
    #fclass.deadline_date = deadline_date.strftime('%d/%m/%Y')
    fclass.deadline_date = datetime.strptime(deadline_date, '%Y/%m/%d %H:%M')
    fclass.save()
    return JsonResponse({'status':deadline_date}, safe=False)             
        
#新增一個公告
class AnnounceCreateView(CreateView):
    model = Message
    form_class = AnnounceForm
    template_name = 'teacher/announce_form.html'     
    def form_valid(self, form):
        self.object = form.save(commit=False)			
        classrooms = self.request.POST.getlist('classrooms')
        files = []
        if self.request.FILES.getlist('files'):
             for file in self.request.FILES.getlist('files'):
                fs = FileSystemStorage()
                filename = uuid4().hex							
                fs.save("static/upload/"+str(self.request.user.id)+"/"+filename, file)								
                files.append([filename, file.name])		
        for classroom_id in classrooms:
            message = Message()
            message.title = u"[公告]" + self.request.user.first_name + ":" + self.object.title
            message.author_id = self.request.user.id	
            message.type = 1 #公告
            message.classroom_id = classroom_id
            message.content = self.object.content
            message.save()
            message.url = "/account/line/detail/" + classroom_id + "/" + str(message.id)
            message.save()
            if files:
                for file, name in files:
                    content = MessageContent()
                    content.title = name
                    content.message_id = message.id
                    content.filename = str(self.request.user.id)+"/"+file
                    content.save()		

            # 班級學生訊息
            enrolls = Enroll.objects.filter(classroom_id=classroom_id)
            for enroll in enrolls:
                messagepoll = MessagePoll(message_type=1, message_id=message.id, reader_id=enroll.student_id, classroom_id=classroom_id)
                messagepoll.save()               
        return redirect("/student/announce/"+self.kwargs['classroom_id']) 
			
    def get_context_data(self, **kwargs):
        context = super(AnnounceCreateView, self).get_context_data(**kwargs)
        context['class'] = Classroom.objects.get(id=self.kwargs['classroom_id'])
        classroom_list = []
        classrooms = Classroom.objects.filter(teacher_id=self.request.user.id)
        for classroom in classrooms:
            classroom_list.append(classroom.id)
        assistants = Assistant.objects.filter(user_id=self.request.user.id)
        for assistant in assistants:
            if not assistant.classroom_id in classroom_list:
                classroom_list.append(assistant.classroom_id)
        classrooms = Classroom.objects.filter(id__in=classroom_list).order_by("-id")
        context['classrooms'] = classrooms
        return context	   
        
    # 限本班任課教師        
    def render_to_response(self, context):
        if not is_teacher(self.request.user, self.kwargs['classroom_id']):
            if not is_assistant(self.request.user, self.kwargs['classroom_id']) :
                return redirect('/')
        return super(AnnounceCreateView, self).render_to_response(context)        
			