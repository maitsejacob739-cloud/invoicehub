"""Schema creation and first-boot demo data."""

from datetime import date, timedelta

from sqlalchemy import func, select

from .database import SessionLocal, engine
from .models import Base, Client, Invoice, InvoiceItem


def init_db() -> None:
    """Create tables and seed demo data once (idempotent)."""
    Base.metadata.create_all(bind=engine)
    seed_if_empty()


def seed_if_empty() -> None:
    with SessionLocal() as db:
        if db.scalar(select(func.count()).select_from(Client)):
            return

        sarah = Client(
            name="Sarah Mitchell",
            email="sarah@brightside.co",
            company="Brightside Design",
        )
        omar = Client(
            name="Omar Farouk",
            email="omar@farouklegal.com",
            company="Farouk Legal",
        )
        db.add_all([sarah, omar])
        db.flush()

        logo = Invoice(
            number="INV-0001",
            client=sarah,
            status="sent",
            issue_date=date.today() - timedelta(days=12),
            due_date=date.today() + timedelta(days=8),
            notes="Net 20 - thank you!",
        )
        logo.items = [
            InvoiceItem(description="Logo design (2 concepts)", quantity=1, unit_price=4500),
            InvoiceItem(description="Brand style guide", quantity=1, unit_price=2000),
        ]
        retainer = Invoice(
            number="INV-0002",
            client=omar,
            status="paid",
            issue_date=date.today() - timedelta(days=35),
            due_date=date.today() - timedelta(days=5),
        )
        retainer.items = [
            InvoiceItem(description="Website consulting retainer", quantity=6, unit_price=950),
        ]
        db.add_all([logo, retainer])
        db.commit()
