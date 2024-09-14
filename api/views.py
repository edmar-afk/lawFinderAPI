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
import fitz  # PyMuPDF
from typing import List, Optional
from pathlib import Path
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
    



















import logging
import os
from typing import List, Optional
from rest_framework import viewsets, status
from rest_framework.response import Response
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer, util

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define the relative path to the PDF file
def get_pdf_path() -> str:
    # Path to the PDF file relative to this script
    return str(Path(__file__).parent / 'knowledge_base.pdf')

def load_pdf(file_path: str) -> str:
    try:
        full_path = file_path
        if not os.path.exists(full_path):
            logger.error(f"PDF file does not exist at: {full_path}")
            return ""
        with fitz.open(full_path) as pdf_file:
            text = ""
            for page_num in range(pdf_file.page_count):
                page = pdf_file.load_page(page_num)
                text += page.get_text()
            logger.info("PDF loaded successfully.")
            return text
    except Exception as e:
        logger.error(f"Error loading PDF: {e}")
        return ""

# Split the extracted text into chunks for easier searching
def split_text_into_chunks(text: str, chunk_size: int = 800) -> List[str]:
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

model = SentenceTransformer('all-MiniLM-L6-v2')

# Encode the text chunks
def encode_chunks(chunks: List[str]) -> List:
    return model.encode(chunks, convert_to_tensor=True)

# Find the best matching text chunk for a user question
def find_best_match_in_pdf(user_question: str, text_chunks: List[str], threshold: float = 0.1) -> Optional[str]:
    user_question_embedding = model.encode(user_question, convert_to_tensor=True)
    chunk_embeddings = encode_chunks(text_chunks)
    similarities = util.pytorch_cos_sim(user_question_embedding, chunk_embeddings)
    
    logger.info(f"User question embedding: {user_question_embedding}")
    logger.info(f"Chunk embeddings: {chunk_embeddings}")
    logger.info(f"Similarities: {similarities}")

    most_similar_idx = similarities.argmax()
    logger.info(f"Most similar index: {most_similar_idx}")
    logger.info(f"Highest similarity score: {similarities.max()}")

    return text_chunks[most_similar_idx] if similarities.max() > threshold else None

class ChatbotViewSet(viewsets.ViewSet):
    serializer_class = ChatbotSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user_question = serializer.validated_data['question']
            
            # Load and process the PDF file
            pdf_path = get_pdf_path()  # Get the relative path
            pdf_text = load_pdf(pdf_path)
            if not pdf_text:
                return Response({'answer': "I don't understand the question."}, status=status.HTTP_200_OK)

            text_chunks = split_text_into_chunks(pdf_text)
            logger.info(f"Text chunks: {text_chunks[:3]}")  # Log first few chunks for inspection

            # Find the best match in the PDF text
            answer = find_best_match_in_pdf(user_question, text_chunks)

            if answer:
                return Response({'answer': answer}, status=status.HTTP_200_OK)
            else:
                return Response({'answer': "I don't understand the question."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)