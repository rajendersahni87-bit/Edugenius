import os
import json
import uuid
import PyPDF2
from typing import List, Dict, Any
import chromadb
from chromadb.utils import embedding_functions
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from backend.config import settings
from backend.prompts.tutor_prompt import TUTOR_SYSTEM_PROMPT, TUTOR_QUERY_TEMPLATE
from backend.prompts.quiz_prompt import QUIZ_SYSTEM_PROMPT, QUIZ_TEMPLATE

class RAGService:
    def __init__(self):
        self.chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        self.embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name='all-MiniLM-L6-v2')
        self.llm = ChatGoogleGenerativeAI(model='gemini-3.6-flash', google_api_key=settings.GOOGLE_API_KEY)
        
    def ingest_document(self, file_path: str, subject_id: str) -> int:
        try:
            text = ""
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            
            paragraphs = text.split("\n\n")
            chunks = []
            current_chunk = ""
            for p in paragraphs:
                if len(current_chunk) + len(p) > settings.CHUNK_SIZE:
                    chunks.append(current_chunk)
                    current_chunk = p
                else:
                    current_chunk += "\n\n" + p
            if current_chunk:
                chunks.append(current_chunk)
                
            collection_name = f"subject_{subject_id}"
            collection = self.chroma_client.get_or_create_collection(
                name=collection_name, 
                embedding_function=self.embedding_func
            )
            
            ids = [uuid.uuid4().hex for _ in chunks]
            metadatas = [{"source": file_path} for _ in chunks]
            
            if chunks:
                collection.add(documents=chunks, metadatas=metadatas, ids=ids)
                
            return len(chunks)
        except Exception as e:
            print(f"Error ingesting document: {e}")
            return 0
            
    def query(self, question: str, subject_id: str, chat_history: list, mode: str = 'direct') -> dict:
        try:
            collection_name = f"subject_{subject_id}"
            try:
                collection = self.chroma_client.get_collection(
                    name=collection_name,
                    embedding_function=self.embedding_func
                )
            except Exception:
                collection = None
                
            context = ""
            sources = []
            if collection:
                results = collection.query(
                    query_texts=[question],
                    n_results=settings.TOP_K
                )
                if results['documents'] and len(results['documents'][0]) > 0:
                    context = "\n\n".join(results['documents'][0])
                    sources = [meta.get('source') for meta in results['metadatas'][0] if meta.get('source')]
                    sources = list(set(sources))
            
            history_str = "\n".join([f"{msg['role']}: {msg['message']}" for msg in chat_history[-5:]])
            
            prompt = TUTOR_QUERY_TEMPLATE.format(
                context=context,
                history=history_str,
                question=question,
                mode=mode
            )
            
            response = self.llm.invoke([
                SystemMessage(content=TUTOR_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ])
            
            # Handle both string and list-of-parts response formats
            answer = response.content
            if isinstance(answer, list):
                answer = " ".join(
                    part.get("text", str(part)) if isinstance(part, dict) else str(part)
                    for part in answer
                )
            
            return {"answer": answer, "sources": sources}
        except Exception as e:
            return {"answer": f"Error querying tutor: {e}", "sources": []}
            
    def generate_quiz(self, subject_id: str, num_questions: int = 5, difficulty: str = 'medium') -> list:
        try:
            collection_name = f"subject_{subject_id}"
            try:
                collection = self.chroma_client.get_collection(
                    name=collection_name,
                    embedding_function=self.embedding_func
                )
            except Exception:
                return []
                
            results = collection.query(
                query_texts=[f"generate {difficulty} quiz questions"],
                n_results=10
            )
            context = ""
            if results['documents'] and len(results['documents'][0]) > 0:
                context = "\n\n".join(results['documents'][0])
                
            prompt = QUIZ_TEMPLATE.format(
                context=context,
                num_questions=num_questions,
                difficulty=difficulty
            )
            
            response = self.llm.invoke([
                SystemMessage(content=QUIZ_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ])
            
            content = response.content
            if isinstance(content, list):
                content = " ".join(
                    part.get("text", str(part)) if isinstance(part, dict) else str(part)
                    for part in content
                )
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].strip()
                
            questions = json.loads(content)
            return questions
        except Exception as e:
            print(f"Error generating quiz: {e}")
            return []

rag_service = RAGService()
