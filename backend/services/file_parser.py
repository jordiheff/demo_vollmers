"""
File parsing service for extracting text and images from PDFs and images.
"""

import base64
import io
from typing import Optional, Tuple, List

import fitz  # PyMuPDF
from PIL import Image

# pytesseract is optional - OCR fallback
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


class FileParser:
    """Extract text content and images from PDF and image files."""

    @staticmethod
    def parse_base64(content: str, file_type: str) -> str:
        """
        Parse base64-encoded file content and extract text.

        NOTE: For better accuracy with tables, use parse_base64_as_images() instead.

        Args:
            content: Base64-encoded file content
            file_type: Type of file ("pdf", "image", or "text")

        Returns:
            Extracted text content
        """
        if file_type == "text":
            # Plain text, just decode
            return base64.b64decode(content).decode("utf-8")

        # Decode base64 to bytes
        file_bytes = base64.b64decode(content)

        if file_type == "pdf":
            return FileParser._parse_pdf(file_bytes)
        elif file_type == "image":
            return FileParser._parse_image(file_bytes)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    @staticmethod
    def parse_base64_as_images(content: str, file_type: str) -> List[str]:
        """
        Parse base64-encoded file and return as base64-encoded images.

        This is the preferred method for documents with tables, as it
        preserves visual structure for vision-based LLM extraction.

        Args:
            content: Base64-encoded file content
            file_type: Type of file ("pdf", "image", or "text")

        Returns:
            List of base64-encoded PNG images (one per page for PDFs)
        """
        file_bytes = base64.b64decode(content)

        if file_type == "pdf":
            return FileParser._pdf_to_images(file_bytes)
        elif file_type == "image":
            # Already an image, just ensure it's PNG format
            image = Image.open(io.BytesIO(file_bytes))
            if image.mode != "RGB":
                image = image.convert("RGB")
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            return [base64.b64encode(buffer.getvalue()).decode("utf-8")]
        elif file_type == "text":
            # Can't convert text to image, return empty
            return []
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    @staticmethod
    def _pdf_to_images(file_bytes: bytes, dpi: int = 200) -> List[str]:
        """
        Convert PDF pages to base64-encoded PNG images.

        Args:
            file_bytes: Raw PDF file bytes
            dpi: Resolution for rendering (higher = better quality but larger)

        Returns:
            List of base64-encoded PNG images
        """
        images = []
        doc = fitz.open(stream=file_bytes, filetype="pdf")

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            # Render page to image
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat)

            # Convert to PNG bytes
            img_bytes = pix.tobytes("png")

            # Encode to base64
            img_base64 = base64.b64encode(img_bytes).decode("utf-8")
            images.append(img_base64)

        doc.close()
        return images

    @staticmethod
    def _parse_pdf(file_bytes: bytes) -> str:
        """
        Extract text from PDF using PyMuPDF.

        Args:
            file_bytes: Raw PDF file bytes

        Returns:
            Extracted text from all pages
        """
        text_parts = []

        # Open PDF from bytes
        doc = fitz.open(stream=file_bytes, filetype="pdf")

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)

            # Extract text
            text = page.get_text()

            if text.strip():
                text_parts.append(text)
            else:
                # If no text found, try OCR on page image
                if TESSERACT_AVAILABLE:
                    pix = page.get_pixmap(dpi=300)
                    img_bytes = pix.tobytes("png")
                    ocr_text = FileParser._ocr_image(img_bytes)
                    if ocr_text.strip():
                        text_parts.append(ocr_text)

        doc.close()

        return "\n\n".join(text_parts)

    @staticmethod
    def _parse_image(file_bytes: bytes) -> str:
        """
        Extract text from image using OCR.

        Args:
            file_bytes: Raw image file bytes

        Returns:
            OCR-extracted text
        """
        if not TESSERACT_AVAILABLE:
            raise RuntimeError(
                "Tesseract OCR is not available. "
                "Please install pytesseract and Tesseract OCR."
            )

        return FileParser._ocr_image(file_bytes)

    @staticmethod
    def _ocr_image(image_bytes: bytes) -> str:
        """
        Perform OCR on image bytes.

        Args:
            image_bytes: Raw image bytes (PNG, JPG, etc.)

        Returns:
            OCR-extracted text
        """
        if not TESSERACT_AVAILABLE:
            return ""

        # Open image with PIL
        image = Image.open(io.BytesIO(image_bytes))

        # Convert to RGB if necessary (handles RGBA, grayscale, etc.)
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Run OCR
        text = pytesseract.image_to_string(image, lang="eng")

        return text

    @staticmethod
    def detect_file_type(filename: str) -> str:
        """
        Detect file type from filename extension.

        Args:
            filename: Original filename

        Returns:
            File type string ("pdf", "image", or "text")
        """
        filename_lower = filename.lower()

        if filename_lower.endswith(".pdf"):
            return "pdf"
        elif filename_lower.endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp")):
            return "image"
        elif filename_lower.endswith((".txt", ".csv")):
            return "text"
        else:
            # Default to text for unknown types
            return "text"
