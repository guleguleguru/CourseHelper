# Research TA Agent

A lightweight, local-first AI assistant that can:

- 📚 Search your textbooks/PDFs and cite exact page numbers —  
  Once you place your own course materials (textbooks, lecture slides, papers) into
  the knowledge base, the agent retrieves the *exact paragraphs* and *page locations*
  that answer your question.  
  Instead of vague or generic responses, it returns explanations that strictly follow
  how your professor presented the concept — no off-topic reasoning, no extra assumptions.  
  Perfect for homework, exam review, and writing course-related papers, where accuracy
  and alignment with your instructor’s materials matter (also very easy to use)


## 1. Features

| Category | Description |
|----------|-------------|
| Retrieval | Hybrid FAISS + BM25 search, citations with file+page |
| Data Analysis | LLM-generated pandas code with sandboxed execution |
| Interfaces | Streamlit (`streamlit run app.py`) and CLI (`python main.py`) |
| Math Output | All formulas rendered with LaTeX |

## 2. Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure API key
cp config/.env.example config/.env
# edit the file and set OPENAI_API_KEY

# Add your PDFs and CSVs
cp your_pdfs/*.pdf knowledge_base/
cp your_data/*.csv data/

# Build index
python build_index.py

# Start web UI
streamlit run app.py
```

## 3. CLI Usage

```bash
python main.py
# Ask questions directly in the terminal
```

## 4. Project Structure

```

├── app.py                # Streamlit UI
├── main.py               # CLI entry
├── build_index.py        # Build FAISS + BM25 indexes
├── check_setup.py        # Environment checker
├── example_usage.py      # Demo script
├── test_tools.py         # Tool tests
├── rebuild_index.*       # One-click index rebuild
├── start_web.*           # One-click web startup
├── requirements.txt
├── LICENSE
├── .gitignore            # Excludes PDFs and sensitive files
├── config/
│   ├── settings.yaml
│   └── .env.example
├── knowledge_base/       # Put your PDFs/TXT/MD here
│   ├── .gitignore        # PDFs excluded from repo
│   ├── README.md         # Example document
│   ├── statistics_basics.md
│   └── research_methods.txt
├── data/                 # Put CSV files here
└── src/
    ├── agent/
    ├── tools/
    ├── ingest/
    └── utils.py
```

## 5. Important Notes

- **PDF files in `knowledge_base/` are excluded** from the repository (see `.gitignore`)
- Only example documents (`.md`, `.txt`) are included in the repo
- Add your own PDFs locally after cloning
- Run `python check_setup.py` after installation
- Rebuild indexes whenever you add/edit PDFs: `python build_index.py`
- Keep your actual `.env` out of version control

Enjoy streamlined research workflows! 🚀
