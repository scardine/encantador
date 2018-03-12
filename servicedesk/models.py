from django.contrib.auth.models import User
from django.db import models
from django_fsm import FSMField, transition, TransitionNotAllowed

COMMENT = 0
RESPONSE = 1


class Queue(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    email = models.EmailField()

    def __str__(self):
        return self.name


class Request(models.Model):
    STATUS = (
        ('new', 'New'),
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('removed', 'Removed'),
    )
    queue = models.ForeignKey(Queue, on_delete=models.PROTECT)
    created_by = models.EmailField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    subject = models.CharField(max_length=200)
    requester = models.EmailField()
    responsible = models.ForeignKey(User, on_delete=models.PROTECT)
    status = FSMField(default='new', choices=STATUS)

    @transition(field=status, source='new', target='open')
    def assign(self, responsible):
        self.responsible = responsible

    @transition(field=status, source='open', target='rejected')
    def reject(self, author, message, comment_type=COMMENT, attachments=None):
        self.record_comment(author, message, comment_type, attachments)

    @transition(field=status, source='*', target='open')
    def comment(self, author, message, comment_type, attachments=None):
        self.record_comment(author, message, comment_type, attachments)

    def record_comment(self, author, message, comment_type, attachments):
        if comment_type == RESPONSE and author not in (self.requester, self.responsible.email):
            try:
                user = User.objects.get(email=author)
            except User.DoesNotExist:
                raise TransitionNotAllowed('{} is not allowed to respond.'.format(author))

        if attachments:
            for payload in attachments:
                Attachment.objects.create(request=self, payload=payload)
        Update.objects.create(request=self, author=author, message=message, type=comment_type)

    @transition(field=status, source='*', target='closed')
    def close(self, author, message, comment_type=RESPONSE, attachments=None):
        self.record_comment(author, message, comment_type, attachments)

    def __str__(self):
        return "[{} #{}] {}".format(self.queue.name, self.pk, self.subject)


class Update(models.Model):
    TYPE = (
        (COMMENT, 'Comment'),
        (RESPONSE, 'Response'),
    )
    request = models.ForeignKey(Request, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    author = models.EmailField()
    type = models.IntegerField(choices=TYPE, default=0)
    message = models.TextField()

    def __str__(self):
        return self.get_type_display()

    class Meta:
        verbose_name = 'Update'


class Attachment(models.Model):
    comment = models.ForeignKey(Update, on_delete=models.CASCADE)
    payload = models.FileField(upload_to='attachments')
    mime_type = models.CharField(max_length=100)
