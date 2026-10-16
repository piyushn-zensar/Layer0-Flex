from datetime import datetime

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, utcnow


class CatalogRefresh(Base):
    """One run of the published-catalog refresh (C-28, P-34): when, from which pages, with what result. A run that
    changed something is a new catalog version (its id)."""
    __tablename__ = "catalog_refresh"
    id: Mapped[int] = mapped_column(primary_key=True)
    started_at: Mapped[datetime] = mapped_column(default=utcnow)
    finished_at: Mapped[datetime | None]
    status: Mapped[str] = mapped_column(String(12), default="running")   # running | ok | partial | failed
    trigger: Mapped[str] = mapped_column(String(40), default="schedule")  # start | schedule | <person>
    sources: Mapped[list] = mapped_column(JSON, default=list)            # [{url, status, sha256, products, error}]
    added: Mapped[int] = mapped_column(default=0)
    changed: Mapped[int] = mapped_column(default=0)
    removed: Mapped[int] = mapped_column(default=0)
    error: Mapped[str] = mapped_column(Text, default="")


class CatalogProduct(Base):
    """A product as published on an official page, identified by its link (stable across renames)."""
    __tablename__ = "catalog_product"
    key: Mapped[str] = mapped_column(String(500), primary_key=True)      # the product's link, else "<page>#<name>"
    bu: Mapped[str | None] = mapped_column(String(20))
    category: Mapped[str] = mapped_column(String(200), default="")
    source_url: Mapped[str] = mapped_column(String(500))                 # the page it was read from
    active: Mapped[bool] = mapped_column(default=True)
    first_seen: Mapped[datetime] = mapped_column(default=utcnow)
    last_seen: Mapped[datetime] = mapped_column(default=utcnow)


class CatalogProductVersion(Base):
    """What the page said about the product during a period: a new name or new features close the old version and
    open a new one, so every earlier name stays traceable."""
    __tablename__ = "catalog_product_version"
    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(ForeignKey("catalog_product.key"), index=True)
    version: Mapped[int] = mapped_column(default=1)
    name: Mapped[str] = mapped_column(String(300))
    features: Mapped[list] = mapped_column(JSON, default=list)
    link: Mapped[str] = mapped_column(String(500), default="")
    refresh_id: Mapped[int] = mapped_column(ForeignKey("catalog_refresh.id"))  # the catalog version that brought it
    valid_from: Mapped[datetime] = mapped_column(default=utcnow)
    valid_to: Mapped[datetime | None]
