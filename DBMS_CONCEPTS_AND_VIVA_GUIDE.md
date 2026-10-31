# CareerLens: Complete DBMS Project & Viva Voce Guide
### Subject: Database Management Systems Lab (DBMS Lab)
**Academic Year:** 2026–2027 | **Department:** Computer Science & Engineering | **College:** JNEC, MGM University  
**Project Title:** CareerLens: CV/Resume Analyser  
**Team Members:** Sanskar Shinde (202401103145), Rohan Tarke (202401103149), Syed Aamer (202401103150), Sarvesh Ghodke (202401103158)  
**Faculty Guide:** Prof. Sandip Kankal  

---

## Table of Contents
1. [Project Overview from a Database Perspective](#1-project-overview-from-a-database-perspective)
2. [ANSI/SPARC 3-Level Architecture Mapping](#2-ansisparc-3-level-architecture-mapping)
3. [Entity-Relationship (ER) Modeling & Cardinality](#3-entity-relationship-er-modeling--cardinality)
4. [Relational Integrity Constraints & Enterprise Rules](#4-relational-integrity-constraints--enterprise-rules)
5. [In-Depth Normalization Journey (UNF to 3NF/BCNF)](#5-in-depth-normalization-journey-unf-to-3nfbcnf)
6. [Transaction Management & ACID Properties](#6-transaction-management--acid-properties)
7. [Indexing, B-Trees & Query Optimization](#7-indexing-b-trees--query-optimization)
8. [Database Security & SQL Injection Prevention](#8-database-security--sql-injection-prevention)
9. [SQL Implementation Breakdown (DDL, DML, DQL & Advanced Queries)](#9-sql-implementation-breakdown)
10. [High-Yield DBMS Viva Voce Q&A (Examiner Favorites)](#10-high-yield-dbms-viva-voce-qa)
    - 10.1 Project Specific Questions
    - 10.2 Relational Model & Schema Design Questions
    - 10.3 Normalization & Dependency Questions
    - 10.4 Transactions, Concurrency & ACID Questions
    - 10.5 Indexing & Query Execution Questions
    - 10.6 SQL & Practical Mechanics Questions

---

## 1. Project Overview from a Database Perspective

### 1.1 What is CareerLens?
**CareerLens** is an intelligent CV/Resume analysis platform that accepts candidate resume image files, extracts text using Optical Character Recognition (OCR), tokenizes and matches qualifications against target Job Descriptions (JDs) using Natural Language Processing (NLP with 300D GloVe vector embeddings), and records every candidate, document, and screening evaluation in a fully normalized relational database.

### 1.2 Why is this a DBMS Project?
While the front-facing user interface handles file uploads and graphical visualization, the **core backbone of CareerLens is an ACID-compliant Relational Database Management System (RDBMS)**. Without a structured database:
- Resumes and candidate accounts would be scattered flat files.
- Screening metrics would lack historical continuity.
- Granular skill match diagnostics (exact vs. semantic vs. missing) could not be queried or filtered.
- Data would suffer from severe insertion, deletion, and update anomalies.

### 1.3 Key Database Metrics
- **Storage Engine:** SQLite3 (Serverless, Zero-Configuration, File-Based Transactional Database).
- **Schema Normalization:** Third Normal Form (3NF) and Boyce-Codd Normal Form (BCNF).
- **Number of Relational Entities:** 5 tables (`users`, `resumes`, `job_descriptions`, `ats_history`, `skill_matches`).
- **Integrity Enforcement:** Primary Keys, Composite Foreign Keys, Cascade Deletes, Domain Checks, Unique Constraints, and Custom Connection-Level Transaction Control.

---

## 2. ANSI/SPARC 3-Level Architecture Mapping

The standard database architecture divides a system into three discrete levels of abstraction. Here is how CareerLens implements them:

```
+-------------------------------------------------------------------------------+
|                       EXTERNAL LEVEL (User Views)                             |
|  - Candidate View: Sees own scores, uploaded resumes, and skill gap chart.    |
|  - Recruiter/Admin View: Sees global applicant rankings and DBMS Inspector.    |
+-------------------------------------------------------------------------------+
                                      |
                                      v  [Logical Data Independence]
+-------------------------------------------------------------------------------+
|                      CONCEPTUAL / LOGICAL LEVEL                               |
|  - Relational Schema: 5 Normalized Tables (3NF/BCNF).                         |
|  - Relationships: 1:N and M:N resolved via associative entity ats_history.     |
|  - Constraints: CHECK, FOREIGN KEY (CASCADE/SET NULL), UNIQUE, NOT NULL.      |
+-------------------------------------------------------------------------------+
                                      |
                                      v  [Physical Data Independence]
+-------------------------------------------------------------------------------+
|                       INTERNAL / PHYSICAL LEVEL                               |
|  - B-Tree Index storage inside single binary file: 'careerlens.db'.           |
|  - Journaling & Write-Ahead Logging (WAL) for durability and rollbacks.       |
|  - File paths to disk for binary images, storing raw OCR strings in TEXT.    |
+-------------------------------------------------------------------------------+
```

### Data Independence in CareerLens:
- **Logical Data Independence:** If we add a new column to `users` (e.g., `phone_number`), the database manager interface (`BaseDatabaseManager`) shields the GUI views from breaking.
- **Physical Data Independence:** If the storage changes from SQLite B-Tree disk pages to PostgreSQL or MySQL on a cloud server, only `database.py` requires a new concrete subclass; the rest of the application remains unchanged due to the Dependency Inversion Principle.

---

## 3. Entity-Relationship (ER) Modeling & Cardinality

### 3.1 Entity Classification
1. **USERS (Strong Entity):** Independent entity identified by primary key `user_id`.
2. **RESUMES (Strong Entity):** Represents resume metadata and extracted text, identified by `resume_id`.
3. **JOB_DESCRIPTIONS (Strong Entity):** Represents job postings and requirements, identified by `jd_id`.
4. **ATS_HISTORY (Associative / Junction Entity):** Represents an evaluation event. It resolves the $M:N$ relationship between `RESUMES` and `JOB_DESCRIPTIONS` while storing transaction attributes (`score`, `created_at`).
5. **SKILL_MATCHES (Dependent Entity):** Stores keyword-level diagnostics tied to an ATS scan via foreign key `history_id`.

### 3.2 Cardinality & Participation Constraints

| Relationship | Cardinality | Parent Table | Child Table | Participation Constraint | Action on Parent Deletion |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **Uploads** | $1 : N$ | `users` | `resumes` | Total (every resume must belong to a user) | `ON DELETE CASCADE` |
| **Creates** | $1 : N$ | `users` | `job_descriptions` | Partial (a user might not create JDs) | `ON DELETE SET NULL` |
| **Evaluated In** | $1 : N$ | `resumes` | `ats_history` | Partial (a resume may exist before scan) | `ON DELETE SET NULL` |
| **Targeted In** | $1 : N$ | `job_descriptions` | `ats_history` | Partial (a JD may exist before scan) | `ON DELETE SET NULL` |
| **Produces** | $1 : N$ | `ats_history` | `skill_matches` | Total (a skill match cannot exist without a scan) | `ON DELETE CASCADE` |
| **Resumes $\leftrightarrow$ JDs** | $M : N$ | `resumes` | `job_descriptions` | Resolved via `ats_history` junction table | Associative Entity |

---

## 4. Relational Integrity Constraints & Enterprise Rules

CareerLens implements all five standard relational database constraints:

### 4.1 Domain Integrity
- `score` must be an integer between 0 and 100:
  ```sql
  score INTEGER NOT NULL CHECK(score >= 0 AND score <= 100)
  ```
- `role` must be one of three predefined strings:
  ```sql
  role TEXT NOT NULL DEFAULT 'candidate' CHECK(role IN ('candidate', 'recruiter', 'admin'))
  ```
- `match_type` must match one of the three classification buckets:
  ```sql
  match_type TEXT NOT NULL CHECK(match_type IN ('exact', 'semantic', 'missing'))
  ```

### 4.2 Entity Integrity
- Every table has a non-null, unique **Primary Key** (`INTEGER PRIMARY KEY AUTOINCREMENT`), guaranteeing that no duplicate tuples exist.

### 4.3 Referential Integrity
- Enforced at connection time via `PRAGMA foreign_keys = ON;`.
- If an ATS history record is deleted, all dependent child rows in `skill_matches` are automatically purged:
  ```sql
  FOREIGN KEY (history_id) REFERENCES ats_history(id) ON DELETE CASCADE
  ```
- If a user is deleted, all their resumes are deleted (`ON DELETE CASCADE`), while job descriptions have their owner set to `NULL` (`ON DELETE SET NULL`).

### 4.4 Key & Uniqueness Constraints
- `email` is strictly unique across the system (`UNIQUE`), preventing duplicate account registrations.

---

## 5. In-Depth Normalization Journey (UNF to 3NF/BCNF)

A major focus of the DBMS viva is proving that your schema eliminates redundancy and anomalies.

### 5.1 Un-Normalized Form (UNF)
Imagine storing every resume scan in a single flat spreadsheet row:
```text
SCAN_FLAT(user_email, full_name, role, password, resume_file, resume_path,
          resume_raw_text, jd_title, company, jd_text, ats_score, scan_date,
          {keyword, match_type, similarity}*)
```
#### Problems in UNF:
1. **Repeating Groups:** Multiple keywords and matches exist in a single scan record.
2. **Massive Redundancy:** The candidate's name, password, resume text, and JD text are repeated for every scan.
3. **Anomalies:**
   - *Insertion Anomaly:* Cannot register a user until they scan a resume.
   - *Deletion Anomaly:* Deleting a scan record wipes out the candidate's account details.
   - *Update Anomaly:* If a company changes its name, we must update thousands of redundant rows.

---

### 5.2 First Normal Form (1NF)
> **Definition:** A relation is in 1NF if all attribute values are atomic (indivisible) and there are no repeating groups.

#### Transformation:
We extract the repeating group `{keyword, match_type, similarity}` into its own entity `skill_matches` with a surrogate primary key `match_id` and a foreign key `history_id`. Every column now holds an atomic scalar value.

---

### 5.3 Second Normal Form (2NF)
> **Definition:** A relation is in 2NF if it is in 1NF and every non-prime attribute is fully functionally dependent on the primary key (no partial functional dependencies).

#### Identifying Partial Dependencies:
If we kept a composite key like `(scan_id, keyword)`, attributes such as `resume_file`, `score`, and `jd_title` would depend only on `scan_id`, NOT on the composite key `(scan_id, keyword)`.
#### Resolution:
We split scan-level data into `ats_history` and keyword diagnostics into `skill_matches`. Because both tables use single-column primary keys (`id` and `match_id`), **partial functional dependency is mathematically impossible**.

---

### 5.4 Third Normal Form (3NF)
> **Definition:** A relation is in 3NF if it is in 2NF and no non-prime attribute is transitively dependent on the primary key ($X \to Y$ and $Y \to Z$).

#### Identifying Transitive Dependencies in the Scan Table:
1. `scan_id` $\to$ `user_email` $\to$ `full_name`, `role` (User details transitively dependent on `scan_id`).
2. `scan_id` $\to$ `resume_id` $\to$ `file_name`, `file_path`, `raw_text` (Resume details transitively dependent on `scan_id`).
3. `scan_id` $\to$ `jd_id` $\to$ `title`, `company`, `jd_text` (Job details transitively dependent on `scan_id`).

#### Resolution into 3NF:
We decompose the schema into five isolated relations:
1. `users (user_id, email, password_hash, full_name, role, created_at)`
2. `resumes (resume_id, user_id, file_name, file_path, raw_text, uploaded_at)`
3. `job_descriptions (jd_id, user_id, title, company, raw_text, created_at)`
4. `ats_history (id, resume_id, jd_id, filename, score, created_at)`
5. `skill_matches (match_id, history_id, keyword, match_type, similarity_score)`

---

### 5.5 Boyce-Codd Normal Form (BCNF)
> **Definition:** A relation is in BCNF if for every non-trivial functional dependency $X \to Y$, $X$ is a superkey.

Let us inspect the functional dependencies of each table:
1. `users`: $\text{user\_id} \to \{\text{email, password\_hash, full\_name, role, created\_at}\}$ ($\text{user\_id}$ is PK).
2. `resumes`: $\text{resume\_id} \to \{\text{user\_id, file\_name, file\_path, raw\_text, uploaded\_at}\}$ ($\text{resume\_id}$ is PK).
3. `job_descriptions`: $\text{jd\_id} \to \{\text{user\_id, title, company, raw\_text, created\_at}\}$ ($\text{jd\_id}$ is PK).
4. `ats_history`: $\text{id} \to \{\text{resume\_id, jd\_id, filename, score, created\_at}\}$ ($\text{id}$ is PK).
5. `skill_matches`: $\text{match\_id} \to \{\text{history\_id, keyword, match\_type, similarity\_score}\}$ ($\text{match\_id}$ is PK).

In every single dependency, the left-hand determinant is a superkey. Therefore, **the CareerLens database satisfies both 3NF and BCNF**.

---

## 6. Transaction Management & ACID Properties

In CareerLens, database interactions are strictly governed by **ACID properties** implemented via Python's Context Manager protocol in `SQLiteConnectionManager`.

```python
class SQLiteConnectionManager:
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
                    self._conn.rollback()  # Atomicity: Rollback on error
                else:
                    self._conn.commit()    # Durability: Commit on success
            finally:
                self._conn.close()         # Resource Cleanup
        return False
```

### ACID Analysis in CareerLens:

| Property | Meaning | How CareerLens Implements It |
| :--- | :--- | :--- |
| **Atomicity** | "All or Nothing". Either the whole transaction finishes, or zero changes persist. | When saving an ATS scan, rows must be added to `resumes`, `job_descriptions`, `ats_history`, and multiple rows to `skill_matches`. If the system crashes mid-way during skill insertion, `__exit__` catches the exception and calls `self._conn.rollback()`. No partial data is left behind. |
| **Consistency** | Database transitions from one valid state to another, obeying all constraints. | Schema checks (`score >= 0 AND score <= 100`), `NOT NULL`, and `PRAGMA foreign_keys = ON;` ensure an orphaned skill match cannot be saved without an existing parent `ats_history` record. |
| **Isolation** | Concurrent transactions cannot see each other’s uncommitted intermediate states. | SQLite locks the database file during write transactions (using table/file level locking and Write-Ahead Logging), ensuring serializability and avoiding dirty reads. |
| **Durability** | Once committed, changes survive power outages or system crashes. | `self._conn.commit()` flushes memory pages directly to disk storage inside `careerlens.db`. |

---

## 7. Indexing, B-Trees & Query Optimization

### 7.1 Why Indexing Matters
Without indexes, looking up the score history or filtering scans requires a **Full Table Scan ($O(N)$)**, reading every single disk page sequentially. With millions of scan records, this degrades latency.

### 7.2 CareerLens Indexes
```sql
CREATE INDEX IF NOT EXISTS idx_ats_history_created_at ON ats_history(created_at);
CREATE INDEX IF NOT EXISTS idx_ats_history_score ON ats_history(score);
CREATE INDEX IF NOT EXISTS idx_skill_matches_history_id ON skill_matches(history_id);
CREATE INDEX IF NOT EXISTS idx_resumes_user_id ON resumes(user_id);
CREATE INDEX IF NOT EXISTS idx_job_descriptions_user_id ON job_descriptions(user_id);
```

### 7.3 Index Data Structure (B-Trees)
SQLite uses **B-Tree (Balanced Tree)** data structures for table storage and indexes:
- **Search Time Complexity:** Reduced from $O(N)$ (linear search) to $O(\log N)$ (tree traversal).
- **Foreign Key Indexing:** `idx_skill_matches_history_id` speeds up the `JOIN` between `ats_history` and `skill_matches` when rendering scan breakdowns.
- **Time-Series Ordering:** `idx_ats_history_created_at` accelerates `ORDER BY created_at DESC LIMIT 15` without requiring an in-memory sort operation.

---

## 8. Database Security & SQL Injection Prevention

### 8.1 Prevention of SQL Injection Attacks
> **Vulnerability:** If user input is concatenated into an SQL string (e.g. `f"SELECT * FROM users WHERE email = '{user_input}'"`), an attacker entering `' OR '1'='1` can bypass authentication.

**CareerLens Defense:** We use **Parameterized Queries with Prepared Statements** across all database functions:
```python
# SECURE: Values are passed as a tuple parameter, never concatenated
cursor.execute("SELECT * FROM users WHERE email = ?;", (email_clean,))
cursor.execute("INSERT INTO resumes (user_id, file_name, file_path, raw_text) VALUES (?, ?, ?, ?);",
               (user_id, file_name, file_path, raw_text))
```
The database engine compiles the query structure first, treating user parameters strictly as literal values rather than executable code.

### 8.2 Cryptographic Password Storage (PBKDF2-HMAC-SHA256)
Passwords are never stored in clear text. CareerLens implements salted hashing:
```text
Stored Hash Format: salt$derived_hash
Algorithm: PBKDF2 with SHA-256 and 100,000 iterations
```
- **Salt:** A cryptographically secure 16-byte random hexadecimal token (`secrets.token_hex(16)`). This prevents **Rainbow Table** precomputation attacks.
- **Key Stretching (100,000 rounds):** Slows down brute-force and dictionary attacks.
- **Timing Attack Resistance:** Verification uses `hmac.compare_digest()`, preventing attackers from determining passwords by measuring response latency.

---

## 9. SQL Implementation Breakdown

### 9.1 Data Definition Language (DDL)
```sql
PRAGMA foreign_keys = ON;

-- USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'candidate' CHECK(role IN ('candidate', 'recruiter', 'admin')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- RESUMES TABLE
CREATE TABLE IF NOT EXISTS resumes (
    resume_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    raw_text TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- JOB DESCRIPTIONS TABLE
CREATE TABLE IF NOT EXISTS job_descriptions (
    jd_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    title TEXT NOT NULL,
    company TEXT,
    raw_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- ATS HISTORY TABLE
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

-- SKILL MATCHES TABLE
CREATE TABLE IF NOT EXISTS skill_matches (
    match_id INTEGER PRIMARY KEY AUTOINCREMENT,
    history_id INTEGER NOT NULL,
    keyword TEXT NOT NULL,
    match_type TEXT NOT NULL CHECK(match_type IN ('exact', 'semantic', 'missing')),
    similarity_score REAL DEFAULT 1.0,
    FOREIGN KEY (history_id) REFERENCES ats_history(id) ON DELETE CASCADE
);
```

### 9.2 Advanced Data Query Language (DQL) Examples in CareerLens

#### Query 1: Correlated Subquery with Joins (Used for the Analytics Dashboard)
```sql
SELECT h.id, h.filename, h.score, h.created_at, h.resume_id, h.jd_id,
       jd.title as job_title,
       (SELECT COUNT(*) FROM skill_matches sm WHERE sm.history_id = h.id AND sm.match_type = 'exact') as exact_count,
       (SELECT COUNT(*) FROM skill_matches sm WHERE sm.history_id = h.id AND sm.match_type = 'semantic') as semantic_count,
       (SELECT COUNT(*) FROM skill_matches sm WHERE sm.history_id = h.id AND sm.match_type = 'missing') as missing_count
FROM ats_history h
LEFT JOIN job_descriptions jd ON h.jd_id = jd.jd_id
ORDER BY h.id DESC LIMIT 15;
```
*Concepts demonstrated:* `LEFT OUTER JOIN`, Correlated Subqueries, Aggregate `COUNT()`, Aliasing, and Sorting with Pagination (`LIMIT`).

#### Query 2: Aggregate Diagnostic Summary per Candidate
```sql
SELECT u.full_name, u.email,
       COUNT(h.id) AS total_scans,
       AVG(h.score) AS average_ats_score,
       MAX(h.score) AS highest_score
FROM users u
INNER JOIN resumes r ON u.user_id = r.user_id
INNER JOIN ats_history h ON r.resume_id = h.resume_id
GROUP BY u.user_id
HAVING COUNT(h.id) > 0;
```
*Concepts demonstrated:* Multi-table `INNER JOIN`, Grouping (`GROUP BY`), Aggregate Functions (`COUNT`, `AVG`, `MAX`), and Filter on Aggregates (`HAVING`).

---

## 10. High-Yield DBMS Viva Voce Q&A

### 10.1 Project Specific Questions

#### Q1: What is the main objective of CareerLens from a database standpoint?
**Answer:** From a database perspective, CareerLens models, structures, and persists an end-to-end recruitment screening pipeline. It manages user authentication, stores candidate resume metadata alongside raw OCR text, catalogs target job descriptions, records ATS scoring sessions, and maintains granular keyword-level diagnostics in a 3NF relational database.

#### Q2: Why did you choose SQLite over MySQL or PostgreSQL?
**Answer:** SQLite is an embedded, serverless, zero-configuration, ACID-compliant RDBMS. It stores the complete database inside a single cross-platform file (`careerlens.db`), eliminating the need to run an external database daemon while still providing full SQL support, foreign key constraints, B-Tree indexes, and transaction isolation.

#### Q3: How many tables are present in the CareerLens database?
**Answer:** There are **5 normalized relational tables**:
1. `users` (User accounts and roles)
2. `resumes` (Resume files and OCR extracted text)
3. `job_descriptions` (Target job profiles and requirements)
4. `ats_history` (Scan event junction entity with ATS score)
5. `skill_matches` (Granular keyword-by-keyword matches and deficiencies)

#### Q4: What is the role of `ats_history` in relation to `resumes` and `job_descriptions`?
**Answer:** A resume can be evaluated against multiple job descriptions, and a job description can be evaluated against multiple resumes. `ats_history` acts as the **associative (junction) entity** that resolves this Many-to-Many ($M:N$) relationship into two One-to-Many ($1:N$) relationships, while storing transaction attributes such as the `score` and `created_at` timestamp.

---

### 10.2 Relational Model & Schema Design Questions

#### Q5: What are the different types of relationships in your database?
**Answer:**
- `users` to `resumes`: $1 : N$ (One user can upload multiple resumes).
- `users` to `job_descriptions`: $1 : N$ (One user can save multiple job descriptions).
- `resumes` to `ats_history`: $1 : N$ (One resume can be scanned multiple times).
- `job_descriptions` to `ats_history`: $1 : N$ (One JD can be used across multiple scans).
- `ats_history` to `skill_matches`: $1 : N$ (One scan produces multiple skill breakdown records).
- `resumes` to `job_descriptions`: $M : N$ (Resolved via `ats_history`).

#### Q6: What integrity constraints did you enforce?
**Answer:**
1. **Primary Key:** `INTEGER PRIMARY KEY AUTOINCREMENT` on all tables.
2. **Foreign Key:** Enforced via `PRAGMA foreign_keys = ON;` with referential actions (`ON DELETE CASCADE` and `ON DELETE SET NULL`).
3. **Unique:** `email TEXT UNIQUE` in `users`.
4. **Check Constraints:** `score CHECK(score >= 0 AND score <= 100)`, `role CHECK(role IN (...))`, `match_type CHECK(match_type IN (...))`.
5. **Not Null:** Applied to critical attributes like `password_hash`, `filename`, `raw_text`, and `keyword`.

#### Q7: What is the difference between `ON DELETE CASCADE` and `ON DELETE SET NULL` in your project?
**Answer:**
- `ON DELETE CASCADE`: Used between `ats_history` and `skill_matches`. If a scan record is deleted, all its individual skill matches become meaningless and must be automatically deleted to prevent orphaned records.
- `ON DELETE SET NULL`: Used between `resumes` and `ats_history`. If a candidate removes a resume file from their profile, we do not want to delete their historical score analytics; instead, the foreign key `resume_id` is set to `NULL`, preserving the numerical score for time-series charts.

---

### 10.3 Normalization & Dependency Questions

#### Q8: What is normalization and why did you normalize the CareerLens database?
**Answer:** Normalization is the systematic process of organizing relational tables to minimize data redundancy and eliminate insertion, update, and deletion anomalies without losing information. We normalized CareerLens to **Third Normal Form (3NF) and BCNF**, ensuring that every non-key attribute depends strictly on the primary key, the whole key, and nothing but the key.

#### Q9: Can you explain how the schema satisfies 1NF, 2NF, and 3NF?
**Answer:**
- **1NF:** Every field contains atomic, indivisible values. Repeating keyword lists are decomposed into separate tuples in `skill_matches`.
- **2NF:** The schema is in 1NF and contains no partial functional dependencies because all tables use single-attribute surrogate keys (`id`, `user_id`, etc.).
- **3NF:** The schema is in 2NF and contains no transitive dependencies. User attributes (`full_name`, `role`), resume details, and job descriptions are separated into distinct entities rather than living in the scan record.

#### Q10: Does your schema satisfy BCNF?
**Answer:** Yes. A relation is in BCNF if for every non-trivial functional dependency $X \to Y$, $X$ is a superkey. In all five tables, the only determinants are primary keys (`user_id`, `resume_id`, `jd_id`, `id`, `match_id`), which are candidate keys.

#### Q11: What anomalies would occur if you kept everything in one table?
**Answer:**
- **Insertion Anomaly:** We could not add a new job description without uploading a dummy resume and generating a fake scan.
- **Deletion Anomaly:** Deleting a scan record would delete the user's account and password.
- **Update Anomaly:** If a job title changed, we would have to update it in every past scan record, risking data inconsistency.

---

### 10.4 Transactions, Concurrency & ACID Questions

#### Q12: How do you guarantee the Atomicity of a resume scan in CareerLens?
**Answer:** When an ATS analysis runs, multiple write operations occur: saving to `resumes`, `job_descriptions`, `ats_history`, and inserting dozens of rows into `skill_matches`. In `database.py`, we implement `SQLiteConnectionManager` using the Python context manager protocol (`__enter__` and `__exit__`). If an exception is raised at any point, `__exit__` automatically calls `self._conn.rollback()`, ensuring that either all records are saved or none are.

#### Q13: What does the 'D' in ACID stand for and how is it achieved?
**Answer:** Durability. Once a transaction is successfully completed, `self._conn.commit()` is called, which instructs SQLite to flush all modified memory pages and transaction logs to non-volatile disk storage (`careerlens.db`), ensuring data survives sudden crashes or power loss.

#### Q14: What is a Context Manager in Python and how does it relate to DBMS?
**Answer:** A Context Manager is a Python construct that uses `__enter__` and `__exit__` magic methods to handle resources deterministically using the `with` statement. In our DBMS project, it ensures database connections are always closed, locks are released, and transactions are cleanly committed or rolled back without manual boilerplate.

---

### 10.5 Indexing & Query Execution Questions

#### Q15: What indexes did you create and why?
**Answer:** We created secondary B-Tree indexes:
1. `idx_ats_history_created_at`: Speeds up time-series queries (`ORDER BY created_at DESC`).
2. `idx_ats_history_score`: Accelerates score-based filtering and ranking.
3. `idx_skill_matches_history_id`: Accelerates relational joins between `ats_history` and `skill_matches`.
4. `idx_resumes_user_id` and `idx_job_descriptions_user_id`: Optimize user-specific lookups.

#### Q16: What data structure does SQLite use for indexes and what is its time complexity?
**Answer:** SQLite uses a **B-Tree (Balanced Tree)** data structure. It reduces search, insertion, and deletion complexity from $O(N)$ (linear table scan) to $O(\log N)$ (tree traversal).

#### Q17: What is the downside of having too many indexes?
**Answer:** While indexes accelerate `SELECT` read queries, they add overhead to `INSERT`, `UPDATE`, and `DELETE` operations because the B-Tree must be rebalanced on every write. They also consume extra disk storage. Hence, we only indexed foreign keys and frequently filtered/sorted columns.

---

### 10.6 SQL & Practical Mechanics Questions

#### Q18: How does CareerLens prevent SQL Injection?
**Answer:** We strictly use **Parameterized Queries (Prepared Statements)** with the `?` placeholder in SQLite. Input values are sent separately from the SQL statement, preventing attackers from injecting arbitrary SQL logic.

#### Q19: Why do you store password hashes instead of plain text, and what hashing algorithm is used?
**Answer:** Storing plain text passwords creates a severe security vulnerability. CareerLens uses **PBKDF2-HMAC-SHA256** with 100,000 iterations and a dynamic 16-byte cryptographically random salt per user. This defends against rainbow table precomputation and dictionary attacks.

#### Q20: What is the difference between `DELETE` and `DROP`?
**Answer:**
- `DELETE`: A DML (Data Manipulation Language) command that removes specific rows (e.g. `DELETE FROM ats_history WHERE id = 1`) or all rows while preserving the table schema and structure. Can be rolled back.
- `DROP`: A DDL (Data Definition Language) command that completely removes the table schema, indexes, and all its data from the database catalog (e.g. `DROP TABLE ats_history;`). Cannot be rolled back in standard SQL.

#### Q21: What is a Correlated Subquery and where is it used in CareerLens?
**Answer:** A correlated subquery is a subquery that references columns from the outer query, evaluating once for every row processed by the outer query. In our `get_score_history()` method, we use correlated subqueries to dynamically count exact, semantic, and missing skills for each scan:
```sql
(SELECT COUNT(*) FROM skill_matches sm WHERE sm.history_id = h.id AND sm.match_type = 'exact') as exact_count
```

#### Q22: How can you prove to the examiner that foreign key constraints are working?
**Answer:** By pointing to the line in `database.py`:
```python
self._conn.execute("PRAGMA foreign_keys = ON;")
```
By default, SQLite disables foreign key enforcement for backward compatibility. Executing this PRAGMA on every connection activates foreign key integrity, ensuring cascade deletes and parent existence checks are strictly enforced.

---

## 11. Quick Viva Cheat Sheet (Key Terms Summary)

| DBMS Concept | Project Implementation in CareerLens |
| :--- | :--- |
| **Relational DBMS** | SQLite3 embedded database engine (`careerlens.db`) |
| **Entities** | 5 Tables: `users`, `resumes`, `job_descriptions`, `ats_history`, `skill_matches` |
| **Associative Entity** | `ats_history` (Resolves $M:N$ between `resumes` and `job_descriptions`) |
| **Normalization** | 3NF & BCNF (Zero partial or transitive dependencies) |
| **Transaction Control** | Custom Context Manager `SQLiteConnectionManager` (`commit()` / `rollback()`) |
| **Integrity Rules** | `PRIMARY KEY`, `FOREIGN KEY (CASCADE/SET NULL)`, `CHECK`, `UNIQUE`, `NOT NULL` |
| **Indexing Structure** | B-Trees on Foreign Keys, Timestamps, and Scores ($O(\log N)$ search) |
| **Security & Privacy** | Parameterized queries (SQLi protection) + Salted PBKDF2-HMAC-SHA256 hashing |
| **Query Complexity** | Multi-table `LEFT OUTER JOIN`, Correlated Subqueries, Aggregations (`COUNT`, `AVG`, `MAX`) |
