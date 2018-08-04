from django.shortcuts import render, redirect
from account.avatar import *
from account.models import *
from teacher.models import *
from student.models import *
from student.forms import *
from django.views import generic
from django.contrib.auth.models import User, Group
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, RedirectView, TemplateView
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import IntegrityError
from django.contrib.auth.mixins import LoginRequiredMixin
from uuid import uuid4
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from wsgiref.util import FileWrapper
from django.http import HttpResponse
from django.http import JsonResponse
import json

def is_classmate(student_id, user_id):
    enrolls = Enroll.objects.filter(student_id=student_id)
    for enroll in enrolls:
        classroom = Classroom.objects.get(id=enroll.classroom_id)
        enrolls2 = Enroll.objects.filter(classroom_id=classroom.id)
        for enroll2 in enrolls2:
            if user_id == enroll2.student_id:
                return True
    return False
  
def in_classroom(classroom_id, user_id):
    enrolls = Enroll.objects.filter(classroom_id=classroom_id)
    for enroll in enrolls:
        if user_id == enroll.student_id:
            return True
    return False	
  
def is_teacher(classroom_id, user_id):
    classroom = Classroom.objects.get(id=classroom_id)
    if user_id == classroom.teacher_id:
        return True
    return False
	
def is_assistant(classroom_id, user_id):
    assistants = Assistant.objects.filter(classroom_id=classroom_id, user_id=user_id)
    if len(assistants)>0 :
        return True
    return False  

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

# 列出所有討論主題
class ForumList(ListView):
    model = SFWork
    context_object_name = 'works'
    template_name = 'student/forum_list.html'    
    
    def get_queryset(self):
        queryset = []
        fclass_dict = dict(((fclass.forum_id, fclass) for fclass in FClass.objects.filter(classroom_id=self.kwargs['classroom_id'])))	
        #fclasses = FClass.objects.filter(classroom_id=self.kwargs['classroom_id']).order_by("-id")
        fworks = FWork.objects.filter(id__in=fclass_dict.keys()).order_by("-id")
        sfwork_pool = SFWork.objects.filter(student_id=self.request.user.id).order_by("-id")
        for fwork in fworks:
            sfworks = list(filter(lambda w: w.index==fwork.id, sfwork_pool))
            if len(sfworks)> 0 :
                queryset.append([fwork, sfworks[0].publish, fclass_dict[fwork.id], len(sfworks)])
            else :
                queryset.append([fwork, False, fclass_dict[fwork.id], 0])
        def getKey(custom):
            return custom[2].publication_date, custom[2].forum_id
        queryset = sorted(queryset, key=getKey, reverse=True)	
        return queryset
        
    def get_context_data(self, **kwargs):
        context = super(ForumList, self).get_context_data(**kwargs)
        context['classroom_id'] = self.kwargs['classroom_id']
        context['bookmark'] =  self.kwargs['bookmark']
        context['fclasses'] = dict(((fclass.forum_id, fclass) for fclass in FClass.objects.filter(classroom_id=self.kwargs['classroom_id'])))
        return context	    

    # 限本班同學
    def render_to_response(self, context):
        try:
            enroll = Enroll.objects.get(student_id=self.request.user.id, classroom_id=self.kwargs['classroom_id'])
        except ObjectDoesNotExist :
            return redirect('/')
        return super(ForumList, self).render_to_response(context)    

class ForumPublish(TemplateView):
    template_name = "student/forum_publish.html"

class ForumPublishDone(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
      index = self.kwargs['index']
      classroom_id = self.kwargs['classroom_id']
      user_id = self.request.user.id
      try:
          fwork = FWork.objects.get(id=index)
          works = SFWork.objects.filter(index=index, student_id=user_id).order_by("-id")
          work = works[0]
          work.publish = True
          work.save()
          if len(works) == 1:
            update_avatar(self.request.user.id, 1, 2)
            # History
            history = PointHistory(user_id=self.request.user.id, kind=1, message=u'2分--繳交討論區作業<'+fwork.title+'>', url='/student/forum/memo/'+classroom_id+'/'+index+'/'+action)
            history.save()								
      except ObjectDoesNotExist:
            pass
      return "/student/forum/memo/"+str(classroom_id)+"/"+str(index)+"/0"
  
	
class ForumSubmit(CreateView):
    model = SFWork
    form_class = ForumSubmitForm    
    template_name = "student/forum_form.html"
    
    def form_valid(self, form):
        valid = super(ForumSubmit, self).form_valid(form)
        index = self.kwargs['index']
        user_id = self.request.user.id
        work = SFWork(index=index, student_id=user_id, publish=False)
        work.memo = form.cleaned_data['memo']
        work.memo_e = form.cleaned_data['memo_e']
        work.memo_c = form.cleaned_data['memo_c']								
        work.save()
        if self.request.FILES:
            content = SFContent(index=index, student_id=user_id)
            myfile =  self.request.FILES.get("file", "")
            fs = FileSystemStorage()
            filename = uuid4().hex
            content.title = myfile.name
            content.work_id = work.id
            content.filename = str(user_id)+"/"+filename
            fs.save("static/upload/"+str(user_id)+"/"+filename, myfile)
            content.save()
        return valid
            
    def get_success_url(self):
        index = self.kwargs['index']
        user_id = self.request.user.id
        classroom_id = self.kwargs['classroom_id']
        works = SFWork.objects.filter(index=index, student_id=user_id).order_by("-id")        
        if not works:
            succ_url = "/student/forum/publish/"+str(classroom_id)+"/"+str(index)	
        elif not works[0].publish:
            succ_url = "/student/forum/publish/"+str(classroom_id)+"/"+str(index)
        else :
            succ_url = "/student/forum/memo/"+str(classroom_id)+"/"+str(index)+"/0"
        return succ_url            

    def get_context_data(self, **kwargs):
        context = super(ForumSubmit, self).get_context_data(**kwargs)
        index = self.kwargs['index']
        classroom_id = self.kwargs['classroom_id']
        user_id = self.request.user.id
        context['classroom_id'] = classroom_id
        context['subject'] =  FWork.objects.get(id=index).title
        context['files'] = SFContent.objects.filter(index=index, student_id=user_id,visible=True).order_by("-id")
        context['index'] = index
        context['fwork'] = FWork.objects.get(id=index)
        works = SFWork.objects.filter(index=index, student_id=user_id).order_by("-id")
        if not works.exists():
            work = SFWork(index=0, publish=False)
        else:
            work = works[0]
        context['works'] = works
        context['work'] = work
        context['scores'] = []
        context['contents'] = FContent.objects.filter(forum_id=index).order_by("id")
        return context	           

class ForumShow(ListView):
  	model = FContent
  	context_object_name = 'contents'
  	template_name = 'student/forum_show.html'    
    
  	def get_queryset(self): 
  		contents = FContent.objects.filter(forum_id=self.kwargs['index']).order_by("id")
  		return contents
    
  	def get_context_data(self, **kwargs):
  		context = super(ForumShow, self).get_context_data(**kwargs)      
  		index = self.kwargs['index']
  		user_id = self.kwargs['user_id']
  		classroom_id = self.kwargs['classroom_id']
  		forum = FWork.objects.get(id=index)
  		teacher_id = forum.teacher_id
  		work = []
  		replys = []
  		files = []
  		works = SFWork.objects.filter(index=index, student_id=user_id).order_by("-id")
	  	publish = False
  		if len(works)> 0:
  			work_new = works[0]
  			work_first = works.last()
  			publish = work_first.publish
  			replys = SFReply.objects.filter(index=index, work_id=work_first.id).order_by("-id")	
  			files = SFContent.objects.filter(index=index, student_id=user_id, visible=True).order_by("-id")	
  		else :
  			work_new = SFWork(index=index, student_id=user_id)
  			work_first = SFWork(index=index, student_id=user_id)			
  		context['work_new'] = work_new
  		context['work_first'] = work_first
  		context['publish'] = publish
  		context['classroom_id'] = classroom_id
  		context['replys'] = replys
  		context['files'] = files
  		context['forum'] = forum
  		context['user_id'] = user_id
  		context['teacher_id'] = teacher_id
  		context['works'] = works
  		context['is_teacher'] = is_teacher(classroom_id, self.request.user.id)
  		return context

    # 限本班同學
  	def render_to_response(self, context):
  		try:
  		  enroll = Enroll.objects.get(student_id=self.request.user.id, classroom_id=self.kwargs['classroom_id'])
  		except ObjectDoesNotExist :
  		  return redirect('/')
  		return super(ForumShow, self).render_to_response(context)      
    
 # 查詢某作業所有同學心得
class ForumMemo(ListView):
    model = SFWork
    context_object_name = 'contents'
    template_name = 'student/forum_memo.html'    
    
    def get_queryset(self): 
        index = self.kwargs['index']
        contents = FContent.objects.filter(forum_id=index).order_by("-id")
        return contents
    
    def get_context_data(self, **kwargs):
      index = self.kwargs['index']
      classroom_id = self.kwargs['classroom_id']
      user_id = self.request.user.id
      action = self.kwargs['action']
      context = super(ForumMemo, self).get_context_data(**kwargs)        
      enrolls = Enroll.objects.filter(classroom_id=classroom_id)
      datas = []
      fwork = FWork.objects.get(id=index)
      teacher_id = fwork.teacher_id
      subject = fwork.title
      if action == "2":
      	works_pool = SFWork.objects.filter(index=index, score=5).order_by("-id")
      else:
        # 一次取得所有 SFWork	
        works_pool = SFWork.objects.filter(index=index).order_by("-id", "publish")
      reply_pool = SFReply.objects.filter(index=index).order_by("-id")	
      file_pool = SFContent.objects.filter(index=index, visible=True).order_by("-id")	
      for enroll in enrolls:
      	works = list(filter(lambda w: w.student_id==enroll.student_id, works_pool))
      	# 對未作答學生不特別處理，因為 filter 會傳回 []
      	if len(works)>0:
      	  replys = list(filter(lambda w: w.work_id==works[-1].id, reply_pool))
      	  files = list(filter(lambda w: w.student_id==enroll.student_id, file_pool))
      	  if action == 2 :
            if works[-1].score == 5:
      	      datas.append([enroll, works, replys, files])
      	  else :
      	    datas.append([enroll, works, replys, files])
      	else :
      	  replys = []
      	  if not action == 2 :
            files = filter(lambda w: w.student_id==enroll.student_id, file_pool)		
            datas.append([enroll, works, replys, files])
            
      def getKey(custom):
        if custom[1]:
          if action == 3:
            return custom[1][-1].like_count
          elif action == 2:
            return custom[1][-1].score, custom[1][0].publication_date		
          elif action == 1:
             return -custom[0].seat
          else :
             return custom[1][0].reply_date, -custom[0].seat			
        else:
          return -custom[0].seat
      datas = sorted(datas, key=getKey, reverse=True)	            
      context['action'] = action
      context['replys'] = replys
      context['datas'] = datas
      context['teacher_id'] = teacher_id
      context['subject'] = subject
      context['classroom_id'] = classroom_id
      context['index'] = index
      context['is_teacher'] = is_teacher(classroom_id, user_id)
      return context

class ForumHistory(generic.ListView):
    model = SFWork
    template_name = 'student/forum_hitory.html'
       
    def get_context_data(self, **kwargs):
        context = super(ForumHistory, self).get_context_data(**kwargs)
        index = self.kwargs['index']
        classroom_id = self.kwargs['classroom_id']
        user_id = self.kwargs['user_id']
        work = []
        contents = FContent.objects.filter(forum_id=index).order_by("-id")
        works = SFWork.objects.filter(index=index, student_id=user_id).order_by("-id")
        files = SFContent.objects.filter(index=index, student_id=user_id).order_by("-id")
        forum = FWork.objects.get(id=index)
        context['forum'] = forum
        context['classroom_id'] = classroom_id
        context['works'] = works
        context['contents'] = contents
        context['files'] = files
        context['index'] = index
        if len(works)> 0 :
            if works[0].publish or user_id==str(request.user.id) or is_teacher(classroom_id, self.request.user.id):
              return context
        return redirect("/")
	
def forum_like(request):
    forum_id = request.POST.get('forumid')  
    classroom_id = request.POST.get('classroomid')  		
    user_id = request.POST.get('userid')
    action = request.POST.get('action')
    likes = []
    sfworks = []
    fwork = FWork.objects.get(id=forum_id)
    user = User.objects.get(id=user_id)
    if forum_id:
        try:
            sfworks = SFWork.objects.filter(index=forum_id, student_id=user_id)
            sfwork = sfworks[0]
            jsonDec = json.decoder.JSONDecoder()
            if action == "like":
                if sfwork.likes:
                    likes = jsonDec.decode(sfwork.likes)                     
                    if not request.user.id in likes:
                        likes.append(request.user.id)
                else:
                    likes.append(request.user.id)
                sfwork.likes = json.dumps(likes)
                sfwork.like_count = len(likes)								
                sfwork.save()
                update_avatar(request.user.id, 2, 0.1)
                # History
                history = PointHistory(user_id=request.user.id, kind=2, message=u'+0.1分--討論區按讚<'+fwork.title+'><'+user.first_name+'>', url="/student/forum/memo/"+classroom_id+"/"+forum_id+"/0/#"+user_id)
                history.save()										
            else:
                if sfwork.likes:
                    likes = jsonDec.decode(sfwork.likes)
                    if request.user.id in likes:
                        likes.remove(request.user.id)
                        sfwork.likes = json.dumps(likes)
                        sfwork.like_count = len(likes)
                        sfwork.save()
                        #積分 
                        update_avatar(request.user.id, 2, -0.1)
                        # History
                        history = PointHistory(user_id=request.user.id, kind=2, message=u'-0.1分--討論區按讚取消<'+fwork.title+'><'+user.first_name+'>', url="/student/forum/memo/"+classroom_id+"/"+forum_id+"/0/#"+user_id)
                        history.save()		               
        except ObjectDoesNotExist:
            sfworks = []            
        
        return JsonResponse({'status':'ok', 'likes':sfworks[0].likes}, safe=False)
    else:
        return JsonResponse({'status':'fail'}, safe=False)        

def forum_reply(request):
    forum_id = request.POST.get('forumid')  
    classroom_id = request.POST.get('classroomid')		
    user_id = request.POST.get('userid')
    work_id = request.POST.get('workid')		
    text = request.POST.get('reply')
    fwork = FWork.objects.get(id=forum_id)
    user = User.objects.get(id=user_id)
    if forum_id:       
        reply = SFReply(index=forum_id, work_id=work_id, user_id=user_id, memo=text, publication_date=timezone.now())
        reply.save()
        sfwork = SFWork.objects.get(id=work_id)
        sfwork.reply_date = timezone.now()
        sfwork.save()
        update_avatar(request.user.id, 3, 0.2)
        # History
        history = PointHistory(user_id=request.user.id, kind=3, message=u'0.2分--討論區留言<'+fwork.title+'><'+user.first_name+'>', url='/student/forum/memo/'+classroom_id+'/'+forum_id+'/0/#'+user_id)
        history.save()		              
				
        return JsonResponse({'status':'ok'}, safe=False)
    else:
        return JsonResponse({'status':'fail'}, safe=False)        

			
def forum_guestbook(request):
    work_id = request.POST.get('workid')  
    guestbooks = "<table class=table>"
    if work_id:
        try :
            replys = SFReply.objects.filter(work_id=work_id).order_by("-id")
        except ObjectDoesNotExist:
            replys = []
        for reply in replys:
            user = User.objects.get(id=reply.user_id)
            guestbooks += '<tr><td nowrap>' + user.first_name + '</td><td>' + reply.memo + "</td></tr>"
        guestbooks += '</table>'
        return JsonResponse({'status':'ok', 'replys': guestbooks}, safe=False)
    else:
        return JsonResponse({'status':'fail'}, safe=False)        
			
def forum_people(request):
    forum_id = request.POST.get('forumid')  
    user_id = request.POST.get('userid')
    likes = []
    sfworks = []
    names = []
    if forum_id:
        try:
            sfworks = SFWork.objects.filter(index=forum_id, student_id=user_id).order_by("id")
            sfwork = sfworks[0]
            jsonDec = json.decoder.JSONDecoder()
            if sfwork.likes:
                likes = jsonDec.decode(sfwork.likes)  
                for like in reversed(likes):
                  user = User.objects.get(id=like)
                  names.append('<button type="button" class="btn btn-default">'+user.first_name+'</button>')
        except ObjectDoesNotExist:
            sfworks = []                   
        return JsonResponse({'status':'ok', 'likes':names}, safe=False)
    else:
        return JsonResponse({'status':'fail'}, safe=False)        

def forum_score(request):
    work_id = request.POST.get('workid')  
    classroom_id = request.POST.get('classroomid')  
    user_id = request.POST.get('userid')  		
    score = request.POST.get('score')
    comment = request.POST.get('comment')		
    if work_id and is_teacher(classroom_id, request.user.id):
        sfwork = SFWork.objects.get(id=work_id)
        sfwork.score = score
        sfwork.comment = comment
        sfwork.scorer = request.user.id
        sfwork.comment_publication_date = timezone.now()
        sfwork.save()
        return JsonResponse({'status':'ok'}, safe=False)
    else:
        return JsonResponse({'status':'fail'}, safe=False)        

# 統計某討論主題所有同學心得
def forum_jieba(request, classroom_id, index): 
    classroom = Classroom.objects.get(id=classroom_id)
    enrolls = Enroll.objects.filter(classroom_id=classroom_id)
    works = []
    contents = FContent.objects.filter(forum_id=index).order_by("-id")
    fwork = FWork.objects.get(id=index)
    teacher_id = fwork.teacher_id
    subject = fwork.title
    memo = ""
    for enroll in enrolls:
        try:
            works = SFWork.objects.filter(index=index, student_id=enroll.student_id).order_by("-id")
            if works:
                memo += works[0].memo
        except ObjectDoesNotExist:
            pass
    memo = memo.rstrip('\r\n')
    seglist = jieba.cut(memo, cut_all=False)
    hash = {}
    for item in seglist: 
        if item in hash:
            hash[item] += 1
        else:
            hash[item] = 1
    words = []
    count = 0
    error=""
    for key, value in sorted(hash.items(), key=lambda x: x[1], reverse=True):
        if ord(key[0]) > 32 :
            count += 1	
            words.append([key, value])
            if count == 100:
                break       
    return render_to_response('student/forum_jieba.html', {'index': index, 'words':words, 'enrolls':enrolls, 'classroom':classroom, 'subject':subject}, context_instance=RequestContext(request))

# 查詢某班某詞句心得
def forum_word(request, classroom_id, index, word):
        enrolls = Enroll.objects.filter(classroom_id=classroom_id).order_by("seat")
        work_ids = []
        datas = []
        pos = word.index(' ')
        word = word[0:pos]
        for enroll in enrolls:
            try:
                works = SFWork.objects.filter(index=index, student_id=enroll.student_id,memo__contains=word).order_by("-id")
                if works:
                    work_ids.append(works[0].id)
                    datas.append([works[0], enroll.seat])
            except ObjectDoesNotExist:
                pass
        classroom = Classroom.objects.get(id=classroom_id)
        for work, seat in datas:
            work.memo = work.memo.replace(word, '<font color=red>'+word+'</font>')          
        return render_to_response('student/forum_word.html', {'word':word, 'datas':datas, 'classroom':classroom}, context_instance=RequestContext(request))
		
# 下載檔案
def forum_download(request, file_id):
    content = SFContent.objects.get(id=file_id)
    filename = content.title
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))		
    download =  BASE_DIR + "/static/upload/" + content.filename
    wrapper = FileWrapper(file( download, "r" ))
    response = HttpResponse(wrapper, content_type = 'application/force-download')
    #response = HttpResponse(content_type='application/force-download')
    response['Content-Disposition'] = 'attachment; filename={0}'.format(filename.encode('utf8'))
    # It's usually a good idea to set the 'Content-Length' header too.
    # You can also set any other required headers: Cache-Control, etc.
    return response
	
# 顯示圖片
def forum_showpic(request, file_id):
        content = SFContent.objects.get(id=file_id)
        return render_to_response('student/forum_showpic.html', {'content':content}, context_instance=RequestContext(request))

# ajax刪除檔案
def forum_file_delete(request):
    file_id = request.POST.get('fileid')  
    if file_id:
        try:
            file = SFContent.objects.get(id=file_id)
            file.visible = False
            file.delete_date = timezone.now()
            file.save()
        except ObjectDoesNotExist:
            file = []           
        return JsonResponse({'status':'ok'}, safe=False)
    else:
        return JsonResponse({'status':'fail'}, safe=False)        	