from django.shortcuts import render



from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication, \
     BasicAuthentication
from rest_framework.views import APIView
from qms_app.models import *
from qms import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect

import json
import uuid
from datetime import datetime,time,date,timedelta
from calendar import monthrange

from django.utils.timezone import localtime
from django.core.files import File
from io import BytesIO
from PIL import Image as IMage
from django.core.files.uploadedfile import InMemoryUploadedFile

import logging
import sys
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
import traceback


# Response
# 400 Bad Request
# 401 Unauthorized
# 403 Forbidden
# 404 Not Found
# 409 Conflict
# 200 OK
# 201 Created
# 202 Accepted

class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return

# LOGGER

def error():
    exc_type, exc_value, exc_traceback = sys.exc_info()
    print("\nLINE = :", exc_traceback.tb_lineno)
    formatted_lines = traceback.format_exc().splitlines()
    print("ERROR = ", formatted_lines[-1],end="\n")

# User Related APIs

class Login_SubmitAPI(APIView):

    authentication_classes = (CsrfExemptSessionAuthentication,BasicAuthentication)

    def post(self, request, *args, **kwargs):

        response = {}
        response["status"] = 500

        try:
            data = request.data

            user = authenticate(username=data['username'], password=data['password'])

            if (len(User.objects.filter(username=data['username'])) == 1):
                response['status'] = 200
                login(request, user)
            else:
                response['status'] = 401

        except Exception as e:
            error()
            print("ERROR IN = Login_SubmitAPI", str(e))

        return Response(data=response)

Login_Submit = Login_SubmitAPI.as_view()

class Signup_SubmitAPI(APIView):

    authentication_classes = (CsrfExemptSessionAuthentication,BasicAuthentication)

    def post(self, request, *args, **kwargs):
        response = {}
        response["status"] = 500

        try:
            data = request.data

            if(len(User.objects.filter(username=data['username'])) == 0):
                try:
                    user = CustomUser.objects.create(username=data['username'], email=data['email'], password=data["password"])
                    user.uuid = str(uuid.uuid4())

                    filepath = settings.STATIC_ROOT+'/qms_app/images/'+data['username'].upper()[0]+'.png'
                    print(filepath)

                    thumb = IMage.open(filepath)
                    im_type = thumb.format
                    thumb_io = BytesIO()
                    thumb.save(thumb_io, format=im_type)

                    thumb_file = InMemoryUploadedFile(thumb_io, None, filepath, 'image/'+im_type, thumb_io.getbuffer(), None)
                    user.dp = thumb_file

                    user.save()
                    response['status'] = 202

                except Exception as e:
                    print(str(e))
                    response['status'] = 400
            else:
                response['status']  = 409

        except Exception as e:
            error()
            print("ERROR = Signup_SubmitAPI", str(e))

        return Response(data=response)

Signup_Submit = Signup_SubmitAPI.as_view()

class Get_QuizzesAPI(APIView):

    authentication_classes = (CsrfExemptSessionAuthentication,BasicAuthentication)

    def post(self, request, *args, **kwargs):
        response = {}
        response["status"] = 500

        try:
            data = request.data
            user = request.user
            user = CustomUser.objects.get(username = user.username)

            response['past_quizzes'] = []
            response['ongoing_quizzes'] = []
            response['upcoming_quizzes'] = []

            quizzes = Quiz.objects.all()

            past_quizzes = quizzes.filter(end_time__lte = datetime.now())
            ongoing_quizzes = quizzes.filter(start_time__lte = datetime.now(), end_time__gte = datetime.now())
            upcoming_quizzes = quizzes.filter(start_time__gte = datetime.now())

            for quiz in past_quizzes:
                temp = {}
                temp['uuid'] = quiz.uuid
                temp['name'] = quiz.name
                temp['start_date'] = quiz.get_start_date()
                temp['end_date'] = quiz.get_end_date()
                temp['start_time'] = quiz.get_start_time()
                temp['end_time'] = quiz.get_end_time()
                temp['description']  = quiz.description
                temp['maximum_score']  = quiz.score

                if len(user.attempt_quiz_set.filter(uuid = quiz.uuid))>0:
                    temp['user_appeared'] = "1"
                    temp['attemp_uuid'] = quiz.uuid
                    temp['score'] = str(user.attempt_quiz_set.get(uuid = quiz.uuid).score)
                else:
                    temp['user_appeared'] = "0"
                    temp['attempt_uuid'] = "None"
                    temp['score'] = "0"

                response['past_quizzes'].append(temp)

            for quiz in ongoing_quizzes:
                temp = {}
                temp['uuid'] = quiz.uuid
                temp['name'] = quiz.name
                temp['start_date'] = quiz.get_start_date()
                temp['end_date'] = quiz.get_end_date()
                temp['start_time'] = quiz.get_start_time()
                temp['end_time'] = quiz.get_end_time()
                temp['description']  = quiz.description
                temp['maximum_score']  = quiz.score

                if len(user.attempt_quiz_set.filter(uuid = quiz.uuid))>0:
                    temp['user_appeared'] = "1"
                    temp['attempt_uuid'] = quiz.uuid
                    temp['score'] = str(user.attempt_quiz_set.get(uuid = quiz.uuid).score)
                else:
                    temp['user_appeared'] = "0"
                    temp['score'] = "0"
                    temp['attemp_uuid'] = "None"

                response['ongoing_quizzes'].append(temp)

            for quiz in upcoming_quizzes:
                temp = {}
                temp['uuid'] = quiz.uuid
                temp['name'] = quiz.name
                temp['start_date'] = quiz.get_start_date()
                temp['end_date'] = quiz.get_end_date()
                temp['start_time'] = quiz.get_start_time()
                temp['end_time'] = quiz.get_end_time()
                temp['description']  = quiz.description
                temp['maximum_score']  = quiz.score
                response['upcoming_quizzes'].append(temp)

            response["status"] = 200

        except Exception as e:
            error()
            print("ERROR IN  = Get_QuizzesAPI", str(e))

        return Response(data=response)

Get_Quizzes = Get_QuizzesAPI.as_view()


class Attemp_QuizAPI(APIView):

    authentication_classes = (CsrfExemptSessionAuthentication,BasicAuthentication)

    def post(self, request, *args, **kwargs):
        response = {}
        response["status"] = 500

        try:
            data = request.data
            user = request.user
            user = CustomUser.objects.get(username = user.username)
            quiz = Quiz.objects.get(uuid = data['quiz_uuid'])
            attempt = Attemp_Quiz.objects.create(custom_user=data['username'], quiz=quiz)
            response['attempt_uuid'] = attempt.uuid
            response["status"] = 200
        except Exception as e:
            error()
            print("ERROR IN  = Get_QuizzesAPI", str(e))

        return Response(data=response)

Attemp_Quiz = Get_QuizzesAPI.as_view()

class Get_QuestionsAPI(APIView):

    authentication_classes = (CsrfExemptSessionAuthentication,BasicAuthentication)

    def post(self, request, *args, **kwargs):
        response = {}
        response["status"] = 500

        try:
            data = request.data
            user = request.user
            user = CustomUser.objects.get(username = user.username)
            attempt = Attemp_Quiz.objects.get(uuid = data['attempt_uuid'])
            quiz = attempt.quiz

            if user != attempt.user or quiz.end_date < datetime.now():
                response['status'] = 401
            else:
                response['attempt_uuid'] = attempt.uuid
                response['MCQs'] = []
                response['OTQs'] = []

                mcqs = MCQ.objects.filter(quiz = quiz)
                otqs = Open_Text_Question.objects.filter(quiz = quiz)

                for mcq in mcqs:
                    temp = {}
                    temp['uuid'] = mcq.uuid
                    temp['name'] = mcq.name
                    temp['statement'] = mcq.statement
                    temp['image'] = mcq.image
                    if quiz._sum_score>0:
                        temp['score'] = str(mcq.score*quiz._score/quiz._sum_score)
                    else:
                        temp['score'] = "0"

                    temp['options'] = []

                    for option in mcq.option_set.all():
                        op = {}
                        op['uuid'] = option.uuid
                        op['text'] = option.text
                        op['image'] = option.image
                        temp['options'].append(op)

                    response['MCQs'].append(temp)

                for otq in otqs:
                    temp = {}
                    temp['uuid'] = otq.uuid
                    temp['name'] = otq.name
                    temp['statement'] = otq.statement
                    temp['image'] = otq.image
                    if quiz._sum_score>0:
                        temp['score'] = str(otq.score*quiz._score/quiz._sum_score)
                    else:
                        temp['score'] = "0"

                    response['OTQs'].append(temp)

                response["status"] = 200
        except Exception as e:
            error()
            print("ERROR IN  = Get_QuizzesAPI", str(e))

        return Response(data=response)

Get_Questions = Get_QuestionsAPI.as_view()


class Attempt_QuestionAPI(APIView):

    authentication_classes = (CsrfExemptSessionAuthentication,BasicAuthentication)

    def post(self, request, *args, **kwargs):
        response = {}
        response["status"] = 500

        try:
            data = request.data
            user = request.user
            user = CustomUser.objects.get(username = user.username)

            if user != attempt.user or quiz.end_date<datetime.now():
                response['status'] = 401
                return Response(data=response)

            if len(MCQ.objects.filter(uuid = data['question_uuid']))>0:
                question = MCQ.objects.get(uuid = data['question_uuid'])
                answers = Answer_MCQ.filter(mcq = question)
            else:
                question = Open_Text_Question.objects.get(uuid = data['question_uuid'])
                answers = Answer_MCQ.filter( open_text_question = question)

            quiz = question.quiz
            attempt = Attemp_Quiz.objects.get(custom_user=user,quiz=quiz)

            if len(MCQ.objects.filter(uuid = data['question_uuid']))>0:
                users_answers = Option.objects.filter( uuid__in = data['options_selected'])
                users_answers = users_answer.difference(answers)

                response['correct'] = "1"
                response['incorrect_selected'] = []
                response['incorrect_not_selected'] = []

                users_answers = list(users_answer)

                for option in users_answer:
                    op = {}
                    op['option_uuid'] = option.uuid
                    response['incorrect_selected'].appent(op)
                    response['correct'] = "0"

                users_answers = Option.objects.filter( uuid__in = data['options_selected'])
                answers = answers.difference(users_answer)

                for option in answers:
                    op = {}
                    op['option_uuid'] = option.uuid
                    response['incorrect_not_selected'].appent(op)
                    response['correct'] = "0"

                if response['correct'] == "1":
                    Attempt_MCQ.objects.create(attempt, score=1 , question=question )
                else:
                    Attempt_MCQ.objects.create(attempt, score=0 , question=question )
            else:

                if len(Answer_Open_Text_Question.objects.filter( answer = data['answer']))>0:
                    response['correct'] = "1"
                    Attempt_Open_Text_Question.objects.create(attempt, score=1 , question=question )
                else:
                    Attempt_Open_Text_Question.objects.create(attempt, score=0 , question=question )
                    response['correct'] = "0"

                response['correct_ans'] = list(Answer_Open_Text_Question.objects.filter( answer = data['answer']))[0].answer
                response["status"] = 200
        except Exception as e:
            error()
            print("ERROR IN  = Attempt_QuestionAPI", str(e))

        return Response(data=response)

Attempt_Question = Attempt_QuestionAPI.as_view()
