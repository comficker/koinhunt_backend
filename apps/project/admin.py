from django.contrib import admin
from apps.project.models import Term, Token, Event, Project

# Register your models here.

admin.site.register((Term, Token, Event, Project))
