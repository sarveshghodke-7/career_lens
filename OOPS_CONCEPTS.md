# CareerLens - OOP & Advanced Python Concepts Guide

This document provides a detailed, file-by-file breakdown of the **Object-Oriented Programming (OOP)** and **Advanced Python** concepts used in the refactored CareerLens application. This guide maps specific code blocks to their theoretical principles, explaining **what** the code does and **why** each concept is highly beneficial for professional software engineering.

---

## 1. File: `database.py`

### 1.1. Concept: Abstraction (Abstract Base Classes)
* **Code Block:**
  ```python
  from abc import ABC, abstractmethod

  class BaseDatabaseManager(ABC):
      @abstractmethod
      def setup_database(self) -> None:
          pass

      @abstractmethod
      def register_user(self, email: str, password: str, full_name: str, role: str = "candidate") -> Dict[str, Any]:
          pass

      @abstractmethod
      def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
          pass

      @abstractmethod
      def save_resume(self, user_id: Optional[int], file_name: str, file_path: str, raw_text: str) -> int:
          pass

      @abstractmethod
      def save_job_description(self, user_id: Optional[int], title: str, company: str, raw_text: str) -> int:
          pass

      @abstractmethod
      def save_result(self, filename: str, score: int, resume_id: Optional[int] = None, 
                      jd_id: Optional[int] = None, exact_matches: Optional[List[str]] = None,
                      semantic_matches: Optional[List[str]] = None, 
                      missing_keywords: Optional[List[str]] = None) -> int:
          pass

      @abstractmethod
      def get_score_history(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
          pass

      @abstractmethod
      def clear_history(self) -> None:
          pass
  ```
* **Explanation:**
  * **What it does:** Using Python's `abc` (Abstract Base Classes) module, this interface acts as a strict blueprint defining which methods any database service *must* implement. It cannot be instantiated on its own.
  * **Why it is beneficial:** It separates the database interface from its concrete storage implementation (SQLite, PostgreSQL, MySQL, etc.). If we decide to migrate from SQLite to a cloud database later, we only need to implement a new subclass of `BaseDatabaseManager` without modifying a single line of GUI code in `main.py`. This follows the **Dependency Inversion Principle (DIP)**.

### 1.2. Concept: Encapsulation
* **Code Block:**
  ```python
  class SQLiteDatabaseManager(BaseDatabaseManager):
      def __init__(self, db_path: str = "careerlens.db"):
          self._db_path = db_path  # Private attribute (prefixed with '_')

      @property
      def db_path(self) -> str:
          return self._db_path
  ```
* **Explanation:**
  * **What it does:** The database filename/path is stored in the private attribute `_db_path`. We provide read-only access to this variable using the `@property` decorator, preventing external components from modifying the database file path arbitrarily.
  * **Why it is beneficial:** It protects the internal state of the database manager, guaranteeing that the database path cannot be corrupted or mutated after the object is created.

### 1.3. Concept: Custom Context Managers (Magic Methods `__enter__` & `__exit__`)
* **Code Block:**
  ```python
  class SQLiteConnectionManager:
      def __init__(self, db_path: str):
          self._db_path = db_path
          self._conn = None

      def __enter__(self) -> sqlite3.Cursor:
          self._conn = sqlite3.connect(self._db_path)
          self._conn.row_factory = sqlite3.Row
          return self._conn.cursor()

      def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
          if self._conn:
              try:
                  if exc_type is not None:
                      self._conn.rollback()  # Rollback on failure
                  else:
                      self._conn.commit()    # Commit on success
              finally:
                  self._conn.close()         # Always close connection
          return False
  ```
* **Explanation:**
  * **What it does:** This class implements Python's context manager protocol via the `__enter__` and `__exit__` magic methods. It permits using the `with` statement:
    ```python
    with SQLiteConnectionManager(self._db_path) as cursor:
        cursor.execute(...)
    ```
  * **Why it is beneficial:** It guarantees that SQLite connections are closed and resources are released, even if an exception occurs during the database transaction. If an error is thrown, it automatically rolls back changes, preserving database transactional integrity. It removes duplicate open/close boilerplates across all functions.

---

## 2. File: `ats_logic.py`

### 2.1. Concept: Custom Decorators
* **Code Block:**
  ```python
  import time
  from functools import wraps

  def log_execution_time(func):
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
  ```
* **Explanation:**
  * **What it does:** The `@log_execution_time` decorator wraps high-overhead operations (like image OCR or spaCy lemmatization and similarity computations) to capture and output operational duration to the console. `@wraps(func)` preserves the metadata of the original function.
  * **Why it is beneficial:** It demonstrates clean separation of concerns. Instead of polluting business logic with execution logging statements, timing metrics are applied modularly as annotations above class methods.

### 2.2. Concept: Inheritance & Custom Exception Hierarchies
* **Code Block:**
  ```python
  class CareerLensError(Exception):
      """Base exception class for CareerLens."""
      pass

  class OcrExtractionError(CareerLensError):
      """Raised when image pre-processing or Tesseract OCR fails."""
      pass

  class AnalysisError(CareerLensError):
      """Raised when NLP scoring engine fails to process text."""
      pass
  ```
* **Explanation:**
  * **What it does:** It creates a custom error hierarchy. `CareerLensError` inherits from the built-in `Exception` class, and both `OcrExtractionError` and `AnalysisError` inherit from `CareerLensError`.
  * **Why it is beneficial:** It allows the application to handle domain-specific errors gracefully. In `main.py`, the GUI can catch specific exceptions individually (`OcrExtractionError`, `AnalysisError`) to show tailored dialogue boxes rather than throwing generic raw system failures.

### 2.3. Concept: Polymorphism
* **Code Block:**
  ```python
  class BaseTextExtractor(ABC):
      @abstractmethod
      def extract_text(self, filepath: str) -> str:
          pass

  class OcrTextExtractor(BaseTextExtractor):
      def extract_text(self, filepath: str) -> str:
          # Custom OpenCV + PyTesseract image processing
          ...

  class PdfTextExtractor(BaseTextExtractor):
      def extract_text(self, filepath: str) -> str:
          # Custom PDF text parsing
          ...
  ```
* **Explanation:**
  * **What it does:** Demonstrates **polymorphism through inheritance**. Both `OcrTextExtractor` and `PdfTextExtractor` share the same `BaseTextExtractor` signature interface but implement `extract_text` in completely different ways.
  * **Why it is beneficial:** The client code in `main.py` simply calls `self.extractor.extract_text(path)` without needing to know *how* text is being extracted or *what* file type it is. This is a classic example of **Polymorphism**, showing how easy it is to add a PDF or Word Document parser under the exact same interface.

### 2.4. Concept: Dataclasses & Magic (Dunder) Methods
* **Code Block:**
  ```python
  from dataclasses import dataclass

  @dataclass(frozen=True)
  class AnalysisResult:
      score: int
      exact_matches: List[str]
      semantic_matches: List[str]
      missing_keywords: List[str]

      def __repr__(self) -> str:
          return f"AnalysisResult(Score: {self.score}%, Matches: {len(self.exact_matches) + len(self.semantic_matches)}, Missing: {len(self.missing_keywords)})"

      def __len__(self) -> int:
          return len(self.exact_matches) + len(self.semantic_matches) + len(self.missing_keywords)
  ```
* **Explanation:**
  * **What it does:** 
    * `@dataclass(frozen=True)` makes the data container immutable and automatically implements standard boilerplate methods like `__init__` and `__eq__`.
    * `__repr__` replaces the default memory-address string representation with a highly informative debug print format.
    * `__len__` is overridden so that calling `len(result)` returns the total number of keywords evaluated.
  * **Why it is beneficial:** Avoids using raw dictionaries or tuples to pass analysis details, making data manipulation type-safe and self-documenting.

### 2.5. Concept: Class Methods & Lazy Loading
* **Code Block:**
  ```python
  class ResumeScoringEngine:
      _nlp = None

      @classmethod
      def get_nlp_model(cls) -> Any:
          if cls._nlp is None:
              print("Loading AI Model (spaCy en_core_web_md)...")
              cls._nlp = spacy.load("en_core_web_md")
              print("spaCy Model Loaded!")
          return cls._nlp
  ```
* **Explanation:**
  * **What it does:** Uses a classmethod to lazily initialize the massive spaCy language model. The model is only loaded into RAM when `get_nlp_model` is invoked for the first time, not during application boot.
  * **Why it is beneficial:** Prevents long initial application launch freezes and saves significant memory overhead if the user launches the GUI only to check their dashboard history without performing a new resume analysis scan.

---

## 3. File: `main.py`

### 3.1. Concept: Dependency Injection (DI)
* **Code Block:**
  ```python
  class CareerLensApp:
      def __init__(self, root: tk.Tk, db_manager: BaseDatabaseManager, extractor: BaseTextExtractor, scoring_engine: ResumeScoringEngine):
          self.root = root
          self.db_manager = db_manager
          self.extractor = extractor
          self.scoring_engine = scoring_engine
          ...
  ```
* **Explanation:**
  * **What it does:** Instead of instantiating database and extractor services directly inside `CareerLensApp`, we "inject" them as concrete objects conforming to our abstract interfaces through the class constructor.
  * **Why it is beneficial:** It makes the application highly testable and loosely coupled. During unit testing, we can inject a mock Database Manager or a mock Text Extractor that doesn't touch the filesystem or run complex OCR engines, enabling fast, isolated testing of GUI elements.

### 3.2. Concept: Type Hinting & Annotations
* **Code Block:**
  ```python
  def display_results(self, result: AnalysisResult) -> None:
      ...
  ```
* **Explanation:**
  * **What it does:** Integrates modern PEP-484 type declarations defining the expected parameter types and function return values.
  * **Why it is beneficial:** Greatly improves readability, prevents bugs during refactoring, and enables IDEs to catch type-mismatch mistakes during development.
