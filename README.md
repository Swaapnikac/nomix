# nomix-recruiter 🛡️
A NoMix-Shield resume bot that prevents cross-candidate contamination using strict metadata filtering

## Features
- Upload 20+ resumes (and mixed random docs)
- Resume-only Q&A (non-resume docs are ignored for answering)
- Pinecone-based RAG with mandatory `resume_id` filtering (NoMix Shield)
- Prompt enhancement (query rewriting) using a lightweight model
- Scout Mode: multi-candidate search across a shortlist
- Auto “Active Candidate” suggestion if user says he/she without selecting
- One-click “Candidate Brief PDF” export for the shortlist
- Evidence chunk transparency + confidence indicator

