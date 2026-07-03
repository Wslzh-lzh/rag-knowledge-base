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
    SUPPORTED_SUFFIXES = {".txt", ".md", ".markdown", ".html", ".htm"}

    def parse(self, path: Path) -> ParsedDocument:
        suffix = path.suffix.lower()
        if suffix not in self.SUPPORTED_SUFFIXES:
            return ParsedDocument(text="", metadata={"file_type": suffix.lstrip("."), "supported": False})

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


class IngestionPipeline:
    def __init__(self, parser: DocumentParser | None = None, chunker: Chunker | None = None) -> None:
        self.parser = parser or DocumentParser()
        self.chunker = chunker or Chunker()

    def process(self, path: Path, *, chunk_size: int = 800, chunk_overlap: int = 120) -> ParsedDocument:
        parsed = self.parser.parse(path)
        if not parsed.chunks and parsed.text:
            raw_chunks = self.chunker.chunk(parsed.text, size=chunk_size, overlap=chunk_overlap)
            parsed.chunks = [
                {"chunk_no": idx, "content": chunk, "char_count": len(chunk)}
                for idx, chunk in enumerate(raw_chunks)
            ]
            parsed.metadata["chunk_count"] = len(parsed.chunks)
        return parsed
