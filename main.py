"""
Entry-point redirect for uvicorn and direct execution.
Allows both:
  uvicorn app.main:app --reload
and
  uvicorn main:app --reload
or
  python main.py
"""

from app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
