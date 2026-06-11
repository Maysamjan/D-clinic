"""Professional print / PDF layouts built as RTL HTML documents.

Important rendering notes (``QTextDocument`` only supports a small HTML/CSS
subset):

  * Image size MUST be set with the ``width``/``height`` *HTML attributes*
    — CSS ``width``/``height`` on ``<img>`` is ignored, which previously
    made large logos fill a whole page. We also pre-scale the logo to a
    small cached copy so printing stays fast and crisp.
  * The base font is forced with ``QTextDocument.setDefaultFont`` (the
    bundled Vazirmatn, registered at startup) rather than ``@font-face``,
    which is unreliable when printing.
  * Text uses dark, high-contrast colors and comfortable sizes so it is
    clearly readable on paper.

Output goes through ``QtPrintSupport`` only (print dialog or PDF export).
"""

from __future__ import annotations

import datetime
import os

from PyQt6.QtCore import QMarginsF, Qt
from PyQt6.QtGui import (
    QFont, QImage, QPageLayout, QPageSize, QTextDocument
)
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from .. import config
from ..models import clinic as clinic_model
from ..models import staff as staff_model
from ..models import (
    attachment as attachment_model,
    expense as expense_model,
    invoice as invoice_model,
    patient as patient_model,
    prescription as prescription_model,
    visit as visit_model,
)
from ..database import db
from . import helpers


# ---------------------------------------------------------------------------
# Shared stylesheet (kept to the QTextDocument-supported CSS subset)
# ---------------------------------------------------------------------------

_CSS = """
<style>
  body { color: #14202E; font-size: 11pt; }
  td, th, p, div { font-size: 11pt; }

  .cname { font-size: 18pt; font-weight: bold; color: #0B2A33; }
  .cmeta { font-size: 8.5pt; color: #3F4A5A; }
  .dtitle { font-size: 15pt; font-weight: bold; color: #0B7D72; }
  .dsub { font-size: 9.5pt; color: #3F4A5A; }
  .dno { font-size: 9.5pt; font-weight: bold; color: #0A6B61; }

  .section { font-size: 13pt; font-weight: bold; color: #ffffff;
             background-color: #0E9F8E; padding: 7pt 10pt; }

  table.info td { font-size: 11pt; padding: 7pt 10pt;
                  border-bottom: 1px solid #D8E0E9; }
  .k { color: #46515F; }
  .v { font-weight: bold; color: #111B27; }

  th.col { background-color: #0E9F8E; color: #ffffff; font-weight: bold;
           padding: 7pt 8pt; font-size: 10.5pt; }
  td.cell { padding: 6pt 8pt; font-size: 10.5pt; color: #16202E;
            border-bottom: 1px solid #D8E0E9; }
  td.alt { background-color: #EEF4F3; }

  .tk { color: #46515F; font-size: 11pt; padding: 5pt 8pt; }
  .tv { font-weight: bold; color: #111B27; font-size: 11pt;
        padding: 5pt 8pt; }
  .grand { font-size: 13pt; font-weight: bold; color: #0A6B61; }

  .amount { background-color: #E3F4F1; color: #0A6B61;
            font-size: 12pt; font-weight: bold; padding: 10pt 12pt; }
  .footer { color: #8A97A6; font-size: 8pt; }
</style>
"""


def _logo_tag() -> str:
    """Return an ``<img>`` tag for the clinic logo, pre-scaled & with proper
    HTML width/height attributes (or a tooth glyph fallback)."""
    c = clinic_model.get()
    logo = c.get("logo_path") or ""
    if logo and os.path.isfile(logo):
        img = QImage(logo)
        if not img.isNull():
            box = 88
            w, h = img.width(), img.height()
            scale = min(box / w, box / h, 1.0)
            tw, th = max(int(w * scale), 1), max(int(h * scale), 1)
            # Pre-scale to a cached copy so we never embed a huge image.
            try:
                config.ensure_dirs()
                cache = os.path.join(config.LOGO_DIR, "_print_logo.png")
                scaled = img.scaled(
                    tw * 2, th * 2, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation)
                scaled.save(cache, "PNG")
                src = cache
            except Exception:  # noqa: BLE001
                src = logo
            url = "file:///" + src.replace("\\", "/").lstrip("/")
            return f"<img src='{url}' width='{tw}' height='{th}'>"
    return ""  # no logo: header omits the logo cell entirely


def _header(doc_title: str, doc_no: str = "", doc_date: str = "") -> str:
    c = clinic_model.get()
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
    no_html = (f" &nbsp;|&nbsp; <span class='dno'>شماره: {helpers.jalali_digits(doc_no)}</span>"
               if doc_no else "")

    logo = _logo_tag()
    logo_cell = (f"<td width='100' valign='middle' align='right'>{logo}</td>"
                 if logo else "")

    return f"""
    <table width='100%' cellspacing='0' cellpadding='0'>
      <tr>
        {logo_cell}
        <td valign='middle' align='right'>
          <div class='cname'>{c.get('name') or 'کلینیک دندانپزشکی'}</div>
          <div class='cmeta'>{meta_html}</div>
        </td>
      </tr>
    </table>
    <hr color='#0E9F8E' size='3'>
    <table width='100%' cellspacing='0' cellpadding='0'>
      <tr><td align='right'>
        <span class='dtitle'>{doc_title}</span>
        &nbsp;&nbsp;&nbsp;
        <span class='dsub'>تاریخ: {doc_date}</span>{no_html}
      </td></tr>
    </table>
    <div style='height:8pt;'></div>
    """


def _section(title: str) -> str:
    return (f"<table width='100%' cellspacing='0' cellpadding='0'>"
            f"<tr><td class='section'>{title}</td></tr></table>"
            f"<div style='height:5pt;'></div>")


def _wrap(body: str) -> str:
    return (f"<html dir='rtl'><head>{_CSS}</head>"
            f"<body>{body}</body></html>")


# QTextDocument always lays table cells out left-to-right regardless of the
# document direction, so for a right-to-left reading order we reverse the
# cell sequence of every row manually (first logical cell ends up on the
# right).

def _info_table(rows: list[list[tuple]]) -> str:
    """Build a label/value information table that reads right-to-left.

    Each row is a list of ``(label, value)`` or ``(label, value, value_span)``
    tuples. Labels appear on the right, values to their left.
    """
    html = "<table class='info' width='100%' cellspacing='0' cellpadding='0'>"
    for row in rows:
        tds = []
        for item in row:
            label, value = item[0], item[1]
            vspan = item[2] if len(item) > 2 else 1
            span = f" colspan='{vspan}'" if vspan > 1 else ""
            tds.append(f"<td class='k' align='right'>{label}</td>")
            tds.append(f"<td class='v' align='right'{span}>{value}</td>")
        tds.reverse()  # render right-to-left
        html += "<tr>" + "".join(tds) + "</tr>"
    return html + "</table>"


def _grid(headers: list[str], rows: list[list[str]], widths=None) -> str:
    """Build a right-to-left data table with header row and zebra striping."""
    cols = list(zip(headers, widths or [None] * len(headers)))
    cols = cols[::-1]  # reverse columns for RTL
    ths = ""
    for h, w in cols:
        wattr = f" width='{w}'" if w else ""
        ths += f"<th class='col' align='right'{wattr}>{h}</th>"
    body = ""
    for r_i, row in enumerate(rows):
        alt = " alt" if r_i % 2 else ""
        cells = list(row)[::-1]  # reverse cells for RTL
        tds = "".join(f"<td class='cell{alt}' align='right'>{c}</td>" for c in cells)
        body += f"<tr>{tds}</tr>"
    if not rows:
        body = (f"<tr><td class='cell' colspan='{len(headers)}' "
                f"align='center'>—</td></tr>")
    return (f"<table width='100%' cellspacing='0' cellpadding='0'>"
            f"<tr>{ths}</tr>{body}</table>")


# ---------------------------------------------------------------------------
# Patient file
# ---------------------------------------------------------------------------

def patient_file_html(patient_id: int) -> str:
    p = patient_model.get(patient_id)
    if not p:
        return ""
    summary = patient_model.financial_summary(patient_id)
    visits = visit_model.for_patient(patient_id, ascending=True)

    info = _section("معلومات مریض") + _info_table([
        [("نام مکمل", p.get("full_name", "")),
         ("کود مریض", helpers.jalali_digits(p.get("code", "")))],
        [("شماره تلفن", helpers.jalali_digits(p.get("phone", ""))),
         ("جنسیت", helpers.gender_label(p.get("gender", "")))],
        [("سن", helpers.jalali_digits(p.get("age")) if p.get("age") else "—"),
         ("تاریخ ثبت", helpers.jalali_date(p.get("registered_at")))],
        [("آدرس", p.get("address") or "—", 3)],
    ]) + "<div style='height:10pt;'></div>"

    rows = []
    for v in visits:
        atts = len(attachment_model.for_visit(v["id"]))
        rows.append([
            helpers.jalali_date(v.get("visit_date")),
            v.get("treatment_name") or "ویزیت",
            helpers.jalali_digits(v.get("tooth")) if v.get("tooth") else "—",
            v.get("doctor_name") or "—",
            v.get("notes") or "—",
            helpers.jalali_digits(atts) if atts else "—",
            helpers.format_money(v.get("cost", 0)),
        ])
    timeline = _section("سوابق معالجات و ویزیت‌ها (جدول زمانی)") + _grid(
        ["تاریخ", "نوع معالجه", "دندان", "داکتر", "یادداشت", "ضمیمه", "هزینه"],
        rows, widths=[90, None, 55, None, None, 55, 95],
    ) + "<div style='height:10pt;'></div>"

    finance = _section("خلاصه مالی") + _info_table([
        [("تعداد ویزیت‌ها", helpers.jalali_digits(summary["visits"])),
         ("مجموع هزینه", helpers.format_money(summary["total_cost"]))],
        [("مجموع پرداختی", helpers.format_money(summary["total_paid"])),
         ("باقیمانده",
          f"<span style='color:#C0344E;'>{helpers.format_money(summary['balance'])}</span>")],
    ])

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
    body += _section("مشخصات ویزیت") + _info_table([
        [("مریض", p.get("full_name", "") if p else ""),
         ("کود مریض", helpers.jalali_digits(p.get("code", "") if p else ""))],
        [("تاریخ", helpers.jalali_date(v.get("visit_date"))),
         ("داکتر", v.get("doctor_name") or "—")],
        [("نوع معالجه", v.get("treatment_name") or "ویزیت"),
         ("دندان", helpers.jalali_digits(v.get("tooth")) if v.get("tooth") else "—")],
        [("یادداشت", v.get("notes") or "—", 3)],
    ]) + f"""
    <div style='height:9pt;'></div>
    <table width='100%' cellspacing='0' cellpadding='0'><tr>
      <td class='amount' align='right'>هزینه این ویزیت: &nbsp; {helpers.format_money(v.get('cost',0))}</td>
    </tr></table>
    """
    if atts:
        rows = [[helpers.jalali_digits(i), a.get("original_name", ""),
                 {"image": "تصویر", "pdf": "PDF", "document": "سند"}.get(
                     a.get("file_type"), a.get("file_type", ""))]
                for i, a in enumerate(atts, 1)]
        body += ("<div style='height:10pt;'></div>" + _section("ضمیمه‌ها")
                 + _grid(["#", "نام فایل", "نوع"], rows, widths=[46, None, 120]))
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
    rows = [[helpers.jalali_digits(i), it["description"],
             helpers.format_money(it["amount"])]
            for i, it in enumerate(items, 1)]
    balance = float(inv["total"]) - float(inv["paid"])

    body = _header("صورتحساب", doc_no=inv.get("number", ""),
                   doc_date=helpers.jalali_date(inv.get("issue_date")))
    body += _section("مشخصات مریض") + _info_table([
        [("نام مریض", p.get("full_name", "") if p else ""),
         ("کود مریض", helpers.jalali_digits(p.get("code", "") if p else ""))],
    ]) + "<div style='height:9pt;'></div>"
    body += _section("خدمات") + _grid(
        ["#", "شرح خدمات", "مبلغ"], rows, widths=[46, None, 150])
    body += f"""
    <div style='height:9pt;'></div>
    <table width='320' cellspacing='0' cellpadding='0' align='right'
           style='background-color:#F4F8F7;'>
      <tr><td class='tk' align='right'>مجموع: &nbsp;&nbsp;<span class='tv'>{helpers.format_money(inv['total'])}</span></td></tr>
      <tr><td class='tk' align='right'>پرداخت شده: &nbsp;&nbsp;<span class='tv'>{helpers.format_money(inv['paid'])}</span></td></tr>
      <tr><td align='right' class='grand' style='padding:6pt 8pt;'>باقیمانده: &nbsp;&nbsp;{helpers.format_money(balance)}</td></tr>
    </table>
    <div style='clear:both;'></div><br><br>
    """
    if inv.get("notes"):
        body += f"<div class='dsub'>یادداشت: {inv['notes']}</div>"
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
    body += _section("مشخصات پرداخت") + _info_table([
        [("دریافت‌کننده", member.get("full_name", "")),
         ("وظیفه", member.get("position") or "—")],
        [("نوع پرداخت", kind), ("دوره", pay.get("period") or "—")],
        [("روش پرداخت", method),
         ("تاریخ", helpers.jalali_date(pay.get("pay_date")))],
        [("یادداشت", pay.get("notes") or "—", 3)],
    ]) + f"""
    <div style='height:9pt;'></div>
    <table width='100%' cellspacing='0' cellpadding='0'><tr>
      <td class='amount' align='right'>مبلغ پرداخت‌شده: &nbsp; {helpers.format_money(pay.get('amount',0))}</td>
    </tr></table>
    <br><br><br>
    <table width='100%' cellspacing='0' cellpadding='0'>
      <tr>
        <td align='center' class='dsub'>...........................<br>امضای دریافت‌کننده</td>
        <td align='center' class='dsub'>...........................<br>امضای پرداخت‌کننده / مدیر</td>
      </tr>
    </table>
    """
    return _wrap(body)


# ---------------------------------------------------------------------------
# Prescription
# ---------------------------------------------------------------------------

def prescription_html(presc_id: int) -> str:
    pres = prescription_model.get(presc_id)
    if not pres:
        return ""
    p = patient_model.get(pres["patient_id"])
    drugs = prescription_model.items(presc_id)
    rows = [[helpers.jalali_digits(i), it["drug"], it.get("dosage") or "—",
             helpers.jalali_digits(it.get("quantity") or "") or "—",
             it.get("instructions") or "—"]
            for i, it in enumerate(drugs, 1)]

    body = _header("نسخه (℞)", doc_date=helpers.jalali_date(pres.get("presc_date")))
    body += _section("مشخصات مریض") + _info_table([
        [("نام مریض", p.get("full_name", "") if p else ""),
         ("کود مریض", helpers.jalali_digits(p.get("code", "") if p else ""))],
        [("سن", helpers.jalali_digits(p.get("age")) if p and p.get("age") else "—"),
         ("داکتر", pres.get("doctor_name") or "—")],
    ])
    if p and (p.get("allergies") or "").strip():
        body += (f"<div style='background:#FEF2F4; color:#B11334; padding:8pt 12pt;"
                 f" margin-top:8pt; font-weight:bold;'>⚠ حساسیت‌ها: "
                 f"{p['allergies']}</div>")
    body += "<div style='height:10pt;'></div>"
    body += _section("℞  داروهای تجویزشده") + _grid(
        ["#", "دوا", "مقدار مصرف", "تعداد تحویلی", "دستور مصرف"],
        rows, widths=[34, None, 78, 90, None])
    if pres.get("notes"):
        body += f"<div class='dsub' style='margin-top:10pt;'>یادداشت: {pres['notes']}</div>"
    body += ("<table width='100%' cellspacing='0' cellpadding='0'>"
             "<tr><td align='left' class='dsub' style='padding-top:40pt;'>"
             "...........................<br>امضای داکتر</td></tr></table>")
    return _wrap(body)


# ---------------------------------------------------------------------------
# Daily cash report
# ---------------------------------------------------------------------------

def daily_report_html(date_iso: str) -> str:
    pay = db.query_one(
        "SELECT COALESCE(SUM(amount),0) AS s, COUNT(*) AS c FROM payments "
        "WHERE pay_date = ?", (date_iso,))
    cash = db.query_one(
        "SELECT COALESCE(SUM(amount),0) AS s FROM payments "
        "WHERE pay_date = ? AND method = 'cash'", (date_iso,))
    card = db.query_one(
        "SELECT COALESCE(SUM(amount),0) AS s FROM payments "
        "WHERE pay_date = ? AND method != 'cash'", (date_iso,))
    visits_row = db.query_one(
        "SELECT COUNT(*) AS c FROM visits WHERE visit_date = ?", (date_iso,))
    expenses = expense_model.total_between(date_iso, date_iso)
    income = float(pay["s"]) if pay else 0.0
    net = income - expenses

    body = _header("راپور روزانه صندوق", doc_date=helpers.jalali_date(date_iso))
    body += _section("خلاصه روز") + _info_table([
        [("تعداد ویزیت‌ها", helpers.jalali_digits(visits_row["c"] if visits_row else 0)),
         ("تعداد پرداخت‌ها", helpers.jalali_digits(pay["c"] if pay else 0))],
        [("دریافت نقدی", helpers.format_money(cash["s"] if cash else 0)),
         ("دریافت کارت/انتقال", helpers.format_money(card["s"] if card else 0))],
        [("مجموع دریافتی‌ها", helpers.format_money(income)),
         ("مجموع مصارف امروز", helpers.format_money(expenses))],
        [("باقی نقد صندوق (تقریبی)",
          f"<b style='color:#0A6B61;'>{helpers.format_money(net)}</b>", 3)],
    ])
    return _wrap(body)


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def _make_document(html: str) -> QTextDocument:
    doc = QTextDocument()
    font = QFont(config.FONT_FAMILY, 11)
    doc.setDefaultFont(font)
    doc.setHtml(html)
    return doc


def print_html(html: str, parent=None, title: str = "چاپ") -> bool:
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    printer.setPageMargins(QMarginsF(14, 14, 14, 14), QPageLayout.Unit.Millimeter)
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
