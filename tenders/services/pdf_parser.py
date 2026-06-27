from pypdf import PdfReader


def extract_pdf_text(file_path):
    reader = PdfReader(file_path)
    parts = []

    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ''
        page_text = page_text.strip()
        if page_text:
            parts.append(f'第{page_number}页\n{page_text}')

    if not parts:
        title = (reader.metadata or {}).get('/Title')
        if title:
            parts.append(str(title))

    return '\n\n'.join(parts).strip()
