from fastapi import UploadFile
from typing import Optional


async def normalize_input(input_type: str, content: Optional[str], file: Optional[UploadFile]):

    # TEXT INPUT
    if input_type == "text":
        return content

    # LOG FILE
    if input_type == "log" and file:
        data = await file.read()
        return data.decode("utf-8", errors="ignore")

    # SQL INPUT
    if input_type == "sql":
        return content

    # PDF (basic)
    if input_type == "pdf" and file:
        try:
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(file.file)
            text = ""

            for page in pdf_reader.pages:
                text += page.extract_text() or ""

            return text
        except:
            return "PDF parsing failed"

    # DOCX (basic)
    if input_type == "docx" and file:
        try:
            import docx
            doc = docx.Document(file.file)
            return "\n".join([p.text for p in doc.paragraphs])
        except:
            return "DOCX parsing failed"

    return ""