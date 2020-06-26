from django.db import models
from django.contrib.auth.models import User
from django.db.models import CheckConstraint, Q, F , UniqueConstraint
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

import uuid


#########

def get_uuid():
    return str(uuid.uuid4())

class Custom_User(User):

    uuid = models.CharField(max_length=100,default = "", editable=False)
    dp = models.ImageField(upload_to='',blank=True)

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        if self.pk==None:
            self.set_password(self.password)
            self.uuid = get_uuid()
        super(Custom_User, self).save(*args, **kwargs)

########

class Quiz(models.Model):
    name = models.CharField(max_length=200)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    description = models.CharField(max_length=1000,blank=True)
    uuid = models.CharField(max_length=100,default = "", editable=False)
    score = models.FloatField(default = 100)

    _sum_score = models.FloatField(default = 0) # ,editable=False
    _score = models.FloatField(default = 0,editable=False)

    class Meta:
        verbose_name = "Quiz"
        verbose_name_plural = "Quizzes"

        constraints = [
            CheckConstraint(
                check=Q(end_date__gt=F('start_date')), name='check_start_date',
            ),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.pk==None:
            self.uuid = get_uuid()
        if self._score != self.score :
            self._score = self.score

            for attempt in self.attempt_quiz_set.all():
                attempt.save()

        super(Quiz, self).save(*args, **kwargs)

    def get_start_date(self):
        return self.start_date.strftime("%x")

    def get_end_date(self):
        return self.end_date.strftime("%x")

    def get_start_time(self):
        return self.start_date.strftime("%X")

    def get_end_time(self):
        return self.end_date.strftime("%X")

##########

# Abstract class for questions
class Question(models.Model):
    uuid = models.CharField(max_length=100,default = "", editable=False)
    name = models.CharField(max_length=100,default = "")
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    statement = models.CharField(max_length=1000,default = "",blank=True)
    image = models.ImageField(upload_to="", blank=True)
    score = models.FloatField(default = 100)
    visible = models.BooleanField(default = True)

    _visible = models.BooleanField(default = True,editable=False)
    _score = models.FloatField(default = 0,editable=False)

    class Meta:
        abstract = True

def question_delete(sender, instance, **kwargs):
    instance.score = 0
    instance.save()

##########

# MCQ extends Question
class MCQ(Question):

    # number_of_correct_options = models.SmallIntegerField()
    #
    #     constraints = [
    #         CheckConstraint(
    #             check=Q(number_of_correct_options__gte=F(0)), name='check_number_of_correct_options',
    #         ),
    #     ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):

        if self.statement=="" and self.image=="":
            raise Exception("Image and Text both can't be empty for a MCQ")

        if self.pk==None:
            self.uuid = get_uuid()
            if self.visible:
                self.quiz._sum_score += self.score - self._score
                self.quiz.save()
                self._score = self.score
            else:
                self._visible = False
        else:
            if self.visible != self._visible:

                if self.visible==True:
                    self.quiz._sum_score += self._score
                    self.quiz.save()
                    self._visible = True
                else:
                    self.quiz._sum_score -= self._score
                    self.quiz.save()
                    self._score = 0
                    self._visible = False

                for attempt in self.quiz.attempt_quiz_set.all():
                    attempt.save()

                for attempt in self.attempt_mcq_set.all():
                    attempt.save()


            if self._visible and self._score != self.score:
                self.quiz._sum_score += self.score - self._score
                self.quiz.save()
                self._score = self.score

                for attempt in self.quiz.attempt_quiz_set.all():
                    attempt.save()
                for attempt in self.attempt_mcq_set.all():
                    attempt.save()

        super(MCQ, self).save(*args, **kwargs)

pre_delete.connect(question_delete, sender=MCQ)


# MCQ can have multiple options and each option can be in multiple questions ( for example true/false options are quite common)
class Option(models.Model):
    uuid = models.CharField(max_length=100,default = "", editable=False)
    mcq = models.ManyToManyField(MCQ)
    text = models.CharField(max_length=1000,default = "",blank=True)
    image = models.ImageField(upload_to="",blank=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['text', 'image'], name='unique options'),
        ]

    def __str__(self):
        return self.uuid

    def save(self, *args, **kwargs):
        if self.pk==None:
            self.uuid = get_uuid()
        if self.text=="" and self.image=="":
            raise Exception("Image and Text both can't be empty for an Option")
        super(Option, self).save(*args, **kwargs)

# It will store the list of correct options for each mcq ( There can be more than one correct option )
class Answer_MCQ(models.Model):
    uuid = models.CharField(max_length=100,default = "", editable=False)
    mcq = models.ForeignKey(MCQ, on_delete=models.CASCADE)
    option = models.ForeignKey(Option, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['mcq', 'option'], name='unique answer MCQ'),
        ]

    def __str__(self):
        return self.uuid

    def save(self, *args, **kwargs):
        if self.pk==None:
            self.uuid = get_uuid()
        super(Answer_MCQ, self).save(*args, **kwargs)

###########

# Open_Text_Question extends Question
class Open_Text_Question(Question):

    # number_of_correct_options = models.SmallIntegerField()
    #
    # class Meta:
    #     constraints = [
    #         CheckConstraint(
    #             check=Q(number_of_correct_options__gte=F(0)), name='check_number_of_correct_options',
    #         ),
    #     ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.statement=="" and self.image=="":
            raise Exception("Image and Text both can't be empty for an open text question")

        if self.pk==None:
            self.uuid = get_uuid()
            if self.visible:
                self.quiz._sum_score += self.score - self._score
                self.quiz.save()
                self._score = self.score
        else:
            if self.visible != self._visible:
                if self.visible==True:
                    self.quiz._sum_score += self._score
                    self.quiz.save()
                    self._visible = True
                else:
                    self.quiz._sum_score -= self._score
                    self.quiz.save()
                    self._score = 0
                    self._visible = False
                for attempt in self.quiz.attempt_quiz_set.all():
                    attempt.save()

                for attempt in self.attempt_open_text_question_set.all():
                    attempt.save()


            if self._visible and self._score != self.score:
                self.quiz._sum_score += self.score - self._score
                self.quiz.save()
                self._score = self.score

                for attempt in self.quiz.attempt_quiz_set.all():
                    attempt.save()

                for attempt in self.attempt_open_text_question_set.all():
                    attempt.save()

        super(Open_Text_Question, self).save(*args, **kwargs)

pre_delete.connect(question_delete, sender=Open_Text_Question)


# It will store the list of correct answers for each open text question ( There can be more than one correct answers )
class Answer_Open_Text_Question(models.Model):

    uuid = models.CharField(max_length=100,default = "", editable=False)
    open_text_question = models.ForeignKey(Open_Text_Question, on_delete=models.CASCADE)
    answer = models.CharField(max_length=1000)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['open_text_question', 'answer'], name='unique answer OTQ'),
        ]

    def __str__(self):
        return self.uuid

    def save(self, *args, **kwargs):
        if self.pk==None:
            self.uuid = get_uuid()
        super(Answer_Open_Text_Question, self).save(*args, **kwargs)

    def is_answer_equivalent_ignore_case( self, users_answer ):
        return ( self.answer.lower() == self.users_answer.lower() )

########


class Attempt_Quiz(models.Model):

    uuid = models.CharField(max_length=100,default = "", editable=False)
    custom_user = models.ForeignKey(Custom_User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    end_at = models.DateTimeField(default = None)

    # Editable though it shouldn't be edited at all ideally
    score = models.FloatField(default = 0 )

    _sum_score = models.FloatField(default = 0 ) # , editable=False

    class Meta:
        verbose_name = "Attempt_Quiz"
        verbose_name_plural = "Attempt_Quizzes"

        constraints = [
            UniqueConstraint(fields=['custom_user', 'quiz'], name='User can give a quiz at most once'),
        ]

    def __str__(self):
        return self.uuid

    def save(self, *args, **kwargs):
        if self.pk==None:
            self.uuid = get_uuid()
            self.end_at = self.quiz.end_date

        if self.quiz._sum_score == 0:
            self.score = 0
        else:
            self.score = self.quiz.score*self._sum_score/self.quiz._sum_score

        super(Attempt_Quiz, self).save(*args, **kwargs)

    def get_created_at(self):
        return self.created_at.strftime("%c")

    def get_end_at(self):
        return self.end_at.strftime("%c")

#######

class Attempt_Question(models.Model):

    uuid = models.CharField(max_length=100,default = "", editable=False)
    attempt_quiz = models.ForeignKey(Attempt_Quiz, on_delete=models.CASCADE)
    score = models.FloatField(default = 0)
    visible = models.BooleanField(default = True)

    _visible = models.BooleanField(default = True , editable=False)
    _score = models.FloatField(default = 0, editable=False)
    _question_score = models.FloatField(default = 0, editable=False)

    class Meta:
        abstract = True

    def __str__(self):
        return self.uuid

def attempt_question_delete(sender, instance, **kwargs):
    instance.score = 0
    instance.save()

#########


class Attempt_MCQ(Attempt_Question):

    question = models.ForeignKey(MCQ, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['attempt_quiz', 'question'], name='User can attemp each MCQ in a quiz at most once'),
        ]

    def __str__(self):
        return self.uuid

    def save(self, *args, **kwargs):
        if self.pk==None:
            self.uuid = get_uuid()
        if self.question._visible:
            if self.visible != self._visible:
                if self.visible == True:
                    self.attempt_quiz._sum_score += self._score*self._question_score
                    self.attempt_quiz.save()
                else:
                    self.attempt_quiz._sum_score -= self._score*self._question_score
                    self.attempt_quiz.save()
                self._visible = self.visible
        elif self._visible == True:
            self.attempt_quiz._sum_score -= self._score*self._question_score
            self.attempt_quiz.save()
            self._visible = self.question._visible

        if self._visible == True and (self._score!=self.score or self._question_score != self.question._score) :
            self.attempt_quiz._sum_score += self.score*self.question._score - self._score*self._question_score
            self._question_score = self.question._score
            self.attempt_quiz.save()
            self._score = self.score
        super(Attempt_MCQ, self).save(*args, **kwargs)

pre_delete.connect(attempt_question_delete, sender=Attempt_MCQ)


class Attempt_Open_Text_Question(Attempt_Question):

    question = models.ForeignKey(Open_Text_Question, on_delete=models.CASCADE)

    constraints = [
        UniqueConstraint(fields=['attempt_quiz', 'question'], name='User can attemp each OTQ in a quiz at most once'),
    ]

    def __str__(self):
        return self.uuid

    def save(self, *args, **kwargs):
        if self.pk==None:
            self.uuid = get_uuid()

        if self.question._visible:
            if self.visible != self._visible:
                if self.visible == True:
                    self.attempt_quiz._sum_score += self._score*self._question_score
                    self.attempt_quiz.save()
                else:
                    self.attempt_quiz._sum_score -= self._score*self._question_score
                    self.attempt_quiz.save()
                self._visible = self.visible
        elif self._visible == True:
            self.attempt_quiz._sum_score -= self._score*self._question_score
            self.attempt_quiz.save()
            self._visible = self.question._visible

        if self._visible == True and ( self._score!=self.score or self._question_score != self.question._score ) :
            self.attempt_quiz._sum_score += self.score*self.question._score - self._score*self._question_score
            self._question_score = self.question._score
            self.attempt_quiz.save()
            self._score = self.score
        super(Attempt_Open_Text_Question, self).save(*args, **kwargs)

pre_delete.connect(attempt_question_delete, sender=Attempt_Open_Text_Question)


########
