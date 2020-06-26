from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('login_submit/', views.Login_SubmitAPI.as_view()),
    path('signup_submit/', views.Signup_SubmitAPI.as_view()),
    path('attempt_quiz/', views.Attempt_QuizAPI.as_view()),
    path('questions/', views.Get_QuestionsAPI.as_view()),
    path('attempt_que/', views.Attempt_QuestionAPI.as_view()),
    path('', views.Get_QuizzesAPI.as_view()),
]
