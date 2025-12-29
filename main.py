"""
FastAPI Backend for PDF OCR and Chat Processing
"""

import os
import tempfile
import logging
import hashlib
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from ocr_pipeline import OCRPipeline
from rag_pipeline import RAGPipeline, LLMHandler

# Load environment variables from .env file
load_dotenv()

# OPENAI_API_KEY will be loaded from .env file
# OPENAI_API_KEY = "sk-..."

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ChatPDF Service",
    description="Backend API for PDF text extraction, table/form detection, and intelligent Q&A",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize pipelines (lazy loading)
ocr_pipeline = None
rag_pipeline = None
llm_handler = None

# Store document metadata
documents_db = {}  # In-memory storage (use database in production)


# Pydantic models for request/response
class ChatRequest(BaseModel):
    document_id: str
    question: str
    conversation_history: Optional[List[dict]] = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]
    document_id: str
    model: Optional[str] = None


def get_ocr_pipeline() -> OCRPipeline:
    """Get or initialize OCR pipeline"""
    global ocr_pipeline
    if ocr_pipeline is None:
        logger.info("Initializing OCR pipeline...")
        ocr_pipeline = OCRPipeline()
        logger.info("OCR pipeline initialized successfully")
    return ocr_pipeline


def get_rag_pipeline() -> RAGPipeline:
    """Get or initialize RAG pipeline"""
    global rag_pipeline
    if rag_pipeline is None:
        logger.info("Initializing RAG pipeline...")
        rag_pipeline = RAGPipeline(persist_directory="./chroma_db")
        logger.info("RAG pipeline initialized successfully")
    return rag_pipeline


import os

def get_llm_handler() -> LLMHandler:
    global llm_handler
    if llm_handler is None:
        logger.info("Initializing LLM handler...")
        
        # Load from environment variable ONLY
        api_key = os.getenv("OPENAI_API_KEY")

        llm_handler = LLMHandler(api_key=api_key)
        logger.info("LLM handler initialized")
    
    return llm_handler


def generate_document_id(filename: str, content: bytes) -> str:
    """Generate unique document ID from filename and content hash"""
    content_hash = hashlib.md5(content).hexdigest()[:8]
    clean_filename = Path(filename).stem.replace(' ', '_')[:20]
    return f"{clean_filename}_{content_hash}"


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "ChatPDF Service",
        "version": "2.0.0",
        "features": ["OCR", "Tables", "Forms", "Chat", "RAG"]
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint"""
    # Initialize LLM handler to check status
    llm = get_llm_handler()
    return {
        "status": "healthy",
        "ocr_initialized": ocr_pipeline is not None,
        "rag_initialized": rag_pipeline is not None,
        "llm_initialized": llm is not None and llm.enabled
    }


@app.post("/upload")
async def upload_and_process_pdf(file: UploadFile = File(...)):
    """
    Upload and process PDF: OCR + add to vector database for chat
    
    Args:
        file: PDF file uploaded via multipart/form-data
    
    Returns:
        JSON with document_id, OCR results, and processing status
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    temp_file = None
    try:
        # Read file content
        content = await file.read()
        
        # Generate document ID
        document_id = generate_document_id(file.filename, content)
        
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp:
            temp.write(content)
            temp_file = temp.name
        
        logger.info(f"Processing file: {file.filename} as document_id: {document_id}")
        
        # Get pipelines
        ocr_pipe = get_ocr_pipeline()
        rag_pipe = get_rag_pipeline()
        
        # Step 1: Process PDF with OCR
        logger.info(f"Running OCR on {file.filename}...")
        ocr_result = ocr_pipe.process_pdf(temp_file)
        
        # Step 2: Add to vector database
        logger.info(f"Adding document to vector database...")
        rag_summary = rag_pipe.add_document(
            document_id=document_id,
            ocr_result=ocr_result,
            metadata={'filename': file.filename}
        )
        
        # Store document metadata
        documents_db[document_id] = {
            'document_id': document_id,
            'filename': file.filename,
            'total_pages': len(ocr_result['pages']),
            'total_chunks': rag_summary['total_chunks'],
            'status': 'ready'
        }
        
        logger.info(f"Successfully processed {file.filename} -> {document_id}")
        
        return JSONResponse(content={
            'document_id': document_id,
            'filename': file.filename,
            'status': 'success',
            'ocr_result': ocr_result,
            'rag_summary': rag_summary,
            'message': 'Document processed successfully. You can now ask questions!'
        })
        
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    
    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
                logger.info(f"Cleaned up temporary file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to delete temporary file: {e}")


@app.post("/chat")
async def chat_with_document(chat_request: ChatRequest):
    """
    Ask questions about an uploaded document
    
    Args:
        chat_request: Contains document_id, question, and optional conversation history
    
    Returns:
        Answer with sources and metadata
    """
    try:
        document_id = chat_request.document_id
        question = chat_request.question
        
        # Check if document exists
        if document_id not in documents_db:
            raise HTTPException(
                status_code=404,
                detail=f"Document '{document_id}' not found. Please upload it first."
            )
        
        logger.info(f"Question for {document_id}: {question}")
        
        # Get pipelines
        rag_pipe = get_rag_pipeline()
        llm = get_llm_handler()
        
        # Step 1: Retrieve relevant chunks
        relevant_chunks = rag_pipe.retrieve_relevant_chunks(
            document_id=document_id,
            query=question,
            top_k=5
        )
        
        if not relevant_chunks:
            return JSONResponse(content={
                'answer': 'I could not find relevant information in the document to answer your question.',
                'sources': [],
                'document_id': document_id
            })
        
        # Step 2: Generate answer with LLM
        result = llm.generate_answer(
            question=question,
            context_chunks=relevant_chunks,
            conversation_history=chat_request.conversation_history
        )
        
        result['document_id'] = document_id
        
        return JSONResponse(content=result)
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")


@app.get("/documents")
async def list_documents():
    """
    List all uploaded documents
    
    Returns:
        List of documents with metadata
    """
    return {
        'documents': list(documents_db.values()),
        'total': len(documents_db)
    }


@app.get("/documents/{document_id}")
async def get_document_info(document_id: str):
    """
    Get information about a specific document
    
    Args:
        document_id: Document identifier
    
    Returns:
        Document metadata
    """
    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found")
    
    return documents_db[document_id]


@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document and its vector database
    
    Args:
        document_id: Document identifier
    
    Returns:
        Deletion status
    """
    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found")
    
    try:
        # Delete from vector database
        rag_pipe = get_rag_pipeline()
        rag_pipe.delete_document(document_id)
        
        # Delete from metadata
        del documents_db[document_id]
        
        logger.info(f"Deleted document: {document_id}")
        
        return {
            'status': 'success',
            'message': f'Document {document_id} deleted successfully'
        }
        
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")


@app.post("/ocr")
async def process_pdf_ocr_only(file: UploadFile = File(...)):
    """
    Process PDF and extract text, tables, and forms (OCR only, no chat)
    
    Args:
        file: PDF file uploaded via multipart/form-data
    
    Returns:
        JSON response with extracted text, tables, and form fields from all pages
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    temp_file = None
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp:
            content = await file.read()
            temp.write(content)
            temp_file = temp.name
        
        logger.info(f"Processing file: {file.filename} ({len(content)} bytes)")
        
        # Get OCR pipeline
        pipeline = get_ocr_pipeline()
        
        # Process PDF
        result = pipeline.process_pdf(temp_file)
        
        logger.info(f"Successfully processed {file.filename}")
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    
    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
                logger.info(f"Cleaned up temporary file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to delete temporary file: {e}")


if __name__ == "__main__":
    import uvicorn
    
    # Run server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

# Run command:
# uvicorn main:app --reload --port 8000
