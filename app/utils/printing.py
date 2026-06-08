"""Professional print / PDF layouts built as RTL HTML documents.

All documents share one clean, well-spaced design:
  * a header with the clinic logo on the right and the clinic name + contact
    details beside it, and the document title/number on the left;
  * clearly titled sections with generous spacing;
  * readable tables;
  * the bundled Vazirmatn font embedded via @font-face so printed output
    looks identical everywhere.

Rendered with ``QTextDocument`` and output through ``QtPrintSupport`` only
(print dialog or PDF export) — no third-party dependencies.
"""

from __future__ import annotations

import datetime
import os

from PyQt6.QtCore import QMarginsF
from PyQt6.QtGui import QPageLayout, QPageSize, QTextDocument
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from .. import config
from ..models import clinic as clinic_model
from ..models import staff as staff_model
from ..models import (
    attachment as attachment_model,
    invoice as invoice_model,
    patient as patient_model,
    visit as visit_model,
)
from . import helpers


# ---------------------------------------------------------------------------
# Shared stylesheet
# ---------------------------------------------------------------------------

def _css() -> str:
    return f"""
<style>
  {helpers.font_face_css()}
  * {{ font-family: 'Vazirmatn','Tahoma','Segoe UI',sans-serif; }}
  body {{ color: #1B2A3D; font-size: 13px; line-height: 1.7; }}

  .doc-header {{ width: 100%; border-collapse: collapse;
                 border-bottom: 3px solid #0E9F8E; padding-bottom: 6px; }}
  .doc-header td {{ vertical-align: middle; padding: 0 6px 10px 6px; border: none; }}
  .logo-cell {{ width: 96px; text-align: right; }}
  .logo-cell img {{ width: 86px; height: 86px; }}
  .logo-fallback {{ font-size: 46px; color: #0E9F8E; }}
  .clinic-name {{ font-size: 23px; font-weight: 700; color: #0C2A33; }}
  .clinic-meta {{ font-size: 11.5px; color: #5B6B80; margin-top: 3px; }}
  .doc-meta {{ text-align: left; }}
  .doc-title {{ font-size: 19px; font-weight: 700; color: #0E9F8E; }}
  .doc-sub {{ font-size: 12px; color: #5B6B80; margin-top: 4px; }}
  .doc-no {{ display:inline-block; background:#E3F6F3; color:#0A6B61;
             font-weight:700; padding:3px 12px; border-radius:8px; margin-top:6px; }}

  h2.section {{ font-size: 15px; color: #0C2A33; font-weight: 700;
                background: #F1F6F5; border-right: 5px solid #0E9F8E;
                padding: 8px 12px; margin: 22px 0 10px 0; border-radius: 6px; }}

  table.info {{ width: 100%; border-collapse: collapse; }}
  table.info td {{ padding: 7px 12px; font-size: 13px;
                   border-bottom: 1px solid #EEF2F7; }}
  table.info td.k {{ color: #5B6B80; width: 130px; }}
  table.info td.v {{ font-weight: 700; color: #1B2A3D; }}

  table.grid {{ width: 100%; border-collapse: collapse; margin-top: 6px; }}
  table.grid th {{ background: #0E9F8E; color: #ffffff; padding: 9px 10px;
                   text-align: right; font-size: 12.5px; font-weight: 700; }}
  table.grid td {{ padding: 9px 10px; font-size: 12.5px;
                   border-bottom: 1px solid #EEF2F7; color: #1B2A3D; }}
  table.grid tr:nth-child(even) td {{ background: #F8FAFC; }}

  .totals {{ width: 320px; border-collapse: collapse; margin-top: 14px; }}
  .totals td {{ padding: 8px 12px; font-size: 13.5px; border-bottom: 1px solid #EEF2F7; }}
  .totals td.k {{ color: #5B6B80; }}
  .totals td.v {{ text-align: left; font-weight: 700; }}
  .totals tr.grand td {{ font-size: 16px; color: #0A6B61;
                         border-top: 2px solid #0E9F8E; border-bottom: none; }}

  .amount-box {{ background:#E3F6F3; border:1px solid #B8E6E0; border-radius:10px;
                 padding: 14px 18px; margin-top: 12px; }}
  .amount-box .big {{ font-size: 24px; font-weight:700; color:#0A6B61; }}
  .amount-box .lbl {{ font-size: 12px; color:#0A6B61; }}

  .note {{ color:#5B6B80; font-size:12px; margin-top:10px; }}
  .sign {{ margin-top: 46px; width:100%; }}
  .sign td {{ padding-top: 30px; font-size: 12px; color:#5B6B80;
              border-top: 1px dashed #C7D3E0; text-align:center; }}
  .footer {{ margin-top: 34px; padding-top: 8px; border-top: 1px solid #E3EAF2;
             text-align: center; font-size: 10.5px; color: #97A6B8; }}
</style>
"""


def _header(doc_title: str, doc_no: str = "", doc_date: str = "") -> str:
    c = clinic_model.get()
    logo = c.get("logo_path") or ""
    if logo and os.path.isfile(logo):
        url = "file:///" + logo.replace("\\", "/").lstrip("/")
        logo_html = f"<img src='{url}'>"
    else:
        logo_html = "<div class='logo-fallback'>🦷</div>"

    meta = []
    if c.get("owner_name"):
        meta.append("داکتر: " + c["owner_name"])
    if c.get("phone"):
        meta.append("تلفن: " + helpers.jalali_digits(c["phone"]))
    if c.get("address"):
        meta.append(c["address"])
    if c.get("email"):
        meta.append(c["email"])
    meta_html = " &nbsp;·&nbsp; ".join(meta)

    if not doc_date:
        doc_date = helpers.jalali_date(datetime.date.today().isoformat())
    no_html = f"<div class='doc-no'>{helpers.jalali_digits(doc_no)}</div>" if doc_no else ""

    return f"""
    <table class='doc-header'>
      <tr>
        <td class='logo-cell'>{logo_html}</td>
        <td>
          <div class='clinic-name'>{c.get('name') or 'کلینیک دندانپزشکی'}</div>
          <div class='clinic-meta'>{meta_html}</div>
        </td>
        <td class='doc-meta'>
          <div class='doc-title'>{doc_title}</div>
          <div class='doc-sub'>تاریخ: {doc_date}</div>
          {no_html}
        </td>
      </tr>
    </table>
    """


def _footer() -> str:
    today = helpers.jalali_date(datetime.date.today().isoformat())
    return (f"<div class='footer'>چاپ شده در {today} — "
            f"سیستم مدیریت کلینیک دندانپزشکی D-Clinic</div>")


def _wrap(body: str) -> str:
    return f"<html dir='rtl'><head>{_css()}</head><body>{body}{_footer()}</body></html>"


# ---------------------------------------------------------------------------
# Patient file
# ---------------------------------------------------------------------------

def patient_file_html(patient_id: int) -> str:
    p = patient_model.get(patient_id)
    if not p:
        return ""
    summary = patient_model.financial_summary(patient_id)
    visits = visit_model.for_patient(patient_id, ascending=True)

    info = f"""
    <h2 class='section'>معلومات مریض</h2>
    <table class='info'>
      <tr><td class='k'>نام مکمل</td><td class='v'>{p.get('full_name','')}</td>
          <td class='k'>کود مریض</td><td class='v'>{helpers.jalali_digits(p.get('code',''))}</td></tr>
      <tr><td class='k'>شماره تلفن</td><td class='v'>{helpers.jalali_digits(p.get('phone',''))}</td>
          <td class='k'>جنسیت</td><td class='v'>{helpers.gender_label(p.get('gender',''))}</td></tr>
      <tr><td class='k'>سن</td><td class='v'>{helpers.jalali_digits(p.get('age')) if p.get('age') else '—'}</td>
          <td class='k'>تاریخ ثبت</td><td class='v'>{helpers.jalali_date(p.get('registered_at'))}</td></tr>
      <tr><td class='k'>آدرس</td><td class='v' colspan='3'>{p.get('address') or '—'}</td></tr>
    </table>
    """

    rows = ""
    for v in visits:
        atts = len(attachment_model.for_visit(v["id"]))
        rows += f"""
        <tr>
          <td>{helpers.jalali_date(v.get('visit_date'))}</td>
          <td>{v.get('treatment_name') or 'ویزیت'}</td>
          <td>{helpers.jalali_digits(v.get('tooth')) if v.get('tooth') else '—'}</td>
          <td>{v.get('doctor_name') or '—'}</td>
          <td>{v.get('notes') or '—'}</td>
          <td>{helpers.jalali_digits(atts) if atts else '—'}</td>
          <td>{helpers.format_money(v.get('cost',0))}</td>
        </tr>"""
    timeline = f"""
    <h2 class='section'>سوابق معالجات و ویزیت‌ها (جدول زمانی)</h2>
    <table class='grid'>
      <tr><th>تاریخ</th><th>نوع معالجه</th><th>دندان</th><th>داکتر</th>
          <th>یادداشت</th><th>ضمیمه</th><th>هزینه</th></tr>
      {rows or "<tr><td colspan='7' style='text-align:center;color:#97A6B8;'>ویزیتی ثبت نشده است</td></tr>"}
    </table>
    """

    finance = f"""
    <h2 class='section'>خلاصه مالی</h2>
    <table class='info'>
      <tr><td class='k'>تعداد ویزیت‌ها</td><td class='v'>{helpers.jalali_digits(summary['visits'])}</td>
          <td class='k'>مجموع هزینه</td><td class='v'>{helpers.format_money(summary['total_cost'])}</td></tr>
      <tr><td class='k'>مجموع پرداختی</td><td class='v'>{helpers.format_money(summary['total_paid'])}</td>
          <td class='k'>باقیمانده</td><td class='v' style='color:#C0344E;'>{helpers.format_money(summary['balance'])}</td></tr>
    </table>
    """

    return _wrap(_header("پرونده کامل مریض") + info + timeline + finance)


# ---------------------------------------------------------------------------
# Single visit
# ---------------------------------------------------------------------------

def visit_html(visit_id: int) -> str:
    v = visit_model.get(visit_id)
    if not v:
        return ""
    p = patient_model.get(v["patient_id"])
    atts = attachment_model.for_visit(visit_id)

    body = _header("گزارش ویزیت", doc_date=helpers.jalali_date(v.get("visit_date")))
    body += f"""
    <h2 class='section'>مشخصات ویزیت</h2>
    <table class='info'>
      <tr><td class='k'>مریض</td><td class='v'>{p.get('full_name','') if p else ''}</td>
          <td class='k'>کود مریض</td><td class='v'>{helpers.jalali_digits(p.get('code','') if p else '')}</td></tr>
      <tr><td class='k'>تاریخ</td><td class='v'>{helpers.jalali_date(v.get('visit_date'))}</td>
          <td class='k'>داکتر</td><td class='v'>{v.get('doctor_name') or '—'}</td></tr>
      <tr><td class='k'>نوع معالجه</td><td class='v'>{v.get('treatment_name') or 'ویزیت'}</td>
          <td class='k'>دندان</td><td class='v'>{helpers.jalali_digits(v.get('tooth')) if v.get('tooth') else '—'}</td></tr>
      <tr><td class='k'>یادداشت</td><td class='v' colspan='3'>{v.get('notes') or '—'}</td></tr>
    </table>
    <div class='amount-box'>
      <span class='lbl'>هزینه این ویزیت:</span>
      <span class='big'>{helpers.format_money(v.get('cost',0))}</span>
    </div>
    """
    if atts:
        rows = "".join(
            f"<tr><td>{helpers.jalali_digits(i)}</td><td>{a.get('original_name','')}</td>"
            f"<td>{ {'image':'تصویر','pdf':'PDF','document':'سند'}.get(a.get('file_type'), a.get('file_type','')) }</td></tr>"
            for i, a in enumerate(atts, 1)
        )
        body += (f"<h2 class='section'>ضمیمه‌ها</h2><table class='grid'>"
                 f"<tr><th>#</th><th>نام فایل</th><th>نوع</th></tr>{rows}</table>")
    return _wrap(body)


# ---------------------------------------------------------------------------
# Invoice
# ---------------------------------------------------------------------------

def invoice_html(invoice_id: int) -> str:
    inv = invoice_model.get(invoice_id)
    if not inv:
        return ""
    p = patient_model.get(inv["patient_id"])
    items = invoice_model.items(invoice_id)
    rows = "".join(
        f"<tr><td>{helpers.jalali_digits(i)}</td><td>{it['description']}</td>"
        f"<td>{helpers.format_money(it['amount'])}</td></tr>"
        for i, it in enumerate(items, 1)
    )
    balance = float(inv["total"]) - float(inv["paid"])

    body = _header("صورتحساب", doc_no=inv.get("number", ""),
                   doc_date=helpers.jalali_date(inv.get("issue_date")))
    body += f"""
    <h2 class='section'>مشخصات مریض</h2>
    <table class='info'>
      <tr><td class='k'>نام مریض</td><td class='v'>{p.get('full_name','') if p else ''}</td>
          <td class='k'>کود مریض</td><td class='v'>{helpers.jalali_digits(p.get('code','') if p else '')}</td></tr>
    </table>
    <h2 class='section'>خدمات</h2>
    <table class='grid'>
      <tr><th style='width:46px;'>#</th><th>شرح خدمات</th><th style='width:160px;'>مبلغ</th></tr>
      {rows or "<tr><td colspan='3'>—</td></tr>"}
    </table>
    <table class='totals' align='left'>
      <tr><td class='k'>مجموع</td><td class='v'>{helpers.format_money(inv['total'])}</td></tr>
      <tr><td class='k'>پرداخت شده</td><td class='v'>{helpers.format_money(inv['paid'])}</td></tr>
      <tr class='grand'><td class='k'>باقیمانده</td><td class='v'>{helpers.format_money(balance)}</td></tr>
    </table>
    <div style='clear:both;'></div>
    """
    if inv.get("notes"):
        body += f"<div class='note'>یادداشت: {inv['notes']}</div>"
    return _wrap(body)


# ---------------------------------------------------------------------------
# Staff payment receipt
# ---------------------------------------------------------------------------

def staff_receipt_html(payment_id: int) -> str:
    pay = staff_model.get_payment(payment_id)
    if not pay:
        return ""
    member = staff_model.get(pay["staff_id"]) or {}
    method = {"cash": "نقدی", "bank": "انتقال بانکی"}.get(
        pay.get("method"), pay.get("method", ""))
    kind = staff_model.PAYMENT_KINDS.get(pay.get("kind"), pay.get("kind", ""))

    body = _header("رسید پرداخت", doc_no=pay.get("receipt_no", ""),
                   doc_date=helpers.jalali_date(pay.get("pay_date")))
    body += f"""
    <h2 class='section'>مشخصات پرداخت</h2>
    <table class='info'>
      <tr><td class='k'>دریافت‌کننده</td><td class='v'>{member.get('full_name','')}</td>
          <td class='k'>وظیفه</td><td class='v'>{member.get('position') or '—'}</td></tr>
      <tr><td class='k'>نوع پرداخت</td><td class='v'>{kind}</td>
          <td class='k'>دوره</td><td class='v'>{pay.get('period') or '—'}</td></tr>
      <tr><td class='k'>روش پرداخت</td><td class='v'>{method}</td>
          <td class='k'>تاریخ</td><td class='v'>{helpers.jalali_date(pay.get('pay_date'))}</td></tr>
      <tr><td class='k'>یادداشت</td><td class='v' colspan='3'>{pay.get('notes') or '—'}</td></tr>
    </table>
    <div class='amount-box'>
      <span class='lbl'>مبلغ پرداخت‌شده:</span>
      <span class='big'>{helpers.format_money(pay.get('amount',0))}</span>
    </div>
    <table class='sign'>
      <tr><td>امضای دریافت‌کننده</td><td>امضای پرداخت‌کننده / مدیر</td></tr>
    </table>
    """
    return _wrap(body)


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def _make_document(html: str) -> QTextDocument:
    doc = QTextDocument()
    doc.setHtml(html)
    return doc


def print_html(html: str, parent=None, title: str = "چاپ") -> bool:
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    dialog = QPrintDialog(printer, parent)
    dialog.setWindowTitle(title)
    if dialog.exec() == QPrintDialog.DialogCode.Accepted:
        _make_document(html).print(printer)
        return True
    return False


def export_pdf(html: str, parent=None, suggested_name: str = "document.pdf") -> str | None:
    path, _ = QFileDialog.getSaveFileName(
        parent, "ذخیره PDF",
        os.path.join(config.BASE_DIR, suggested_name), "PDF (*.pdf)")
    if not path:
        return None
    if not path.lower().endswith(".pdf"):
        path += ".pdf"
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    printer.setPageMargins(QMarginsF(14, 14, 14, 14), QPageLayout.Unit.Millimeter)
    printer.setOutputFileName(path)
    _make_document(html).print(printer)
    return path


def print_or_pdf(parent, html: str, title: str) -> None:
    """Show a Print / PDF / Cancel chooser and act on the result."""
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(f"{title} — چاپ یا ذخیره به صورت PDF؟")
    print_b = box.addButton("🖨 چاپ", QMessageBox.ButtonRole.AcceptRole)
    pdf_b = box.addButton("📄 PDF", QMessageBox.ButtonRole.ActionRole)
    box.addButton("لغو", QMessageBox.ButtonRole.RejectRole)
    box.exec()
    if box.clickedButton() == print_b:
        print_html(html, parent, title)
    elif box.clickedButton() == pdf_b:
        path = export_pdf(html, parent, f"{title}.pdf")
        if path:
            QMessageBox.information(parent, "ذخیره شد", "فایل PDF ذخیره شد:\n" + path)
