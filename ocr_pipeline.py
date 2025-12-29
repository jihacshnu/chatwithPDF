"""
OCR Pipeline Module
Handles text extraction from PDFs using native text extraction, PaddleOCR,
table extraction with Camelot, and form field detection
"""

import os
import cv2
import numpy as np
import fitz  # PyMuPDF
from pdf2image import convert_from_path
from paddleocr import PaddleOCR
from PIL import Image
import logging
import camelot
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OCRPipeline:
    """OCR processing pipeline for PDF documents with table and form extraction"""
    
    def __init__(self):
        """Initialize PaddleOCR with English language support"""
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang='en'
        )
    
    def extract_native_text(self, pdf_path: str, page_num: int) -> str:
        """
        Extract native text from PDF page using PyMuPDF
        
        Args:
            pdf_path: Path to PDF file
            page_num: Page number (0-indexed)
        
        Returns:
            Extracted text string
        """
        try:
            doc = fitz.open(pdf_path)
            page = doc[page_num]
            text = page.get_text().strip()
            doc.close()
            return text
        except Exception as e:
            logger.error(f"Error extracting native text from page {page_num}: {e}")
            return ""
    
    def extract_tables(self, pdf_path: str, page_num: int) -> list:
        """
        Extract tables from PDF page using Camelot
        
        Args:
            pdf_path: Path to PDF file
            page_num: Page number (1-indexed for Camelot)
        
        Returns:
            List of dictionaries containing table data
        """
        tables_data = []
        try:
            # Try lattice method first (for tables with lines)
            tables = camelot.read_pdf(
                pdf_path,
                pages=str(page_num + 1),
                flavor='lattice'
            )
            
            # If no tables found with lattice, try stream method
            if len(tables) == 0:
                tables = camelot.read_pdf(
                    pdf_path,
                    pages=str(page_num + 1),
                    flavor='stream'
                )
            
            for idx, table in enumerate(tables):
                # Convert table to dict format
                df = table.df
                
                # Clean up the dataframe
                if not df.empty:
                    table_dict = {
                        'table_id': idx + 1,
                        'accuracy': round(table.parsing_report['accuracy'], 2),
                        'rows': len(df),
                        'columns': len(df.columns),
                        'data': df.values.tolist(),
                        'headers': df.iloc[0].tolist() if len(df) > 0 else [],
                        'markdown': df.to_markdown(index=False)
                    }
                    tables_data.append(table_dict)
                    logger.info(f"Extracted table {idx + 1} from page {page_num + 1} with accuracy {table.parsing_report['accuracy']:.2f}")
            
        except Exception as e:
            logger.warning(f"Error extracting tables from page {page_num + 1}: {e}")
        
        return tables_data
    
    def extract_form_fields(self, pdf_path: str, page_num: int) -> list:
        """
        Extract form fields from PDF page using PyMuPDF
        
        Args:
            pdf_path: Path to PDF file
            page_num: Page number (0-indexed)
        
        Returns:
            List of dictionaries containing form field data
        """
        form_fields = []
        try:
            doc = fitz.open(pdf_path)
            page = doc[page_num]
            
            # Get widgets (form fields) on the page
            widgets = page.widgets()
            
            if widgets:
                for widget in widgets:
                    field_info = {
                        'field_name': widget.field_name or 'unnamed',
                        'field_type': widget.field_type_string,
                        'field_value': widget.field_value or '',
                        'field_label': widget.field_label or '',
                        'is_readonly': widget.field_flags & (1 << 0) != 0,
                        'is_required': widget.field_flags & (1 << 1) != 0,
                        'position': {
                            'x': round(widget.rect.x0, 2),
                            'y': round(widget.rect.y0, 2),
                            'width': round(widget.rect.width, 2),
                            'height': round(widget.rect.height, 2)
                        }
                    }
                    form_fields.append(field_info)
                    logger.info(f"Found form field: {field_info['field_name']} ({field_info['field_type']})")
            
            doc.close()
            
        except Exception as e:
            logger.warning(f"Error extracting form fields from page {page_num + 1}: {e}")
        
        return form_fields
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better OCR results
        
        Args:
            image: Input image as numpy array
        
        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Deskew
        coords = np.column_stack(np.where(denoised > 0))
        if len(coords) > 0:
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            
            # Only deskew if angle is significant
            if abs(angle) > 0.5:
                (h, w) = denoised.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                denoised = cv2.warpAffine(
                    denoised, M, (w, h),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE
                )
        
        # Adaptive thresholding for better contrast
        thresh = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )
        
        return thresh
    
    def pdf_page_to_image(self, pdf_path: str, page_num: int) -> np.ndarray:
        """
        Convert PDF page to image
        
        Args:
            pdf_path: Path to PDF file
            page_num: Page number (1-indexed for pdf2image)
        
        Returns:
            Image as numpy array
        """
        try:
            images = convert_from_path(
                pdf_path,
                first_page=page_num + 1,
                last_page=page_num + 1,
                dpi=300
            )
            if images:
                # Convert PIL Image to numpy array
                img_array = np.array(images[0])
                return img_array
            return None
        except Exception as e:
            logger.error(f"Error converting page {page_num} to image: {e}")
            return None
    
    def run_ocr(self, image: np.ndarray) -> tuple[str, float]:
        """
        Run PaddleOCR on preprocessed image
        
        Args:
            image: Preprocessed image as numpy array
        
        Returns:
            Tuple of (extracted_text, average_confidence)
        """
        try:
            result = self.ocr.ocr(image, cls=True)
            
            if not result or not result[0]:
                return "", 0.0
            
            texts = []
            confidences = []
            
            for line in result[0]:
                if line:
                    text = line[1][0]
                    confidence = line[1][1]
                    texts.append(text)
                    confidences.append(confidence)
            
            extracted_text = "\n".join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return extracted_text, avg_confidence
            
        except Exception as e:
            logger.error(f"Error running OCR: {e}")
            return "", 0.0
    
    def process_pdf(self, pdf_path: str) -> dict:
        """
        Process entire PDF and extract text, tables, and forms from all pages
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Dictionary containing processing results
        """
        try:
            doc = fitz.open(pdf_path)
            num_pages = len(doc)
            doc.close()
            
            results = {
                "file": os.path.basename(pdf_path),
                "pages": []
            }
            
            for page_num in range(num_pages):
                logger.info(f"Processing page {page_num + 1}/{num_pages}")
                
                page_result = {
                    "page_num": page_num + 1,
                    "text": "",
                    "source": "",
                    "confidence": 0.0,
                    "tables": [],
                    "forms": []
                }
                
                # Extract tables
                logger.info(f"Page {page_num + 1}: Extracting tables...")
                tables = self.extract_tables(pdf_path, page_num)
                page_result["tables"] = tables
                
                # Extract form fields
                logger.info(f"Page {page_num + 1}: Extracting form fields...")
                forms = self.extract_form_fields(pdf_path, page_num)
                page_result["forms"] = forms
                
                # Try native text extraction
                native_text = self.extract_native_text(pdf_path, page_num)
                
                if native_text and len(native_text.strip()) > 50:
                    # Native text is substantial
                    page_result["text"] = native_text
                    page_result["source"] = "native"
                    page_result["confidence"] = 1.0
                    logger.info(f"Page {page_num + 1}: Using native text")
                else:
                    # Need OCR
                    logger.info(f"Page {page_num + 1}: No native text, running OCR")
                    
                    # Convert page to image
                    image = self.pdf_page_to_image(pdf_path, page_num)
                    
                    if image is not None:
                        # Preprocess image
                        preprocessed = self.preprocess_image(image)
                        
                        # Run OCR
                        ocr_text, confidence = self.run_ocr(preprocessed)
                        
                        page_result["text"] = ocr_text
                        page_result["source"] = "ocr"
                        page_result["confidence"] = round(confidence, 4)
                        logger.info(f"Page {page_num + 1}: OCR completed with confidence {confidence:.2f}")
                    else:
                        page_result["source"] = "error"
                        logger.error(f"Page {page_num + 1}: Failed to convert to image")
                
                results["pages"].append(page_result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            raise
