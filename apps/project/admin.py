from django.contrib import admin
from apps.project.models import Term, Partner, Token, Event

# Register your models here.

admin.site.register((Term, Partner, Token, Event))
