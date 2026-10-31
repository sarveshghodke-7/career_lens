import cv2
import pytesseract
import os
import spacy
import time
from abc import ABC, abstractmethod
from functools import wraps
from dataclasses import dataclass
from typing import List, Tuple, Set, Dict, Any

# ==========================================
# 1. ADVANCED PYTHON: CUSTOM DECORATOR
# ==========================================
def log_execution_time(func):
    """
    Advanced Python: Custom Decorator.
    Logs the execution duration of the decorated function to the terminal.
    Uses functools.wraps to preserve function metadata (docstring, name, etc.).
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"[TIMING] {func.__name__} took {elapsed_time:.4f} seconds to execute.")
    return wrapper


# ==========================================
# 2. OOP CONCEPT: INHERITANCE (CUSTOM EXCEPTIONS)
# ==========================================
class CareerLensError(Exception):
    """
    OOP Concept: Inheritance.
    Base class for all custom exceptions in CareerLens.
    """
    pass


class OcrExtractionError(CareerLensError):
    """
    OOP Concept: Inheritance.
    Raised when image pre-processing or Tesseract OCR fails.
    """
    pass


class AnalysisError(CareerLensError):
    """
    OOP Concept: Inheritance.
    Raised when NLP scoring engine fails to process text.
    """
    pass


# ==========================================
# 3. ADVANCED PYTHON: DATACLASS & MAGIC METHODS
# ==========================================
@dataclass(frozen=True)
class AnalysisResult:
    """
    Advanced Python: Dataclass.
    Creates an immutable data holder for NLP analysis results.
    Includes custom magic methods (__repr__, __len__) for advanced object behavior.
    """
    score: int
    exact_matches: List[str]
    semantic_matches: List[str]
    missing_keywords: List[str]

    def __repr__(self) -> str:
        """Magic Method: Custom string representation."""
        return f"AnalysisResult(Score: {self.score}%, Matches: {len(self.exact_matches) + len(self.semantic_matches)}, Missing: {len(self.missing_keywords)})"

    def __len__(self) -> int:
        """Magic Method: Returns the total number of processed job description keywords."""
        return len(self.exact_matches) + len(self.semantic_matches) + len(self.missing_keywords)


# ==========================================
# 4. OOP CONCEPT: ABSTRACTION & POLYMORPHISM (TEXT EXTRACTOR)
# ==========================================
class BaseTextExtractor(ABC):
    """
    OOP Concept: Abstraction.
    Defines the abstract base class for text extraction services.
    """
    @abstractmethod
    def extract_text(self, filepath: str) -> str:
        """Extract text from the given file."""
        pass


class OcrTextExtractor(BaseTextExtractor):
    """
    OOP Concept: Inheritance & Encapsulation.
    Extracts text from images using OpenCV and PyTesseract OCR.
    """
    def __init__(self, tesseract_cmd_path: str = r'D:\Tr-OCR\tesseract.exe'):
        # Encapsulate the command path configuration
        self._tesseract_cmd_path = tesseract_cmd_path
        pytesseract.pytesseract.tesseract_cmd = self._tesseract_cmd_path

    def _process_image_with_opencv(self, filepath: str) -> Any:
        """
        OOP Concept: Encapsulation.
        Helper private method to preprocess image using OpenCV.
        """
        img = cv2.imread(filepath)
        if img is None:
            raise OcrExtractionError("Could not read image. Ensure it is a valid PNG/JPG.")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        return thresh

    @log_execution_time
    def extract_text(self, filepath: str) -> str:
        """
        OOP Concept: Polymorphism.
        Concrete implementation of the extract_text interface.
        """
        try:
            processed_img = self._process_image_with_opencv(filepath)
            text = pytesseract.image_to_string(processed_img)
            return text.lower()
        except OcrExtractionError:
            raise
        except Exception as e:
            raise OcrExtractionError(f"OCR text extraction failed: {str(e)}") from e


class PdfTextExtractor(BaseTextExtractor):
    """
    OOP Concept: Polymorphism (Extensibility Example).
    A placeholder subclass showing that the system can support different extractors
    under the same BaseTextExtractor interface.
    """
    def extract_text(self, filepath: str) -> str:
        # Placeholder that could represent extracting text from a PDF
        return "this is a mock resume text representing a pdf file content."


# ==========================================
# 5. OOP CONCEPT: ENCAPSULATION (SCORING ENGINE)
# ==========================================
class ResumeScoringEngine:
    """
    OOP Concept: Encapsulation.
    This class encapsulates the spaCy NLP model and the resume-job description scoring logic.
    It demonstrates classmethods, lazy loading of expensive models, and static helper methods.
    """
    _nlp = None

    def __init__(self):
        # Trigger model load on instantiation
        self.get_nlp_model()

    @classmethod
    def get_nlp_model(cls) -> Any:
        """
        Advanced Python: Classmethod with Lazy Loading.
        The spaCy language model is loaded once on-demand when first requested, saving startup time and memory.
        """
        if cls._nlp is None:
            print("Loading AI Model (spaCy en_core_web_md)...")
            cls._nlp = spacy.load("en_core_web_md")
            print("spaCy Model Loaded!")
        return cls._nlp

    @log_execution_time
    def calculate_ats_score(self, resume_text: str, job_description: str) -> AnalysisResult:
        """
        Advanced ATS scoring using NLP Lemmatization and Word Vectors.
        Encapsulates exact match and semantic match extraction.
        """
        try:
            nlp = self.get_nlp_model()
            
            # 1. Process texts through the NLP pipeline
            doc_jd = nlp(job_description.lower())
            doc_res = nlp(resume_text.lower())
        
            # 2. Extract meaningful 'lemmas' (base words) ignoring punctuation and stop words
            jd_words = {token.lemma_ for token in doc_jd if not token.is_stop and not token.is_punct and not token.is_space}
            res_words = {token.lemma_ for token in doc_res if not token.is_stop and not token.is_punct and not token.is_space}
        
            # 3. Find Exact Matches
            exact_matches = jd_words.intersection(res_words)
            missing_initially = jd_words.difference(res_words)
        
            semantic_matches = set()
            still_missing = set()
        
            # Create a list of resume tokens that have vectors for fast comparison
            res_tokens_for_sim = [nlp(w)[0] for w in res_words if nlp(w)[0].has_vector]
        
            # 4. Check missing words for Semantic (Meaning) Matches
            for w in missing_initially:
                t1 = nlp(w)[0] # Get the vector for the missing JD word
                
                if not t1.has_vector:
                    still_missing.add(w)
                    continue
        
                best_sim = 0.0
                # Compare it against every word in the resume
                for t2 in res_tokens_for_sim:
                    sim = t1.similarity(t2)
                    if sim > best_sim:
                        best_sim = sim
        
                # If the word is 75% or more similar to a word in the resume, count it as a match!
                if best_sim >= 0.75: 
                    semantic_matches.add(w)
                else:
                    still_missing.add(w)
        
            # 5. Calculate Final Score
            total_jd_keywords = len(jd_words)
            total_matches = len(exact_matches) + len(semantic_matches)
            
            score = int((total_matches / total_jd_keywords) * 100) if total_jd_keywords > 0 else 0
        
            return AnalysisResult(
                score=score,
                exact_matches=list(exact_matches),
                semantic_matches=list(semantic_matches),
                missing_keywords=list(still_missing)
            )
        except Exception as e:
            raise AnalysisError(f"Failed to calculate ATS score: {str(e)}") from e