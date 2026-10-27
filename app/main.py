"""InvoiceHub - simple invoicing for freelancers.

Server-rendered FastAPI app: dashboard, clients, invoices with line items.
"""

from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .database import get_db
from .models import Client, Invoice, InvoiceItem
from .seed import init_db

CURRENCY = "R"
VALID_STATUSES = ("draft", "sent", "paid")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="InvoiceHub", lifespan=lifespan)
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


def invoice_total(invoice: Invoice) -> float:
    return sum(item.quantity * item.unit_price for item in invoice.items)


def money(value: float) -> str:
    return f"{CURRENCY}{value:,.2f}"


def next_invoice_number(db: Session) -> str:
    last_id = db.scalar(select(func.max(Invoice.id)))
    return f"INV-{(last_id or 0) + 1:04d}"


templates.env.globals["invoice_total"] = invoice_total
templates.env.filters["money"] = money


@app.get("/")
def dashboard(request: Request, db: Session = Depends(get_db)):
    invoices = db.scalars(
        select(Invoice).order_by(Invoice.issue_date.desc(), Invoice.id.desc())
    ).all()
    today = date.today()
    stats = {"outstanding": 0.0, "overdue": 0.0, "paid": 0.0, "overdue_count": 0}
    for invoice in invoices:
        total = invoice_total(invoice)
        if invoice.status == "paid":
            stats["paid"] += total
        else:
            stats["outstanding"] += total
            if invoice.due_date and invoice.due_date < today:
                stats["overdue"] += total
                stats["overdue_count"] += 1
    return templates.TemplateResponse(
        request, "dashboard.html", {"invoices": invoices, "stats": stats, "today": today}
    )


@app.get("/clients")
def clients_page(request: Request, db: Session = Depends(get_db)):
    clients = db.scalars(select(Client).order_by(Client.name)).all()
    counts = dict(
        db.execute(
            select(Invoice.client_id, func.count(Invoice.id)).group_by(Invoice.client_id)
        ).all()
    )
    return templates.TemplateResponse(
        request, "clients.html", {"clients": clients, "counts": counts}
    )


@app.post("/clients")
def create_client(
    db: Session = Depends(get_db),
    name: str = Form(...),
    email: str = Form(""),
    company: str = Form(""),
):
    db.add(Client(name=name, email=email or None, company=company or None))
    db.commit()
    return RedirectResponse("/clients", status_code=303)


@app.post("/clients/{client_id}/delete")
def delete_client(client_id: int, db: Session = Depends(get_db)):
    client = db.get(Client, client_id)
    if client:
        db.delete(client)
        db.commit()
    return RedirectResponse("/clients", status_code=303)


@app.get("/invoices")
def invoices_page(
    request: Request, db: Session = Depends(get_db), status: str | None = None
):
    query = select(Invoice).order_by(Invoice.issue_date.desc(), Invoice.id.desc())
    if status in VALID_STATUSES:
        query = query.where(Invoice.status == status)
    invoices = db.scalars(query).all()
    return templates.TemplateResponse(
        request,
        "invoices.html",
        {"invoices": invoices, "status": status, "today": date.today()},
    )


@app.get("/invoices/new")
def new_invoice_form(request: Request, db: Session = Depends(get_db)):
    clients = db.scalars(select(Client).order_by(Client.name)).all()
    if not clients:
        return RedirectResponse("/clients", status_code=303)
    return templates.TemplateResponse(
        request,
        "invoice_form.html",
        {"clients": clients, "next_number": next_invoice_number(db), "today": date.today()},
    )


@app.post("/invoices")
def create_invoice(
    db: Session = Depends(get_db),
    number: str = Form(...),
    client_id: int = Form(...),
    issue_date: str = Form(""),
    due_date: str = Form(""),
    notes: str = Form(""),
    description: list[str] = Form(...),
    quantity: list[float] = Form(...),
    unit_price: list[float] = Form(...),
):
    invoice = Invoice(
        number=number,
        client_id=client_id,
        status="draft",
        issue_date=date.fromisoformat(issue_date) if issue_date else date.today(),
        due_date=date.fromisoformat(due_date) if due_date else None,
        notes=notes or None,
    )
    for desc, qty, price in zip(description, quantity, unit_price):
        if desc.strip():
            invoice.items.append(
                InvoiceItem(description=desc.strip(), quantity=qty or 1, unit_price=price or 0)
            )
    if not invoice.items:
        raise HTTPException(status_code=400, detail="An invoice needs at least one line item")
    db.add(invoice)
    db.commit()
    return RedirectResponse(f"/invoices/{invoice.id}", status_code=303)


@app.get("/invoices/{invoice_id}")
def invoice_detail(request: Request, invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return templates.TemplateResponse(request, "invoice_detail.html", {"invoice": invoice})


@app.post("/invoices/{invoice_id}/status")
def update_invoice_status(
    invoice_id: int, status: str = Form(...), db: Session = Depends(get_db)
):
    if status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    invoice.status = status
    db.commit()
    return RedirectResponse(f"/invoices/{invoice_id}", status_code=303)


@app.post("/invoices/{invoice_id}/delete")
def delete_invoice(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.get(Invoice, invoice_id)
    if invoice:
        db.delete(invoice)
        db.commit()
    return RedirectResponse("/invoices", status_code=303)
