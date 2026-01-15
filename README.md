
# CourseAid – Centralized Course Selection Platform

Course selection can often feel overwhelming. As master’s students, we frequently spend significant time researching and comparing courses to determine which ones will best enhance our learning experience. While platforms like Rate My Professor are commonly used, they are primarily designed for searching individual professors rather than exploring courses holistically. Existing navigation and filtering options are limited, making it difficult to obtain comprehensive and comparative insights.

**CourseAid** aims to solve this problem by creating a centralized hub for course-related information. The application integrates objective course descriptions, student reviews, and perceptions of course difficulty based on the professor teaching the course. With robust filtering and semantic search capabilities, CourseAid empowers students to make more informed academic decisions.

---

## Features

- Centralized course and instructor information
- Student reviews with perceived course difficulty
- Semantic search using vector embeddings
- Advanced filtering and search functionality
- Real-time CRUD operations
- AI-powered assistant for course-related queries

---

## Technical Specifications

This application uses a full-stack architecture backed by a SQL database.

### Architecture Overview

- **Backend:** Flask (Python) for application logic
- **Frontend:** HTML/CSS with Jinja templates
- **Database:** PostgreSQL for both relational and vector storage
- **Vector Search:** pgvector extension in PostgreSQL
- **Embeddings:** Gemma Embedding Model
- **AI Assistant:** Gemini API using the `gemini-2.5-flash` model
- **Hosting:** Amazon RDS

---

## Languages

- **Python** – Backend development
- **SQL** – Database management
- **HTML/CSS** – Frontend development

---

## Technologies & Frameworks

- **Backend:** Flask (Python)
- **Database:** PostgreSQL + pgvector
- **Database Hosting:** AWS RDS
- **Frontend:** HTML/CSS with Jinja Templates
- **Embeddings:** Gemma Embedding Model
- **AI API:** Google Gemini API
- **ML Libraries:** PyTorch, Sentence Transformers, scikit-learn

---

## System Design

### User Activity Diagram
*(See diagram in project documentation)*

### Conceptual Design

The application is designed for a **single university**. Instructors are assumed to be uniquely identifiable by their full name (first name + last name).

### Logical Design

The database consists of **11 tables**, capturing courses, instructors, reviews, users, and vector embeddings.  
*(Refer to the Logical Design Diagram in the documentation for full schema details.)*

---

## Getting Started

### Prerequisites

- **Python 3.13+**
- **pip (latest version)**

### Required API Accounts

You will need API keys/accounts for:
- Hugging Face
- Google Gemini API
- Amazon Web Services (RDS)

---

## Installation

### Step 1: Clone and Open the Repository
Open the repository in your preferred IDE.

### Step 2: Create and Activate a Virtual Environment

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
````

**Windows**

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```
---

## Running the Application

Start the development server with:

```bash
python3 run.py
```

The application will be available at:

```
http://localhost:5000
```

(or another port if configured differently)

---

## Troubleshooting

### Common Issues

#### 1. Hugging Face Token Expired

* Generate a new token at: [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
* Update the `HF_TOKEN` in your `.env` file

#### 2. `ModuleNotFoundError`

* Ensure the virtual environment is activated
* Reinstall dependencies:

```bash
pip install -r requirements.txt
```
