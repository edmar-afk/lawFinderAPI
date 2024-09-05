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


import os
import json
import logging
from typing import Optional, List
from sentence_transformers import SentenceTransformer, util
from rest_framework import viewsets, status
from rest_framework.response import Response
from .serializers import ChatbotSerializer

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
    
























logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_knowledge_base(file_path: str) -> dict:
    try:
        full_path = os.path.join(BASE_DIR, file_path)
        with open(full_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        logger.error(f"Error loading knowledge base: {e}")
        return {}

def save_knowledge_base(file_path: str, data: dict) -> None:
    try:
        full_path = os.path.join(BASE_DIR, file_path)
        with open(full_path, 'w') as file:
            json.dump(data, file, indent=2)
    except Exception as e:
        logger.error(f"Error saving knowledge base: {e}")

model = SentenceTransformer('all-MiniLM-L6-v2')


def encode_questions(questions: List[str]) -> List:
    return model.encode(questions, convert_to_tensor=True)


def find_best_match(user_question: str, questions: List[str]) -> Optional[str]:
    user_question_embedding = model.encode(user_question, convert_to_tensor=True)
    question_embeddings = encode_questions(questions)
    similarities = util.pytorch_cos_sim(user_question_embedding, question_embeddings)
    most_similar_idx = similarities.argmax()
    return questions[most_similar_idx] if similarities.max() > 0.5 else None


def get_answer_for_question(user_question: str, knowledge_base: dict) -> Optional[str]:
    questions = [q.get("question") for q in knowledge_base.get("questions", [])]
    best_match = find_best_match(user_question, questions)
    if best_match:
        for q in knowledge_base.get("questions", []):
            if q.get("question") == best_match:
                return q.get("answer")
    return None

class ChatbotViewSet(viewsets.ViewSet):
    serializer_class = ChatbotSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user_question = serializer.validated_data['question']
            knowledge_base = load_knowledge_base('knowledge_base.json')
            answer = get_answer_for_question(user_question, knowledge_base)

            if answer:
                return Response({'answer': answer}, status=status.HTTP_200_OK)
            else:
                return Response({'answer': "I don't understand the question."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)