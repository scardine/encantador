from django.contrib.auth.models import User
from django.db import models


class Request(models.Model):
    created_by = models.ForeignKey(User, on_delete='cascade')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    subject