from django.urls import path
from .views import home, about, add_note, note_detail, edit_note, delete_note, signup, summarize_note, generate_quiz, quiz_detail, api_notes
from .views import api_quiz_detail

urlpatterns = [
    path('', home, name="home"),
    path('about/', about, name="about"),
    path('add-note/', add_note, name="add_note"),
    path('note/<int:id>/', note_detail, name="note_detail"),
    path('note/<int:id>/edit/', edit_note, name="edit_note"),
    path('note/<int:id>/delete/', delete_note, name="delete_note"),
    path("signup/", signup, name="signup"),
    path("note/<int:id>/summarize/", summarize_note, name="summarize_note"),
    path("note/<int:id>/quiz/", generate_quiz, name="generate_quiz"),
    path("quiz/<int:id>/", quiz_detail, name="quiz_detail"),
    path('api/notes/', api_notes, name='api_notes'),
    path('api/quiz/<int:id>/', api_quiz_detail, name='api_quiz_detail'),
]