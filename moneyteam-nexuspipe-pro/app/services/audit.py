from __future__ import annotations

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, Session, mapped_column

from ..db import Base
from ..models import utcnow


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    actor: Mapped[str] = mapped_column(String(120), default="system")
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=utcnow)


def audit(db: Session, event_type: str, detail: str, actor: str = "system"):
    row = AuditEvent(event_type=event_type, detail=detail[:10000], actor=actor)
    db.add(row)
    db.commit()
    return row
