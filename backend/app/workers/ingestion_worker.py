from app.services.ingestion.pipeline import IngestionPipeline


def run_ingestion_job(file_path: str) -> dict:
    pipeline = IngestionPipeline()
    parsed = pipeline.process(__import__("pathlib").Path(file_path))
    return {"text_length": len(parsed.text), "chunks": len(parsed.chunks)}

