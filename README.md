# 🛡️ NoMix Recruiter — Intelligent, Safe Resume Chatbot  

**NoMix Recruiter** is an AI-powered, evidence-grounded recruiter assistant that allows you to upload multiple resumes and ask questions in natural language — **without ever mixing candidates or hallucinating information**.  

The system is built using a **metadata-filtered RAG (Retrieval-Augmented Generation) pipeline**, ensuring that every answer is grounded strictly in the correct candidate’s resume.

---

## 🌐 Live Deployment  

👉 **Deployed App:**  

*(Replace this with your actual deployment link if different.)*

---

## 🎯 What NoMix Recruiter Does  

NoMix Recruiter enables recruiters to:  

- Upload multiple resumes (PDF/DOCX/TXT)  
- Automatically detect whether a document is a resume  
- Ask natural language questions about candidates  
- Get **evidence-backed answers only**  
- Search a **single candidate** (Single Mode)  
- Compare multiple candidates (Scout Mode)  
- Avoid hallucinations and cross-candidate mixing  

---

## 🧠 How the System Works (High-Level Architecture)  

### **1) File Upload & Resume Detection**  
- Users upload any document (PDF/DOCX/TXT)  
- The system checks if it “looks like a resume”  
- If **not a resume** → stored in UI but **not processed**  
- If **a resume** → sent for further processing  

---

### **2) Chunking (Document Processing)**  

Each resume is split into smaller pieces (chunks) for efficient retrieval:  

- **Chunk size:** ~900 tokens  
- **Overlap:** ~90 tokens  

Why?  
- Keeps full sections (like experience) together  
- Prevents loss of context at chunk boundaries  
- Makes retrieval more accurate  

---

### **3) Metadata Tagging (NoMix Shield)**  

Every chunk is stored with metadata such as:  

- `resume_id` (unique per candidate)  
- `person_name`  
- `doc_type = "resume"`  
- `section` (education, experience, skills, etc.)  

This ensures:  
> The AI can only retrieve chunks from the correct candidate.  

---

### **4) Vector Storage (Pinecone)**  

Chunks are embedded and stored in **Pinecone**, enabling:  

- Fast semantic search  
- Metadata filtering  
- Scalable retrieval  

---

### **5) Query Rewriting**  

If enabled, user queries are rewritten for clarity.  

Example:  
- “frontend experience” → “HTML, CSS, JavaScript, React experience”  

This improves retrieval quality.  

---

### **6) Retrieval & Answering**  

- The system retrieves only relevant chunks for:  
  - the **active candidate** (Single Mode), or  
  - the **shortlist** (Scout Mode)  
- The LLM answers **strictly from retrieved evidence**  
- If evidence is weak or missing → the model refuses instead of guessing  

---

## 🧰 Tech Stack  

### **Frontend**  
- **Streamlit**  
  - Chat UI  
  - File uploads  
  - Candidate list  
  - Mode switching (Single / Scout)  
  - Session state management  

### **Backend / AI**  
- **Python 3.10+**  
- **OpenAI API**  
  - `text-embedding-3-small` → embeddings  
  - `gpt-4o-mini` → query rewriting + answer generation  

### **Vector Database**  
- **Pinecone**  
  - Stores resume chunks as vectors  
  - Supports metadata filtering  

### **Document Processing**  
- **PyMuPDF (fitz)** → PDF text extraction  
- **python-docx** → DOCX support  
- **tiktoken** → token-based chunking  

### **Core AI Techniques**  
- **RAG (Retrieval-Augmented Generation)**  
- **Metadata-filtered retrieval (NoMix Shield)**  
- **Token-based chunking**  
- **LLM-based resume understanding**  
- **Context-aware chat**  
- **Strict hallucination prevention**  
