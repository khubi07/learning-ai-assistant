from django.contrib import admin
from .models import Note
from .models import Quiz, Question

# Register your models here.
admin.site.register(Note)
admin.site.register(Quiz)
admin.site.register(Question)