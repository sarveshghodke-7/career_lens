import sqlite3
import hashlib
import hmac
import secrets
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseDatabaseManager(ABC):
    """
    OOP Concept: Abstraction.
    This abstract base class defines the interface for database operations in CareerLens.
    Any concrete database manager (e.g., SQLite, PostgreSQL, MySQL) must inherit from this
    class and implement its abstract methods.
    """

    @abstractmethod
    def setup_database(self) -> None:
        """Initialize the database tables and indexes."""
        pass

    @abstractmethod
    def register_user(self, email: str, password: str, full_name: str, role: str = "candidate") -> Dict[str, Any]:
        """Register a new user in the database with salted password hashing."""
        pass

    @abstractmethod
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Verify user credentials and return user record if valid."""
        pass

    @abstractmethod
    def save_resume(self, user_id: Optional[int], file_name: str, file_path: str, raw_text: str) -> int:
        """Store an uploaded resume and its extracted text."""
        pass

    @abstractmethod
    def save_job_description(self, user_id: Optional[int], title: str, company: str, raw_text: str) -> int:
        """Save a target job description."""
        pass

    @abstractmethod
    def save_result(self, filename: str, score: int, resume_id: Optional[int] = None, 
                    jd_id: Optional[int] = None, exact_matches: Optional[List[str]] = None,
                    semantic_matches: Optional[List[str]] = None, 
                    missing_keywords: Optional[List[str]] = None) -> int:
        """Save a new ATS score result and granular skill matches to the database."""
        pass

    @abstractmethod
    def get_score_history(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve recent score history."""
        pass

    @abstractmethod
    def clear_history(self) -> None:
        """Clear all ATS history from the database."""
        pass


class SQLiteConnectionManager:
    """
    Advanced Python: Custom Context Manager.
    Manages SQLite database connections using __enter__ and __exit__ magic methods.
    Ensures safe resource acquisition and release, automatically committing transactions
    on success or rolling them back if an exception occurs. Enables foreign key enforcement.
    """
    def __init__(self, db_path: str):
        self._db_path = db_path
        self._conn = None

    def __enter__(self) -> sqlite3.Cursor:
        self._conn = sqlite3.connect(self._db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON;")
        return self._conn.cursor()

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if self._conn:
            try:
                if exc_type is not None:
                    # An error occurred: roll back changes
                    self._conn.rollback()
                else:
                    # Success: commit changes
                    self._conn.commit()
            finally:
                self._conn.close()
        # Propagate exceptions normally
        return False


class SQLiteDatabaseManager(BaseDatabaseManager):
    """
    OOP Concept: Inheritance & Encapsulation.
    This class inherits from BaseDatabaseManager and provides a concrete implementation
    using SQLite across all 5 normalized tables (users, resumes, job_descriptions,
    ats_history, skill_matches) adhering to 3NF.
    """
    def __init__(self, db_path: str = "careerlens.db"):
        self._db_path = db_path  # Encapsulation: Private attribute
        self.setup_database()

    @property
    def db_path(self) -> str:
        """Encapsulation: Getter property to read the database path safely."""
        return self._db_path

    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> str:
        """
        Cryptographic password hashing using PBKDF2-HMAC-SHA256 with dynamic salt.
        Format: salt$derived_key
        """
        if salt is None:
            salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
        return f"{salt}${pwd_hash}"

    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        """Verify cleartext password against stored salted hash using constant-time comparison."""
        try:
            salt, original_hash = stored_hash.split("$", 1)
            computed_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
            return hmac.compare_digest(computed_hash, original_hash)
        except Exception:
            return False

    def setup_database(self) -> None:
        """
        Initializes the 5 relational database tables and performance indexes according to 3NF.
        Also migrates legacy single-table databases seamlessly.
        """
        with SQLiteConnectionManager(self._db_path) as cursor:
            # 1. USERS TABLE
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'candidate' CHECK(role IN ('candidate', 'recruiter', 'admin')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')

            # 2. RESUMES TABLE
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS resumes (
                    resume_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    file_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    raw_text TEXT,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                );
            ''')

            # 3. JOB DESCRIPTIONS TABLE
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS job_descriptions (
                    jd_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    title TEXT NOT NULL,
                    company TEXT,
                    raw_text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
                );
            ''')

            # 4. ATS HISTORY TABLE (Core Project Table)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ats_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resume_id INTEGER,
                    jd_id INTEGER,
                    filename TEXT NOT NULL,
                    score INTEGER NOT NULL CHECK(score >= 0 AND score <= 100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (resume_id) REFERENCES resumes(resume_id) ON DELETE SET NULL,
                    FOREIGN KEY (jd_id) REFERENCES job_descriptions(jd_id) ON DELETE SET NULL
                );
            ''')

            # Handle migration if ats_history was created in earlier version without foreign keys
            cursor.execute("PRAGMA table_info(ats_history);")
            columns = [row["name"] for row in cursor.fetchall()]
            if "resume_id" not in columns:
                cursor.execute("ALTER TABLE ats_history ADD COLUMN resume_id INTEGER REFERENCES resumes(resume_id) ON DELETE SET NULL;")
            if "jd_id" not in columns:
                cursor.execute("ALTER TABLE ats_history ADD COLUMN jd_id INTEGER REFERENCES job_descriptions(jd_id) ON DELETE SET NULL;")

            # 5. SKILL MATCHES BREAKDOWN TABLE
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS skill_matches (
                    match_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    history_id INTEGER NOT NULL,
                    keyword TEXT NOT NULL,
                    match_type TEXT NOT NULL CHECK(match_type IN ('exact', 'semantic', 'missing')),
                    similarity_score REAL DEFAULT 1.0,
                    FOREIGN KEY (history_id) REFERENCES ats_history(id) ON DELETE CASCADE
                );
            ''')

            # PERFORMANCE INDEXES
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ats_history_created_at ON ats_history(created_at);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ats_history_score ON ats_history(score);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_skill_matches_history_id ON skill_matches(history_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_resumes_user_id ON resumes(user_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_descriptions_user_id ON job_descriptions(user_id);")

            # Seed default demo users if users table is empty
            cursor.execute("SELECT COUNT(*) AS count FROM users;")
            if cursor.fetchone()["count"] == 0:
                demo_users = [
                    ("sanskar@jnec.edu", self.hash_password("password123"), "Sanskar Shinde", "candidate"),
                    ("rohan@jnec.edu", self.hash_password("password123"), "Rohan Tarke", "candidate"),
                    ("aamer@jnec.edu", self.hash_password("password123"), "Syed Aamer", "candidate"),
                    ("sarvesh@jnec.edu", self.hash_password("password123"), "Sarvesh Ghodke", "candidate"),
                    ("recruiter@techcorp.com", self.hash_password("admin123"), "Campus Recruiter", "recruiter"),
                    ("admin@careerlens.ai", self.hash_password("admin123"), "System Admin", "admin")
                ]
                cursor.executemany(
                    "INSERT INTO users (email, password_hash, full_name, role) VALUES (?, ?, ?, ?);",
                    demo_users
                )

    def register_user(self, email: str, password: str, full_name: str, role: str = "candidate") -> Dict[str, Any]:
        """Registers a new user profile with salted password hash."""
        email_clean = email.strip().lower()
        if not email_clean or not password or not full_name.strip():
            raise ValueError("All fields are required for registration.")
        if role not in ('candidate', 'recruiter', 'admin'):
            role = 'candidate'

        hashed_password = self.hash_password(password)
        with SQLiteConnectionManager(self._db_path) as cursor:
            try:
                cursor.execute(
                    "INSERT INTO users (email, password_hash, full_name, role) VALUES (?, ?, ?, ?);",
                    (email_clean, hashed_password, full_name.strip(), role)
                )
                user_id = cursor.lastrowid
                return {
                    "user_id": user_id,
                    "email": email_clean,
                    "full_name": full_name.strip(),
                    "role": role
                }
            except sqlite3.IntegrityError:
                raise ValueError(f"An account with email '{email_clean}' already exists.")

    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Verifies credentials and returns user dictionary if authenticated, None otherwise."""
        email_clean = email.strip().lower()
        with SQLiteConnectionManager(self._db_path) as cursor:
            cursor.execute("SELECT user_id, email, password_hash, full_name, role FROM users WHERE email = ?;", (email_clean,))
            row = cursor.fetchone()
            if row and self.verify_password(password, row["password_hash"]):
                return {
                    "user_id": row["user_id"],
                    "email": row["email"],
                    "full_name": row["full_name"],
                    "role": row["role"]
                }
        return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Fetch user by ID."""
        with SQLiteConnectionManager(self._db_path) as cursor:
            cursor.execute("SELECT user_id, email, full_name, role, created_at FROM users WHERE user_id = ?;", (user_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    def get_all_users(self) -> List[Dict[str, Any]]:
        """Fetch all registered users."""
        with SQLiteConnectionManager(self._db_path) as cursor:
            cursor.execute("SELECT user_id, email, full_name, role, created_at FROM users ORDER BY user_id ASC;")
            return [dict(row) for row in cursor.fetchall()]

    def save_resume(self, user_id: Optional[int], file_name: str, file_path: str, raw_text: str) -> int:
        """Stores a resume record and returns its resume_id."""
        with SQLiteConnectionManager(self._db_path) as cursor:
            cursor.execute(
                "INSERT INTO resumes (user_id, file_name, file_path, raw_text) VALUES (?, ?, ?, ?);",
                (user_id, file_name, file_path, raw_text)
            )
            return cursor.lastrowid

    def save_job_description(self, user_id: Optional[int], title: str, company: str, raw_text: str) -> int:
        """Stores a job description and returns its jd_id."""
        with SQLiteConnectionManager(self._db_path) as cursor:
            cursor.execute(
                "INSERT INTO job_descriptions (user_id, title, company, raw_text) VALUES (?, ?, ?, ?);",
                (user_id, title, company, raw_text)
            )
            return cursor.lastrowid

    def save_result(self, filename: str, score: int, resume_id: Optional[int] = None, 
                    jd_id: Optional[int] = None, exact_matches: Optional[List[str]] = None,
                    semantic_matches: Optional[List[str]] = None, 
                    missing_keywords: Optional[List[str]] = None) -> int:
        """
        Saves scan result to ats_history and saves each keyword to skill_matches.
        Maintains backward compatibility with older save_result(filename, score) signature.
        """
        with SQLiteConnectionManager(self._db_path) as cursor:
            cursor.execute(
                "INSERT INTO ats_history (resume_id, jd_id, filename, score) VALUES (?, ?, ?, ?);",
                (resume_id, jd_id, filename, score)
            )
            history_id = cursor.lastrowid

            # Populate skill_matches table
            matches_data = []
            if exact_matches:
                for kw in exact_matches:
                    matches_data.append((history_id, kw, 'exact', 1.0))
            if semantic_matches:
                for kw in semantic_matches:
                    matches_data.append((history_id, kw, 'semantic', 0.85))
            if missing_keywords:
                for kw in missing_keywords:
                    matches_data.append((history_id, kw, 'missing', 0.0))

            if matches_data:
                cursor.executemany(
                    "INSERT INTO skill_matches (history_id, keyword, match_type, similarity_score) VALUES (?, ?, ?, ?);",
                    matches_data
                )

            return history_id

    def get_score_history(self, user_id: Optional[int] = None, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Fetches the recent scores from the database with resume & job details.
        Ordered oldest to newest for chronological plotting.
        """
        with SQLiteConnectionManager(self._db_path) as cursor:
            if user_id:
                query = '''
                    SELECT h.id, h.filename, h.score, h.created_at, h.resume_id, h.jd_id,
                           jd.title as job_title,
                           (SELECT COUNT(*) FROM skill_matches sm WHERE sm.history_id = h.id AND sm.match_type = 'exact') as exact_count,
                           (SELECT COUNT(*) FROM skill_matches sm WHERE sm.history_id = h.id AND sm.match_type = 'semantic') as semantic_count,
                           (SELECT COUNT(*) FROM skill_matches sm WHERE sm.history_id = h.id AND sm.match_type = 'missing') as missing_count
                    FROM ats_history h
                    LEFT JOIN resumes r ON h.resume_id = r.resume_id
                    LEFT JOIN job_descriptions jd ON h.jd_id = jd.jd_id
                    WHERE r.user_id = ?
                    ORDER BY h.id DESC LIMIT ?;
                '''
                cursor.execute(query, (user_id, limit))
            else:
                query = '''
                    SELECT h.id, h.filename, h.score, h.created_at, h.resume_id, h.jd_id,
                           jd.title as job_title,
                           (SELECT COUNT(*) FROM skill_matches sm WHERE sm.history_id = h.id AND sm.match_type = 'exact') as exact_count,
                           (SELECT COUNT(*) FROM skill_matches sm WHERE sm.history_id = h.id AND sm.match_type = 'semantic') as semantic_count,
                           (SELECT COUNT(*) FROM skill_matches sm WHERE sm.history_id = h.id AND sm.match_type = 'missing') as missing_count
                    FROM ats_history h
                    LEFT JOIN job_descriptions jd ON h.jd_id = jd.jd_id
                    ORDER BY h.id DESC LIMIT ?;
                '''
                cursor.execute(query, (limit,))

            rows = cursor.fetchall()
            results = [dict(row) for row in rows]

        return list(reversed(results))

    def get_scan_details(self, history_id: int) -> Optional[Dict[str, Any]]:
        """Fetch full details and all skill matches for a given scan."""
        with SQLiteConnectionManager(self._db_path) as cursor:
            cursor.execute('''
                SELECT h.id, h.filename, h.score, h.created_at, h.resume_id, h.jd_id,
                       jd.title as job_title, jd.company
                FROM ats_history h
                LEFT JOIN job_descriptions jd ON h.jd_id = jd.jd_id
                WHERE h.id = ?;
            ''', (history_id,))
            scan_row = cursor.fetchone()
            if not scan_row:
                return None

            scan_dict = dict(scan_row)
            cursor.execute('''
                SELECT keyword, match_type, similarity_score
                FROM skill_matches
                WHERE history_id = ?
                ORDER BY match_type ASC, keyword ASC;
            ''', (history_id,))
            scan_dict["matches"] = [dict(r) for r in cursor.fetchall()]
            return scan_dict

    def get_table_records(self, table_name: str, limit: int = 100) -> Dict[str, Any]:
        """
        Utility method for DBMS Table Inspector.
        Returns columns and up to `limit` rows from the specified table.
        """
        allowed_tables = ["users", "resumes", "job_descriptions", "ats_history", "skill_matches"]
        if table_name not in allowed_tables:
            raise ValueError(f"Table '{table_name}' is not an authorized CareerLens table.")

        with SQLiteConnectionManager(self._db_path) as cursor:
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = [col["name"] for col in cursor.fetchall()]

            cursor.execute(f"SELECT * FROM {table_name} ORDER BY 1 DESC LIMIT ?;", (limit,))
            rows = [dict(row) for row in cursor.fetchall()]

            cursor.execute(f"SELECT COUNT(*) AS total FROM {table_name};")
            total = cursor.fetchone()["total"]

            return {
                "table": table_name,
                "columns": columns,
                "rows": rows,
                "total_count": total
            }

    def clear_history(self) -> None:
        """
        OOP Concept: Encapsulation.
        Clears all records in ats_history and cascades to skill_matches.
        """
        with SQLiteConnectionManager(self._db_path) as cursor:
            cursor.execute("DELETE FROM skill_matches;")
            cursor.execute("DELETE FROM ats_history;")