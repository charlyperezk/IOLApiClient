import json
from typing import Any, Callable, Dict, List, Optional, Sequence

from sqlalchemy import Column, DateTime, Integer, JSON, String
from sqlalchemy.orm import Session

from .database import Base
from .entities import Attempt, Extraction
from .interfaces import ExtractionRepo


def _normalize_json(obj: Any) -> Any:
    if obj is None:
        return None
    serialized = json.dumps(obj, default=str, ensure_ascii=False)
    return json.loads(serialized)


class InMemoryExtractionRepo(ExtractionRepo):
    saved: List[Extraction]

    def __init__(self) -> None:
        self.saved = []

    def save(self, extraction: Extraction) -> Extraction:
        self.saved.append(extraction)
        return extraction

    def save_many(self, extractions: List[Extraction]) -> List[Extraction]:
        self.saved.extend(extractions)
        return extractions


class ExtractionModel(Base):
    __tablename__ = "extractions"

    id = Column(Integer, primary_key=True)
    identifier = Column(String)
    url = Column(String, nullable=False)
    method = Column(String, nullable=False)
    status = Column(String, nullable=False)
    success = Column(Integer, nullable=False)
    retries = Column(Integer, nullable=False)
    fetched_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False)
    headers = Column(JSON)
    params = Column(JSON)
    json_body = Column(JSON)
    attempts = Column(JSON)
    response = Column(JSON)
    module = Column(String)
    reference_id = Column(String)


class SQLAlchemyExtractionRepo(ExtractionRepo):
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def _serialize_attempts(self, attempts: Sequence[Attempt]) -> List[Dict[str, Any]]:
        serialized = []
        for attempt in attempts:
            content = attempt.response.content
            if isinstance(content, bytes):
                content_value = content.decode("utf-8", errors="replace")
            else:
                content_value = str(content)
            serialized.append(
                {
                    "fetched_at": attempt.fetched_at.isoformat(),
                    "status_code": attempt.response.status_code,
                    "content": content_value,
                }
            )
        return serialized

    def _build_model(self, extraction: Extraction) -> ExtractionModel:
        request = extraction.request
        last_attempt = extraction.attempts[-1]
        response_payload = {
            "status_code": last_attempt.response.status_code,
            "content": last_attempt.response.content,
        }

        return ExtractionModel(
            identifier=getattr(request, "identity", None),
            url=request.url,
            method=request.method.value,
            status=extraction.status.value,
            success=1 if extraction.success else 0,
            retries=extraction.retries,
            fetched_at=last_attempt.fetched_at,
            created_at=request.created_at,
            headers=_normalize_json(request.headers),
            params=_normalize_json(request.params),
            json_body=_normalize_json(request.json),
            attempts=self._serialize_attempts(extraction.attempts),
            response=_normalize_json(response_payload),
            module=request.module,
            reference_id=request.reference_id,
        )

    def save(self, extraction: Extraction) -> Extraction:
        model = self._build_model(extraction)
        with self._session_factory() as session:
            session.add(model)
            session.commit()
        return extraction

    def save_many(self, extractions: List[Extraction]) -> List[Extraction]:
        if not extractions:
            return []

        models = [self._build_model(extraction) for extraction in extractions]
        with self._session_factory() as session:
            session.add_all(models)
            session.commit()
        return extractions
