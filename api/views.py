# views.py
from rest_framework import generics, permissions, views
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
from rest_framework import status, viewsets
from .serializers import UserSerializer, ChatbotSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.views import View
from rest_framework.decorators import api_view
from django.conf import settings
BASE_DIR = settings.BASE_DIR

from sentence_transformers import SentenceTransformer, util
import torch
import json
from difflib import get_close_matches
from django.conf import settings
import os
BASE_DIR = settings.BASE_DIR

class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        # Extract user data from request
        user_data = self.request.data
        username = user_data.get('username')
        email = user_data.get('email')
        mobile_num = user_data.get('mobile_num')
       
        # Check if the username, email, or mobile number already exists
        if User.objects.filter(username=username).exists():
            raise ValidationError({'username': 'A user with this Mobile Number already exists.'})

        if User.objects.filter(email=email).exists():
            raise ValidationError({'email': 'A user with this email already exists.'})

        
        # Save the user and profile
        serializer.save()


class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
    












# Load the model once when the application starts
model = SentenceTransformer('all-MiniLM-L6-v2')  # Lightweight and efficient model for embeddings

BASE_DIR = settings.BASE_DIR  # Set your project's base directory

# Load the knowledge base from a JSON file
def load_knowledge_base(file_path: str):
    full_path = os.path.join(BASE_DIR, file_path)
    with open(full_path, 'r') as file:
        data = json.load(file)
    return data

# Save the updated knowledge base to the JSON file
def save_knowledge_base(file_path: str, data: dict):
    full_path = os.path.join(BASE_DIR, file_path)
    with open(full_path, 'w') as file:
        json.dump(data, file, indent=2)

# Generate embeddings for each question in the knowledge base
def embed_questions(questions):
    return model.encode(questions, convert_to_tensor=True)

# Match user question with the highest similarity score
def find_best_match(user_question: str, questions: list[str]) -> str | None:
    question_embeddings = embed_questions(questions)
    user_question_embedding = model.encode(user_question, convert_to_tensor=True)
    similarity_scores = util.pytorch_cos_sim(user_question_embedding, question_embeddings)
    best_match_index = torch.argmax(similarity_scores)

    # Return the question with the highest similarity score above a threshold
    if similarity_scores[0][best_match_index] > 0.6:  # Adjust the threshold as needed
        return questions[best_match_index]
    return None

# Retrieve the answer for a given question
def get_answer_for_question(question: str, knowledge_base: dict) -> str | None:
    for q in knowledge_base["questions"]:
        if q["question"] == question:
            return q["answer"]
    return None

class ChatbotViewSet(viewsets.ViewSet):
    serializer_class = ChatbotSerializer

    # Ensure authentication is disabled for this view
    authentication_classes = []
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user_question = serializer.validated_data['question']
            knowledge_base = load_knowledge_base('knowledge_base.json')
            questions = [q["question"] for q in knowledge_base["questions"]]
            best_match = find_best_match(user_question, questions)

            if best_match:
                answer = get_answer_for_question(best_match, knowledge_base)
                if answer:  # Check if answer is not None
                    # Replace pipe with newline for better formatting
                    formatted_answer = answer.replace('|', '\n').strip()
                    return Response({'answer': formatted_answer}, status=status.HTTP_200_OK)
                else:
                    return Response({'answer': "Wala ko'y nakita nga tubag para ana."}, status=status.HTTP_200_OK)
            else:
                return Response({'answer': "Wala ko kasabot sa pangutana. Palihug pangutana sa Cebuano."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)