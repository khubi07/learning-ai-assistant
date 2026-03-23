from rest_framework import serializers
from .models import Note, Quiz, Question

class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = '__all__'

#“Take Note model → convert ALL fields into JSON”

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = '__all__'  # convert all question fields to JSON


class QuizSerializer(serializers.ModelSerializer):

    questions = QuestionSerializer(many=True)
    note_title = serializers.CharField(source='note.title')

    class Meta:
        model = Quiz
        fields = ['id', 'note_title', 'questions']