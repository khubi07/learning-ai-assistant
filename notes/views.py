from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect, get_object_or_404
from .models import Note, Quiz, Question
from .forms import NoteForm
import os
import re
from groq import Groq
from django.conf import settings
import json
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import NoteSerializer, QuizSerializer

# drf(django rest frammework) returns json
@api_view(['GET']) #allow only get req
def api_notes(request):
    notes = Note.objects.filter(user=request.user) # fetch user's notes
    serializer = NoteSerializer(notes, many=True) # fetch user's notes
    return Response(serializer.data) # send JSON response

@api_view(['GET'])
@permission_classes([IsAuthenticated])  # only logged-in users
def api_quiz_detail(request, id):

    quiz = get_object_or_404(Quiz, id=id, note__user=request.user)

    serializer = QuizSerializer(quiz)

    return Response(serializer.data)

# other view returns html
def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = UserCreationForm()

    return render(request, "registration/signup.html", {"form": form})
@login_required
def home(request):
    notes = Note.objects.filter(user=request.user)
    return render(request, "home.html", {"notes": notes})

def about(request):
    return render(request, "about.html")

def add_note(request):
    if request.method == "POST":
        print(request.FILES)
        form = NoteForm(request.POST, request.FILES)
        if form.is_valid():
            note = form.save(commit=False)   # create note but don't save yet
            note.user = request.user         # assign logged-in user
            note.save()                      # now save
            return redirect("home")
        else:
            print(form.errors)
    else:
        form = NoteForm()

    return render(request, "add_note.html", {"form": form})

def note_detail(request, id):
    note = Note.objects.get(id=id)
    return render(request, "note_detail.html", {"note": note})

def edit_note(request, id):
    note = Note.objects.get(id=id) #Fetch the specific note user wants to edit.

    if request.method == "POST":
        #Take submitted data
        #AND apply it to existing note
        form = NoteForm(request.POST, request.FILES, instance=note)
        if form.is_valid():
            form.save()
            return redirect("home")
    else:
        #Create form pre-filled with old data.existing title/content automatically filled
        form = NoteForm(instance=note)
        #reuse same template
    return render(request, "add_note.html", {"form": form})

#explanation of edit_note- 
#instance=note, This tells Django:UPDATE this object NOT create new one

def delete_note(request, id):
    # get note using id
    note = Note.objects.get(id=id)

    # delete only when POST request comes
    if request.method == "POST":
        note.delete()

        # if request came from HTMX
        if request.headers.get("HX-Request"):
            return HttpResponse("")  # return empty response

        return redirect("home")

    # normal confirmation page
    return render(request, "delete_note.html", {"note": note})


from groq import Groq
import os


def summarize_note(request, id):

    # get the specific note belonging to logged-in user
    note = Note.objects.get(id=id, user=request.user)

    # initialize Groq client
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    # send prompt to LLM
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": f"""
                Summarize this note strictly in bullet points.
                Use '-' for each point.

                Note:
                {note.content}
                """
            }
        ]
    )

    # safely extract response text
    summary = response.choices[0].message.content or "No summary generated"

    return render(request, "partials/summary.html", {"summary": summary})
def generate_quiz(request, id):
    
    # 1️⃣ Get note
    note = Note.objects.get(id=id, user=request.user)

    # if quiz exists → delete it
    from .models import Quiz

    quiz = Quiz.objects.filter(note=note).first()

    if quiz:
        quiz.delete()

    # initialize Groq client
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    # send prompt to LLM
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": f"""
            Generate exactly 3 MCQ questions from the following note.

            Return ONLY JSON in this format:
            [
                {{
                     "question": "...",
                     "option_a": "...",
                     "option_b": "...",
                     "option_c": "...",
                     "option_d": "...",
                     "correct_answer": "A"
                }}
            ]

            Note:
                {note.content}
                """
            }
        ]
    )

    raw_text = response.choices[0].message.content or ""
    # if None → convert to empty string

    # extract JSON safely using regex
    match = re.search(r'\[.*\]', raw_text, re.DOTALL)

    if not match:
        return HttpResponse("Error: Invalid AI response")

    quiz_data = json.loads(match.group())

    # create quiz
    quiz = Quiz.objects.create(note=note)

    # save questions
    for q in quiz_data:
        Question.objects.create(
            quiz=quiz,
            question_text=q["question"],
            option_a=q["option_a"],
            option_b=q["option_b"],
            option_c=q["option_c"],
            option_d=q["option_d"],
            correct_answer=q["correct_answer"]
        )

    return redirect("quiz_detail", quiz.id)



def quiz_detail(request, id):

    quiz = Quiz.objects.get(id=id, note__user=request.user)
    questions = quiz.questions.all()

    score = 0
    total = questions.count()

    if request.method == "POST":
        for q in questions:
            user_answer = request.POST.get(f"q{q.id}")
            if user_answer == q.correct_answer:
                score += 1

        return render(request, "quiz_result.html", {
            "score": score,
            "total": total
        })

    return render(request, "quiz_detail.html", {
        "quiz": quiz,
        "questions": questions
    })