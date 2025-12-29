"""
RAG Pipeline Module
Handles document chunking, embeddings, vector storage, and retrieval for ChatPDF
"""

import os
import logging
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import tiktoken
from datetime import datetime
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ⚠️ TEMPORARY: Direct API Key (remove this and use .env in production!)
# OPENAI_API_KEY will be loaded from .env file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGPipeline:
    """RAG pipeline for document processing and question answering"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initialize RAG pipeline with vector database and embeddings model
        
        Args:
            persist_directory: Directory to persist ChromaDB data
        """
        self.persist_directory = persist_directory
        
        # Initialize ChromaDB
        logger.info("Initializing ChromaDB...")
        self.chroma_client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize embeddings model (free, local)
        logger.info("Loading embeddings model...")
        self.embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Embeddings model loaded successfully")
        
        # Initialize tokenizer for chunking
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Chunk settings
        self.chunk_size = 500  # tokens
        self.chunk_overlap = 50  # tokens
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        Split text into chunks with overlap
        
        Args:
            text: Text to chunk
            metadata: Metadata to attach to each chunk
        
        Returns:
            List of chunks with metadata
        """
        if not text or not text.strip():
            return []
        
        # Tokenize text
        tokens = self.tokenizer.encode(text)
        
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(tokens):
            # Get chunk
            end = min(start + self.chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            
            # Decode back to text
            chunk_text = self.tokenizer.decode(chunk_tokens)
            
            # Create chunk with metadata
            chunk = {
                'text': chunk_text,
                'chunk_id': chunk_id,
                'start_token': start,
                'end_token': end,
                'metadata': metadata or {}
            }
            
            chunks.append(chunk)
            chunk_id += 1
            
            # Move start position with overlap
            start += self.chunk_size - self.chunk_overlap
        
        logger.info(f"Created {len(chunks)} chunks from text of {len(tokens)} tokens")
        return chunks
    
    def create_or_get_collection(self, document_id: str) -> chromadb.Collection:
        """
        Create or get a collection for a document
        
        Args:
            document_id: Unique document identifier
        
        Returns:
            ChromaDB collection
        """
        collection_name = f"doc_{document_id}"
        
        try:
            collection = self.chroma_client.get_collection(name=collection_name)
            logger.info(f"Retrieved existing collection: {collection_name}")
        except:
            collection = self.chroma_client.create_collection(
                name=collection_name,
                metadata={"created_at": datetime.now().isoformat()}
            )
            logger.info(f"Created new collection: {collection_name}")
        
        return collection
    
    def add_document(
        self,
        document_id: str,
        ocr_result: Dict,
        metadata: Dict = None
    ) -> Dict:
        """
        Process OCR result and add to vector database
        
        Args:
            document_id: Unique document identifier
            ocr_result: OCR processing result from ocr_pipeline
            metadata: Additional metadata
        
        Returns:
            Processing summary
        """
        logger.info(f"Processing document {document_id} for RAG...")
        
        collection = self.create_or_get_collection(document_id)
        
        all_chunks = []
        texts_to_embed = []
        chunk_metadata_list = []
        chunk_ids = []
        
        # Process each page
        for page in ocr_result['pages']:
            page_num = page['page_num']
            
            # Prepare page metadata
            page_metadata = {
                'document_id': document_id,
                'page_num': page_num,
                'source': page['source'],
                'confidence': page['confidence'],
                'has_tables': len(page.get('tables', [])) > 0,
                'has_forms': len(page.get('forms', [])) > 0,
                **(metadata or {})
            }
            
            # Chunk page text
            page_text = page.get('text', '')
            if page_text:
                chunks = self.chunk_text(page_text, page_metadata)
                
                for chunk in chunks:
                    chunk_id = f"{document_id}_p{page_num}_c{chunk['chunk_id']}"
                    texts_to_embed.append(chunk['text'])
                    chunk_metadata_list.append(chunk['metadata'])
                    chunk_ids.append(chunk_id)
                    all_chunks.append(chunk)
            
            # Add table data as separate chunks
            for table in page.get('tables', []):
                table_text = f"Table {table['table_id']} (Page {page_num}):\n{table.get('markdown', '')}"
                table_metadata = {
                    **page_metadata,
                    'content_type': 'table',
                    'table_id': table['table_id'],
                    'table_accuracy': table['accuracy']
                }
                
                chunk_id = f"{document_id}_p{page_num}_t{table['table_id']}"
                texts_to_embed.append(table_text)
                chunk_metadata_list.append(table_metadata)
                chunk_ids.append(chunk_id)
            
            # Add form data as separate chunks
            for idx, form in enumerate(page.get('forms', [])):
                form_text = f"Form Field (Page {page_num}): {form['field_name']} ({form['field_type']}): {form['field_value']}"
                form_metadata = {
                    **page_metadata,
                    'content_type': 'form',
                    'field_name': form['field_name'],
                    'field_type': form['field_type']
                }
                
                chunk_id = f"{document_id}_p{page_num}_f{idx}"
                texts_to_embed.append(form_text)
                chunk_metadata_list.append(form_metadata)
                chunk_ids.append(chunk_id)
        
        # Generate embeddings
        if texts_to_embed:
            logger.info(f"Generating embeddings for {len(texts_to_embed)} chunks...")
            embeddings = self.embeddings_model.encode(
                texts_to_embed,
                show_progress_bar=True,
                convert_to_numpy=True
            )
            
            # Add to ChromaDB
            collection.add(
                embeddings=embeddings.tolist(),
                documents=texts_to_embed,
                metadatas=chunk_metadata_list,
                ids=chunk_ids
            )
            
            logger.info(f"Added {len(texts_to_embed)} chunks to vector database")
        
        summary = {
            'document_id': document_id,
            'total_chunks': len(texts_to_embed),
            'total_pages': len(ocr_result['pages']),
            'collection_name': collection.name,
            'status': 'success'
        }
        
        return summary
    
    def retrieve_relevant_chunks(
        self,
        document_id: str,
        query: str,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Retrieve relevant chunks for a query
        
        Args:
            document_id: Document identifier
            query: User question
            top_k: Number of chunks to retrieve
        
        Returns:
            List of relevant chunks with metadata and scores
        """
        try:
            collection = self.create_or_get_collection(document_id)
            
            # Generate query embedding
            query_embedding = self.embeddings_model.encode(
                [query],
                convert_to_numpy=True
            )[0]
            
            # Search in vector database
            results = collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format results
            relevant_chunks = []
            if results['documents'] and len(results['documents'][0]) > 0:
                for idx, doc in enumerate(results['documents'][0]):
                    chunk = {
                        'text': doc,
                        'metadata': results['metadatas'][0][idx],
                        'similarity_score': 1 - results['distances'][0][idx],  # Convert distance to similarity
                        'rank': idx + 1
                    }
                    relevant_chunks.append(chunk)
            
            logger.info(f"Retrieved {len(relevant_chunks)} relevant chunks for query: {query[:50]}...")
            return relevant_chunks
            
        except Exception as e:
            logger.error(f"Error retrieving chunks: {e}")
            return []
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document's collection from vector database
        
        Args:
            document_id: Document identifier
        
        Returns:
            Success status
        """
        try:
            collection_name = f"doc_{document_id}"
            self.chroma_client.delete_collection(name=collection_name)
            logger.info(f"Deleted collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            return False
    
    def list_documents(self) -> List[str]:
        """
        List all document collections
        
        Returns:
            List of document IDs
        """
        try:
            collections = self.chroma_client.list_collections()
            doc_ids = [
                col.name.replace('doc_', '')
                for col in collections
                if col.name.startswith('doc_')
            ]
            return doc_ids
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return []


class LLMHandler:
    """Handler for LLM-based question answering"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize LLM handler

        Priority for API key:
        1. api_key parameter
        2. environment variable OPENAI_API_KEY
        """

        # Only parameter or env var — safest & correct
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model

        # Debug logging (never log full key)
        if self.api_key:
            key_preview = (
                f"{self.api_key[:8]}...{self.api_key[-4:]}"
                if len(self.api_key) > 12
                else "*" * len(self.api_key)
            )
            logger.info(f"✅ OpenAI API key found: {key_preview}")
        else:
            logger.warning("❌ No OpenAI API key found!")
            logger.warning("   Please set OPENAI_API_KEY in your environment.")

        # Initialize client
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                self.enabled = True
                logger.info(f"✅ LLM initialized successfully with model: {self.model}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize OpenAI client: {e}")
                self.client = None
                self.enabled = False
        else:
            self.client = None
            self.enabled = False


    
    def generate_answer(
        self,
        question: str,
        context_chunks: List[Dict],
        conversation_history: List[Dict] = None
    ) -> Dict:
        """
        Generate answer using LLM with retrieved context
        
        Args:
            question: User question
            context_chunks: Retrieved relevant chunks
            conversation_history: Previous conversation (optional)
        
        Returns:
            Answer with metadata
        """
        if not self.enabled:
            return {
                'answer': 'LLM not configured. Please set OPENAI_API_KEY environment variable.',
                'sources': [],
                'error': 'LLM not enabled'
            }
        
        try:
            # Build context from chunks
            context_text = "\n\n".join([
                f"[Page {chunk['metadata'].get('page_num', 'N/A')}] {chunk['text']}"
                for chunk in context_chunks
            ])
            
            # Build messages
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful AI assistant that answers questions based on PDF documents. "
                        "Use the provided context to answer questions accurately. "
                        "If the answer is not in the context, say so. "
                        "Always cite the page number when referencing information."
                    )
                }
            ]
            
            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history[-6:])  # Last 3 exchanges
            
            # Add current question with context
            messages.append({
                "role": "user",
                "content": f"Context from document:\n\n{context_text}\n\nQuestion: {question}"
            })
            
            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content
            
            # Extract sources
            sources = [
                {
                    'page_num': chunk['metadata'].get('page_num'),
                    'similarity_score': chunk['similarity_score'],
                    'text_preview': chunk['text'][:200] + '...'
                }
                for chunk in context_chunks[:3]  # Top 3 sources
            ]
            
            return {
                'answer': answer,
                'sources': sources,
                'model': self.model,
                'context_used': len(context_chunks)
            }
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return {
                'answer': f'Error generating answer: {str(e)}',
                'sources': [],
                'error': str(e)
            }

