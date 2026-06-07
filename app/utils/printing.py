"""Professional print/PDF layouts built as RTL HTML documents.

Documents are rendered with ``QTextDocument`` so they can be sent to a
printer (``QPrinter`` + ``QPrintDialog``) or exported to PDF, both using
only the built-in ``QtPrintSupport`` module.
"""

from __future__ import annotations

import os

from PyQt6.QtCore import QMarginsF, QSizeF
from PyQt6.QtGui import QPageLayout, QPageSize, QTextDocument
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtWidgets import QFileDialog

from .. import config
from ..models import clinic as clinic_model
from ..models import (
    attachment as attachment_model,
    invoice as invoice_model,
    patient as patient_model,
    visit as visit_model,
)
from . import helpers


# ---------------------------------------------------------------------------
# HTML building blocks
# ---------------------------------------------------------------------------

_BASE_CSS = """
<style>
  body { font-family: 'Vazirmatn','Tahoma','Segoe UI',sans-serif; color:#1f2a37; }
  .header { border-bottom: 3px solid #2563eb; padding-bottom: 10px; margin-bottom: 16px; }
  .clinic-name { font-size: 22px; font-weight: bold; color: #0f2942; }
  .clinic-meta { font-size: 12px; color: #64748b; }
  h2 { color: #0f2942; font-size: 17px; border-right: 4px solid #2563eb;
       padding-right: 8px; margin-top: 22px; }
  table { width: 100%; border-collapse: collapse; margin-top: 8px; }
  th { background: #f1f5fb; color: #475569; padding: 8px; text-align: right;
       border-bottom: 2px solid #e3e8ef; font-size: 13px; }
  td { padding: 8px; border-bottom: 1px solid #eef2f7; font-size: 13px; }
  .info td { border: none; padding: 4px 8px; }
  .label { color: #64748b; }
  .value { font-weight: bold; }
  .totals { margin-top: 14px; width: 50%; float: left; }
  .totals td { font-size: 14px; }
  .grand { font-size: 16px; font-weight: bold; color: #2563eb; }
  .footer { margin-top: 40px; font-size: 11px; color: #94a3b8;
            text-align: center; border-top: 1px solid #e3e8ef; padding-top: 8px; }
  .badge { background:#e8f0fe; color:#2563eb; padding:2px 8px; border-radius:6px; font-size:12px;}
</style>
"""


def _clinic_header() -> str:
    c = clinic_model.get()
    logo_html = ""
    logo = c.get("logo_path") or ""
    if logo and os.path.isfile(logo):
        logo_html = (
            f"<td style='width:90px;'>"
            f"<img src='{logo}' style='max-width:80px; max-height:80px;'></td>"
        )
    meta = []
    if c.get("owner_name"):
        meta.append("داکتر: " + c["owner_name"])
    if c.get("phone"):
        meta.append("تلفن: " + helpers.jalali_digits(c["phone"]))
    if c.get("address"):
        meta.append(c["address"])
    if c.get("email"):
        meta.append(c["email"])
    meta_html = " &nbsp;|&nbsp; ".join(meta)
    return f"""
    <div class='header'>
      <table style='width:100%; border:none;'>
        <tr style='border:none;'>
          {logo_html}
          <td style='border:none;'>
            <div class='clinic-name'>{c.get('name') or 'کلینیک دندانپزشکی'}</div>
            <div class='clinic-meta'>{meta_html}</div>
          </td>
        </tr>
      </table>
    </div>
    """


def _footer() -> str:
    from ..services import jalali
    import datetime
    today = jalali.long_jalali(datetime.date.today())
    return (
        f"<div class='footer'>چاپ شده در تاریخ {today} — "
        f"سیستم مدیریت کلینیک D-Clinic</div>"
    )


# ---------------------------------------------------------------------------
# Document builders
# ---------------------------------------------------------------------------

def patient_file_html(patient_id: int) -> str:
    p = patient_model.get(patient_id)
    if not p:
        return ""
    summary = patient_model.financial_summary(patient_id)
    visits = visit_model.for_patient(patient_id, ascending=True)

    info = f"""
    <h2>معلومات مریض</h2>
    <table class='info'>
      <tr><td class='label'>کود مریض</td><td class='value'>{helpers.jalali_digits(p.get('code',''))}</td>
          <td class='label'>نام مکمل</td><td class='value'>{p.get('full_name','')}</td></tr>
      <tr><td class='label'>شماره تلفن</td><td class='value'>{helpers.jalali_digits(p.get('phone',''))}</td>
          <td class='label'>جنسیت</td><td class='value'>{helpers.gender_label(p.get('gender',''))}</td></tr>
      <tr><td class='label'>سن</td><td class='value'>{helpers.jalali_digits(str(p.get('age') or '—'))}</td>
          <td class='label'>تاریخ ثبت</td><td class='value'>{helpers.jalali_date(p.get('registered_at'))}</td></tr>
      <tr><td class='label'>آدرس</td><td class='value' colspan='3'>{p.get('address') or '—'}</td></tr>
    </table>
    """

    rows = ""
    for v in visits:
        atts = len(attachment_model.for_visit(v["id"]))
        att_txt = helpers.jalali_digits(str(atts)) if atts else "—"
        rows += f"""
        <tr>
          <td>{helpers.jalali_date(v.get('visit_date'))}</td>
          <td>{v.get('treatment_name') or 'ویزیت'}</td>
          <td>{v.get('tooth') or '—'}</td>
          <td>{v.get('doctor_name') or '—'}</td>
          <td>{v.get('notes') or ''}</td>
          <td>{att_txt}</td>
          <td>{helpers.format_money(v.get('cost',0))}</td>
        </tr>"""
    treatments = f"""
    <h2>سوابق معالجات و ویزیت‌ها</h2>
    <table>
      <tr><th>تاریخ</th><th>نوع معالجه</th><th>دندان</th><th>داکتر</th>
          <th>یادداشت</th><th>ضمیمه</th><th>هزینه</th></tr>
      {rows or "<tr><td colspan='7'>ویزیتی ثبت نشده است</td></tr>"}
    </table>
    """

    finance = f"""
    <h2>خلاصه مالی</h2>
    <table class='info'>
      <tr><td class='label'>تعداد ویزیت‌ها</td>
          <td class='value'>{helpers.jalali_digits(str(summary['visits']))}</td></tr>
      <tr><td class='label'>مجموع هزینه خدمات</td>
          <td class='value'>{helpers.format_money(summary['total_cost'])}</td></tr>
      <tr><td class='label'>مجموع پرداختی</td>
          <td class='value'>{helpers.format_money(summary['total_paid'])}</td></tr>
      <tr><td class='label grand'>باقیمانده</td>
          <td class='value grand'>{helpers.format_money(summary['balance'])}</td></tr>
    </table>
    """

    return (f"<html dir='rtl'><head>{_BASE_CSS}</head><body>"
            f"{_clinic_header()}<h1 style='font-size:18px;color:#0f2942;'>"
            f"پرونده کامل مریض</h1>{info}{treatments}{finance}{_footer()}"
            f"</body></html>")


def visit_html(visit_id: int) -> str:
    v = visit_model.get(visit_id)
    if not v:
        return ""
    p = patient_model.get(v["patient_id"])
    atts = attachment_model.for_visit(visit_id)
    att_rows = ""
    for a in atts:
        att_rows += f"<tr><td>{a.get('original_name','')}</td><td>{a.get('file_type','')}</td></tr>"
    att_html = ""
    if atts:
        att_html = (f"<h2>ضمیمه‌ها</h2><table><tr><th>نام فایل</th><th>نوع</th></tr>"
                    f"{att_rows}</table>")

    return (f"<html dir='rtl'><head>{_BASE_CSS}</head><body>"
            f"{_clinic_header()}"
            f"<h1 style='font-size:18px;color:#0f2942;'>گزارش ویزیت</h1>"
            f"<table class='info'>"
            f"<tr><td class='label'>مریض</td><td class='value'>{p.get('full_name','') if p else ''}</td>"
            f"<td class='label'>کود مریض</td><td class='value'>{helpers.jalali_digits(p.get('code','') if p else '')}</td></tr>"
            f"<tr><td class='label'>تاریخ</td><td class='value'>{helpers.jalali_date(v.get('visit_date'))}</td>"
            f"<td class='label'>داکتر</td><td class='value'>{v.get('doctor_name') or '—'}</td></tr>"
            f"<tr><td class='label'>نوع معالجه</td><td class='value'>{v.get('treatment_name') or 'ویزیت'}</td>"
            f"<td class='label'>دندان</td><td class='value'>{v.get('tooth') or '—'}</td></tr>"
            f"<tr><td class='label'>هزینه</td><td class='value grand'>{helpers.format_money(v.get('cost',0))}</td></tr>"
            f"<tr><td class='label'>یادداشت</td><td class='value' colspan='3'>{v.get('notes') or '—'}</td></tr>"
            f"</table>{att_html}{_footer()}</body></html>")


def invoice_html(invoice_id: int) -> str:
    inv = invoice_model.get(invoice_id)
    if not inv:
        return ""
    p = patient_model.get(inv["patient_id"])
    items = invoice_model.items(invoice_id)
    rows = ""
    for i, it in enumerate(items, 1):
        rows += (f"<tr><td>{helpers.jalali_digits(str(i))}</td>"
                 f"<td>{it['description']}</td>"
                 f"<td>{helpers.format_money(it['amount'])}</td></tr>")
    balance = float(inv["total"]) - float(inv["paid"])
    notes_html = ""
    if inv.get("notes"):
        notes_html = "<p class='clinic-meta'>یادداشت: " + inv["notes"] + "</p>"
    return (f"<html dir='rtl'><head>{_BASE_CSS}</head><body>"
            f"{_clinic_header()}"
            f"<table style='width:100%;border:none;'><tr style='border:none;'>"
            f"<td style='border:none;'><h1 style='font-size:20px;color:#0f2942;margin:0;'>صورتحساب</h1>"
            f"<span class='badge'>{helpers.jalali_digits(inv.get('number',''))}</span></td>"
            f"<td style='border:none;text-align:left;'>"
            f"<div class='clinic-meta'>تاریخ: {helpers.jalali_date(inv.get('issue_date'))}</div></td>"
            f"</tr></table>"
            f"<table class='info' style='margin-top:10px;'>"
            f"<tr><td class='label'>نام مریض</td><td class='value'>{p.get('full_name','') if p else ''}</td>"
            f"<td class='label'>کود مریض</td><td class='value'>{helpers.jalali_digits(p.get('code','') if p else '')}</td></tr>"
            f"</table>"
            f"<table><tr><th style='width:50px;'>#</th><th>شرح خدمات</th><th>مبلغ</th></tr>{rows}</table>"
            f"<table class='totals'>"
            f"<tr><td class='label'>مجموع</td><td class='value'>{helpers.format_money(inv['total'])}</td></tr>"
            f"<tr><td class='label'>پرداخت شده</td><td class='value'>{helpers.format_money(inv['paid'])}</td></tr>"
            f"<tr><td class='label grand'>باقیمانده</td><td class='value grand'>{helpers.format_money(balance)}</td></tr>"
            f"</table>"
            f"<div style='clear:both;'></div>"
            f"{notes_html}"
            f"{_footer()}</body></html>")


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def _make_document(html: str) -> QTextDocument:
    doc = QTextDocument()
    doc.setHtml(html)
    return doc


def print_html(html: str, parent=None, title: str = "چاپ") -> bool:
    """Open a print dialog and print *html*. Returns True if printed."""
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    dialog = QPrintDialog(printer, parent)
    dialog.setWindowTitle(title)
    if dialog.exec() == QPrintDialog.DialogCode.Accepted:
        _make_document(html).print(printer)
        return True
    return False


def export_pdf(html: str, parent=None, suggested_name: str = "document.pdf") -> str | None:
    """Ask for a destination and export *html* to a PDF. Returns the path."""
    path, _ = QFileDialog.getSaveFileName(
        parent, "ذخیره PDF",
        os.path.join(config.BASE_DIR, suggested_name), "PDF (*.pdf)"
    )
    if not path:
        return None
    if not path.lower().endswith(".pdf"):
        path += ".pdf"
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    printer.setPageMargins(QMarginsF(12, 12, 12, 12), QPageLayout.Unit.Millimeter)
    printer.setOutputFileName(path)
    _make_document(html).print(printer)
    return path
