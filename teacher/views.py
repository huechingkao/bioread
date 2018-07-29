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
#from django.urls import reverse

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

