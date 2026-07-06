from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path


@dataclass
class ParsedDocument:
    text: str
    metadata: dict = field(default_factory=dict)
    chunks: list[dict] = field(default_factory=list)


class PDFParser:
    def extract_pages(self, path: Path) -> list[dict]:
        try:
            return self._extract_with_pymupdf(path)
        except ImportError:
            pass
        try:
            return self._extract_with_pypdf(path)
        except ImportError:
            return []

    def get_metadata(self, path: Path) -> dict:
        try:
            import fitz
            with fitz.open(path) as doc:
                meta = doc.metadata or {}
                return {
                    "title": meta.get("title"),
                    "author": meta.get("author"),
                    "subject": meta.get("subject"),
                    "keywords": meta.get("keywords"),
                    "page_count": doc.page_count,
                    "creator": meta.get("creator"),
                    "producer": meta.get("producer"),
                }
        except ImportError:
            pass
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            meta = reader.metadata or {}
            return {
                "title": getattr(meta, "title", None),
                "author": getattr(meta, "author", None),
                "subject": getattr(meta, "subject", None),
                "keywords": getattr(meta, "keywords", None),
                "page_count": len(reader.pages),
                "creator": getattr(meta, "creator", None),
                "producer": getattr(meta, "producer", None),
            }
        except ImportError:
            return {"page_count": 0}

    def get_toc(self, path: Path) -> list[dict]:
        try:
            import fitz
            with fitz.open(path) as doc:
                toc = doc.get_toc()
                return [
                    {"level": level, "title": title, "page": page}
                    for level, title, page in toc
                ]
        except ImportError:
            pass
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            try:
                outlines = reader.outline
                return self._flatten_outline_pypdf(outlines)
            except Exception:
                return []
        except ImportError:
            return []
        return []

    def _flatten_outline_pypdf(self, outlines, result=None, level=1) -> list[dict]:
        if result is None:
            result = []
        from pypdf.generic import Destination
        for item in outlines or []:
            if isinstance(item, Destination):
                page_num = None
                try:
                    if hasattr(item, "page") and item.page:
                        page_num = item.page.index + 1
                except Exception:
                    pass
                result.append({
                    "level": level,
                    "title": item.title or "",
                    "page": page_num,
                })
            elif isinstance(item, list):
                self._flatten_outline_pypdf(item, result, level + 1)
        return result

    def extract_tables(self, path: Path) -> list[dict]:
        try:
            import fitz
            tables = []
            with fitz.open(path) as doc:
                for page_idx, page in enumerate(doc, start=1):
                    try:
                        tabs = page.find_tables()
                        for tab_idx, tab in enumerate(tabs.tables):
                            data = tab.extract()
                            if data and len(data) > 0:
                                tables.append({
                                    "page": page_idx,
                                    "table_index": tab_idx,
                                    "rows": len(data),
                                    "cols": len(data[0]) if data else 0,
                                    "data": data,
                                    "markdown": self._table_to_markdown(data),
                                })
                    except Exception:
                        continue
            return tables
        except ImportError:
            pass
        try:
            import pdfplumber
            tables = []
            with pdfplumber.open(str(path)) as pdf:
                for page_idx, page in enumerate(pdf.pages, start=1):
                    try:
                        page_tables = page.extract_tables()
                        for tab_idx, data in enumerate(page_tables):
                            if data and len(data) > 0:
                                tables.append({
                                    "page": page_idx,
                                    "table_index": tab_idx,
                                    "rows": len(data),
                                    "cols": len(data[0]) if data else 0,
                                    "data": data,
                                    "markdown": self._table_to_markdown(data),
                                })
                    except Exception:
                        continue
            return tables
        except ImportError:
            return []
        return []

    def _table_to_markdown(self, data: list[list]) -> str:
        if not data or not data[0]:
            return ""
        cleaned = [[(cell or "").strip() if cell else "" for cell in row] for row in data]
        header = cleaned[0]
        separator = ["---"] * len(header)
        body = cleaned[1:]
        lines = []
        lines.append("| " + " | ".join(header) + " |")
        lines.append("| " + " | ".join(separator) + " |")
        for row in body:
            while len(row) < len(header):
                row.append("")
            lines.append("| " + " | ".join(row[:len(header)]) + " |")
        return "\n".join(lines)

    def _extract_with_pymupdf(self, path: Path) -> list[dict]:
        import fitz
        pages = []
        with fitz.open(path) as doc:
            for page_idx, page in enumerate(doc, start=1):
                text = page.get_text("text")
                pages.append({
                    "page_num": page_idx,
                    "text": text,
                    "metadata": {
                        "width": page.rect.width,
                        "height": page.rect.height,
                    }
                })
        return pages

    def _extract_with_pypdf(self, path: Path) -> list[dict]:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        pages = []
        for page_idx, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            pages.append({
                "page_num": page_idx,
                "text": text,
                "metadata": {}
            })
        return pages


class TextCleaner:
    def clean_pages(self, pages: list[dict]) -> list[dict]:
        cleaned = []
        for page in pages:
            text = self._clean_text(page["text"])
            text = self._remove_page_number_lines(text, page["page_num"])
            text = self._fix_hyphenation(text)
            cleaned.append({
                **page,
                "text": text,
            })
        if len(cleaned) >= 3:
            cleaned = self._remove_headers_footers(cleaned)
        return cleaned

    def _clean_text(self, text: str) -> str:
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'\r', '\n', text)
        lines = text.split('\n')
        lines = [re.sub(r'[ \t]+', ' ', line).rstrip() for line in lines]
        text = '\n'.join(lines)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def _remove_page_number_lines(self, text: str, page_num: int) -> str:
        lines = text.split('\n')
        result = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                result.append(line)
                continue
            if re.fullmatch(r'[-—\s]*\d+\s*[-—\s]*', stripped):
                digits = re.findall(r'\d+', stripped)
                if digits and int(digits[0]) == page_num:
                    continue
            if re.fullmatch(r'第\s*\d+\s*页\s*(/\s*\d+\s*页?)?', stripped):
                continue
            if re.fullmatch(r'Page\s*\d+\s*(of\s*\d+)?', stripped, re.IGNORECASE):
                continue
            result.append(line)
        return '\n'.join(result)

    def _fix_hyphenation(self, text: str) -> str:
        text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)
        text = re.sub(r'(\w+)­\n(\w+)', r'\1\2', text)
        return text

    def _remove_headers_footers(self, pages: list[dict], head_lines: int = 3, tail_lines: int = 3, threshold: float = 0.7) -> list[dict]:
        n = len(pages)
        if n < 3:
            return pages

        head_candidates: dict[str, int] = {}
        tail_candidates: dict[str, int] = {}

        for page in pages:
            lines = [l.strip() for l in page["text"].split('\n') if l.strip()]
            if not lines:
                continue
            for i in range(min(head_lines, len(lines))):
                line = lines[i]
                if len(line) < 100:
                    head_candidates[line] = head_candidates.get(line, 0) + 1
            for i in range(min(tail_lines, len(lines))):
                line = lines[-(i + 1)]
                if len(line) < 100:
                    tail_candidates[line] = tail_candidates.get(line, 0) + 1

        header_lines = {line for line, count in head_candidates.items() if count / n >= threshold}
        footer_lines = {line for line, count in tail_candidates.items() if count / n >= threshold}

        if not header_lines and not footer_lines:
            return pages

        result = []
        for page in pages:
            lines = page["text"].split('\n')
            new_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped in header_lines:
                    continue
                if stripped in footer_lines:
                    continue
                new_lines.append(line)
            text = '\n'.join(new_lines)
            text = re.sub(r'\n{3,}', '\n\n', text).strip()
            result.append({
                **page,
                "text": text,
            })
        return result


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._pieces: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip += 1
        elif tag in {"p", "br", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr"}:
            self._pieces.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if self._skip == 0:
            self._pieces.append(data)

    def get_text(self) -> str:
        text = "".join(self._pieces)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


class DocumentParser:
    SUPPORTED_SUFFIXES = {".txt", ".md", ".markdown", ".html", ".htm", ".pdf"}

    def parse(self, path: Path) -> ParsedDocument:
        suffix = path.suffix.lower()
        if suffix not in self.SUPPORTED_SUFFIXES:
            return ParsedDocument(text="", metadata={"file_type": suffix.lstrip("."), "supported": False})

        if suffix == ".pdf":
            return self._parse_pdf(path)

        raw = path.read_text(encoding="utf-8", errors="ignore")
        text = self._extract_text(raw, suffix)
        metadata = {
            "file_type": suffix.lstrip("."),
            "char_count": len(text),
            "line_count": text.count("\n") + 1 if text else 0,
            "supported": True,
        }
        return ParsedDocument(text=text, metadata=metadata)

    def _extract_text(self, raw: str, suffix: str) -> str:
        if suffix in {".html", ".htm"}:
            extractor = _HTMLTextExtractor()
            try:
                extractor.feed(raw)
                return extractor.get_text()
            except Exception:
                return re.sub(r"<[^>]+>", " ", raw).strip()
        if suffix in {".md", ".markdown"}:
            return self._normalize_markdown(raw)
        return raw.strip()

    def _normalize_markdown(self, text: str) -> str:
        text = re.sub(r"```[\s\S]*?```", lambda m: m.group(0), text)
        text = re.sub(r"#{1,6}\s*", "", text)
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"\*(.+?)\*", r"\1", text)
        text = re.sub(r"`(.+?)`", r"\1", text)
        text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)
        text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"^>+\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _parse_pdf(self, path: Path) -> ParsedDocument:
        from app.core.config import settings

        pdf_parser = PDFParser()
        cleaner = TextCleaner()
        pages = pdf_parser.extract_pages(path)
        if not pages:
            return ParsedDocument(text="", metadata={"file_type": "pdf", "supported": True, "page_count": 0})
        cleaned = cleaner.clean_pages(pages)

        tables = []
        if settings.pdf_enable_table_extract:
            tables = pdf_parser.extract_tables(path)
            for table in tables:
                md = table.get("markdown", "")
                if md.strip():
                    page_num = table.get("page")
                    for page_data in cleaned:
                        if page_data["page_num"] == page_num:
                            page_data["text"] = page_data["text"] + "\n\n" + md
                            break

        full_text = "\n\n".join(p["text"] for p in cleaned)
        total_chars = sum(len(p["text"]) for p in cleaned)

        pdf_meta = pdf_parser.get_metadata(path)
        toc = pdf_parser.get_toc(path) if settings.pdf_enable_toc else []

        return ParsedDocument(
            text=full_text,
            metadata={
                "file_type": "pdf",
                "char_count": total_chars,
                "page_count": len(cleaned),
                "supported": True,
                "title": pdf_meta.get("title"),
                "author": pdf_meta.get("author"),
                "subject": pdf_meta.get("subject"),
                "keywords": pdf_meta.get("keywords"),
                "creator": pdf_meta.get("creator"),
                "producer": pdf_meta.get("producer"),
                "toc": toc,
                "table_count": len(tables),
                "tables": [
                    {"page": t["page"], "rows": t["rows"], "cols": t["cols"]}
                    for t in tables
                ],
            },
            chunks=[],
        )


class Chunker:
    def chunk(self, text: str, *, size: int = 800, overlap: int = 120) -> list[str]:
        if not text:
            return []

        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        if not paragraphs:
            paragraphs = [text]

        chunks: list[str] = []
        current = ""
        for para in paragraphs:
            if len(current) + len(para) + 2 <= size:
                current = (current + "\n\n" + para).strip() if current else para
            else:
                if current:
                    chunks.append(current)
                if len(para) > size:
                    start = 0
                    while start < len(para):
                        end = min(len(para), start + size)
                        chunk = para[start:end].strip()
                        if chunk:
                            chunks.append(chunk)
                        if end >= len(para):
                            break
                        start = max(end - overlap, start + 1)
                    current = ""
                else:
                    current = para

        if current:
            chunks.append(current)

        return chunks


class PageAwareChunker(Chunker):
    def chunk_pages(self, pages: list[dict], *, size: int = 800, overlap: int = 120) -> list[dict]:
        chunks = []
        current_text = ""
        current_page_start: int | None = None
        current_page_end: int | None = None

        for page in pages:
            page_num = page["page_num"]
            page_text = page["text"]

            if not page_text.strip():
                continue

            if current_page_start is None:
                current_page_start = page_num

            if len(current_text) + len(page_text) + 2 <= size:
                current_text = (current_text + "\n\n" + page_text).strip() if current_text else page_text
                current_page_end = page_num
            else:
                if current_text:
                    chunks.append({
                        "chunk_no": len(chunks),
                        "content": current_text,
                        "page_start": current_page_start,
                        "page_end": current_page_end,
                        "char_count": len(current_text),
                    })

                if len(page_text) > size:
                    sub_chunks = self.chunk(page_text, size=size, overlap=overlap)
                    for sub in sub_chunks:
                        chunks.append({
                            "chunk_no": len(chunks),
                            "content": sub,
                            "page_start": page_num,
                            "page_end": page_num,
                            "char_count": len(sub),
                        })
                    current_text = ""
                    current_page_start = None
                    current_page_end = None
                else:
                    current_text = page_text
                    current_page_start = page_num
                    current_page_end = page_num

        if current_text:
            chunks.append({
                "chunk_no": len(chunks),
                "content": current_text,
                "page_start": current_page_start,
                "page_end": current_page_end,
                "char_count": len(current_text),
            })

        return chunks


class IngestionPipeline:
    def __init__(
        self,
        parser: DocumentParser | None = None,
        chunker: Chunker | None = None,
        page_chunker: PageAwareChunker | None = None,
    ) -> None:
        self.parser = parser or DocumentParser()
        self.chunker = chunker or Chunker()
        self.page_chunker = page_chunker or PageAwareChunker()

    def process(self, path: Path, *, chunk_size: int = 800, chunk_overlap: int = 120) -> ParsedDocument:
        from app.core.config import settings

        parsed = self.parser.parse(path)
        if not parsed.chunks and parsed.text:
            if parsed.metadata.get("file_type") == "pdf":
                pdf_parser = PDFParser()
                cleaner = TextCleaner()
                pages = pdf_parser.extract_pages(path)
                cleaned = cleaner.clean_pages(pages)

                if settings.pdf_enable_table_extract:
                    tables = pdf_parser.extract_tables(path)
                    for table in tables:
                        md = table.get("markdown", "")
                        if md.strip():
                            page_num = table.get("page")
                            for page_data in cleaned:
                                if page_data["page_num"] == page_num:
                                    page_data["text"] = page_data["text"] + "\n\n" + md
                                    break

                raw_chunks = self.page_chunker.chunk_pages(cleaned, size=chunk_size, overlap=chunk_overlap)
                parsed.chunks = raw_chunks
                parsed.metadata["chunk_count"] = len(parsed.chunks)
            else:
                raw_chunks = self.chunker.chunk(parsed.text, size=chunk_size, overlap=chunk_overlap)
                parsed.chunks = [
                    {"chunk_no": idx, "content": chunk, "char_count": len(chunk)}
                    for idx, chunk in enumerate(raw_chunks)
                ]
                parsed.metadata["chunk_count"] = len(parsed.chunks)
        return parsed
