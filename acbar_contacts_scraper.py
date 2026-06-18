# -*- coding: utf-8 -*-
"""
اسکریپت جمع‌آوری خودکار اطلاعات تماس انجوهای عضو ACBAR
=====================================================

این اسکریپت در سه مرحله کار می‌کند:
  مرحله ۱) استخراج فهرست اعضا (مخفف، نوع، نام کامل) از صفحات سایت ACBAR
  مرحله ۲) پیدا کردن وبسایت رسمی هر انجو با جستجوی اینترنتی و استخراج ایمیل/تلفن
  مرحله ۳) ذخیرهٔ نتیجه در فایل اکسل acbar_contacts.xlsx

نصب پیش‌نیازها (یک‌بار اجرا شود):
    pip install requests beautifulsoup4 ddgs openpyxl
"""

import re
import time
import random

import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook

# کتابخانهٔ جستجو (نسخهٔ جدید duckduckgo_search با نام ddgs)
from ddgs import DDGS


# ---------------------------------------------------------------------------
# تنظیمات اصلی (ورودی برنامه)
# ---------------------------------------------------------------------------
BASE_URL = "https://www.acbar.org/en/site-members"   # لینک صفحهٔ اعضا
TOTAL_PAGES = 6          # تعداد صفحات صفحه‌بندی (?page=1 تا ?page=6)
MAX_PAGES_PER_SITE = 4   # حداکثر تعداد صفحه‌ای که از هر وبسایت بررسی می‌شود
OUTPUT_FILE = "acbar_contacts.xlsx"

# هدر مرورگر تا کمتر بلاک شویم
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}

# دامنه‌هایی که داده‌شان نامعتبر است و باید رد شوند
BLACKLIST_DOMAINS = [
    "zoominfo", "rocketreach", "getprospect", "contactout",
    "linkedin", "facebook", "devex", "developmentaid", "wikipedia",
]

# کلمات کلیدی صفحات تماس/درباره (انگلیسی و فارسی/دری)
CONTACT_KEYWORDS = ["contact", "about", "تماس", "درباره", "تماس-با-ما", "about-us"]

# ---------------------------------------------------------------------------
# الگوهای regex
# ---------------------------------------------------------------------------
# الگوی ایمیل
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

# الگوی تلفن افغانستان:
#   با +93 و سپس ۹ رقم   یا   با 0 و سپس ۹ رقم
# بین ارقام ممکن است فاصله/خط تیره باشد، که آن‌ها را بعداً پاک می‌کنیم.
PHONE_REGEX = re.compile(r"(?:\+93|0)(?:[\s\-]?\d){9}")

# پسوندهای تصویری که نباید به‌عنوان ایمیل پذیرفته شوند
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp")


# ---------------------------------------------------------------------------
# توابع کمکی
# ---------------------------------------------------------------------------
def polite_sleep():
    """بین درخواست‌ها ۱ تا ۲ ثانیه مکث می‌کند تا بلاک نشویم."""
    time.sleep(random.uniform(1.0, 2.0))


def fetch(url, timeout=15):
    """یک صفحه را دریافت می‌کند و در صورت خطا None برمی‌گرداند."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        return resp
    except Exception as exc:
        print(f"   [!] خطا در دریافت {url} -> {exc}")
        return None


def is_blacklisted(url):
    """بررسی می‌کند که آیا دامنهٔ آدرس در فهرست سیاه است یا خیر."""
    low = url.lower()
    return any(bad in low for bad in BLACKLIST_DOMAINS)


# ---------------------------------------------------------------------------
# مرحله ۱ — استخراج فهرست اعضا از سایت ACBAR
# ---------------------------------------------------------------------------
def parse_members_from_page(html):
    """
    از HTML یک صفحه، فهرست انجوها را استخراج می‌کند.

    خروجی: لیستی از دیکشنری‌ها با کلیدهای acronym, type, full_name

    توجه: ساختار دقیق HTML سایت ACBAR ممکن است تغییر کند؛ این تابع
    چند حالت رایج (جدول و کارت) را پوشش می‌دهد. اگر سایت تغییر کرد،
    فقط همین تابع را تنظیم کنید.
    """
    soup = BeautifulSoup(html, "html.parser")
    members = []

    # --- حالت ۱: داده‌ها داخل جدول (table) باشند ---
    table = soup.find("table")
    if table:
        for row in table.find_all("tr"):
            cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
            # سطرهای داده معمولاً سه ستون یا بیشتر دارند
            if len(cells) >= 3 and cells[0].lower() not in ("acronym", "مخفف"):
                acronym, ngo_type, full_name = cells[0], cells[1], cells[2]
                if acronym:
                    members.append({
                        "acronym": acronym,
                        "type": ngo_type,
                        "full_name": full_name,
                    })
        if members:
            return members

    # --- حالت ۲: داده‌ها داخل کارت/بلاک‌ها باشند ---
    # دنبال عناصری می‌گردیم که هم نام و هم نوع NNGO/INGO دارند.
    cards = soup.select(".member, .views-row, .card, li")
    for card in cards:
        text = card.get_text(" ", strip=True)
        if not text:
            continue
        type_match = re.search(r"\b(NNGO|INGO)\b", text)
        if not type_match:
            continue
        ngo_type = type_match.group(1)

        # نام کامل: معمولاً در یک عنوان (h2/h3/strong/a) قرار دارد
        title_el = card.find(["h2", "h3", "h4", "strong", "a"])
        full_name = title_el.get_text(strip=True) if title_el else text

        # مخفف: تلاش می‌کنیم متن داخل پرانتز را به‌عنوان مخفف برداریم
        acr_match = re.search(r"\(([A-Z0-9\-]{2,15})\)", text)
        acronym = acr_match.group(1) if acr_match else full_name.split()[0]

        members.append({
            "acronym": acronym,
            "type": ngo_type,
            "full_name": full_name,
        })

    return members


def collect_all_members():
    """همهٔ صفحات صفحه‌بندی را پیمایش کرده و فهرست کامل اعضا را برمی‌گرداند."""
    all_members = []
    print("=== مرحله ۱: استخراج فهرست اعضا از ACBAR ===")
    for page in range(1, TOTAL_PAGES + 1):
        url = f"{BASE_URL}?page={page}"
        print(f"[*] در حال خواندن صفحه {page}: {url}")
        resp = fetch(url)
        if resp:
            page_members = parse_members_from_page(resp.text)
            print(f"    -> {len(page_members)} انجو در این صفحه پیدا شد.")
            all_members.extend(page_members)
        polite_sleep()

    # حذف موارد تکراری بر اساس نام کامل
    seen = set()
    unique = []
    for m in all_members:
        key = m["full_name"].lower()
        if key not in seen:
            seen.add(key)
            unique.append(m)

    print(f"[=] مجموعاً {len(unique)} انجوی یکتا استخراج شد.\n")
    return unique


# ---------------------------------------------------------------------------
# مرحله ۲ — پیدا کردن وبسایت و اطلاعات تماس هر انجو
# ---------------------------------------------------------------------------
def find_official_website(ngo_name):
    """
    با جستجوی اینترنتی، وبسایت رسمی انجو را پیدا می‌کند.
    دامنه‌های فهرست سیاه نادیده گرفته می‌شوند.
    """
    query = f"{ngo_name} Afghanistan NGO official website"
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=8)
            for r in results:
                link = r.get("href") or r.get("url") or ""
                if link and not is_blacklisted(link):
                    return link
    except Exception as exc:
        print(f"   [!] خطا در جستجوی '{ngo_name}': {exc}")
    return ""


def extract_contacts_from_html(html):
    """از HTML یک صفحه، ایمیل‌ها و شماره‌های تلفن معتبر را استخراج می‌کند."""
    # --- ایمیل ---
    emails = set()
    for email in EMAIL_REGEX.findall(html):
        low = email.lower()
        # حذف ایمیل‌هایی که در واقع نام فایل تصویری‌اند
        if low.endswith(IMAGE_EXTENSIONS):
            continue
        emails.add(email)

    # --- تلفن ---
    phones = set()
    for raw in PHONE_REGEX.findall(html):
        # حذف فاصله و خط تیره برای نرمال‌سازی شماره
        clean = re.sub(r"[\s\-]", "", raw)
        phones.add(clean)

    return emails, phones


def get_contact_page_links(html, base_url):
    """لینک صفحات تماس/درباره را از صفحهٔ اصلی پیدا می‌کند."""
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True).lower()
        if any(kw in href.lower() or kw in text for kw in CONTACT_KEYWORDS):
            # تبدیل لینک نسبی به مطلق
            full = requests.compat.urljoin(base_url, href)
            if full not in links:
                links.append(full)
    return links


def scrape_website_contacts(website):
    """
    صفحهٔ اصلی و صفحات تماس/درباره را بررسی کرده و ایمیل و تلفن استخراج می‌کند.
    حداکثر MAX_PAGES_PER_SITE صفحه بررسی می‌شود.
    """
    all_emails, all_phones = set(), set()

    resp = fetch(website)
    if not resp:
        return "", ""

    # ۱) خود صفحهٔ اصلی
    emails, phones = extract_contacts_from_html(resp.text)
    all_emails |= emails
    all_phones |= phones

    # ۲) صفحات تماس/درباره (تا سقف مجاز)
    contact_links = get_contact_page_links(resp.text, website)
    pages_checked = 1
    for link in contact_links:
        if pages_checked >= MAX_PAGES_PER_SITE:
            break
        if is_blacklisted(link):
            continue
        sub = fetch(link)
        pages_checked += 1
        polite_sleep()
        if sub:
            e, p = extract_contacts_from_html(sub.text)
            all_emails |= e
            all_phones |= p

    email_str = ", ".join(sorted(all_emails))
    phone_str = ", ".join(sorted(all_phones))
    return email_str, phone_str


def enrich_member(member):
    """برای یک انجو، وبسایت و اطلاعات تماس را پیدا کرده و به دیکشنری اضافه می‌کند."""
    name = member["full_name"]
    print(f"[*] پردازش: {name}")

    website, email, phone = "", "", ""
    try:
        website = find_official_website(name)
        polite_sleep()
        if website:
            email, phone = scrape_website_contacts(website)
    except Exception as exc:
        # خطای یک سایت نباید کل اسکریپت را متوقف کند
        print(f"   [!] خطا هنگام پردازش {name}: {exc}")

    member["website"] = website
    member["email"] = email
    member["phone"] = phone

    # چاپ پیشرفت کار در ترمینال
    print(f"    وبسایت: {website or '-'}")
    print(f"    ایمیل : {email or '-'}")
    print(f"    تلفن  : {phone or '-'}\n")
    return member


# ---------------------------------------------------------------------------
# مرحله ۳ — ذخیره در فایل اکسل
# ---------------------------------------------------------------------------
def save_to_excel(members, filename):
    """نتیجه را در فایل اکسل با ستون‌های مشخص‌شده ذخیره می‌کند."""
    wb = Workbook()
    ws = wb.active
    ws.title = "ACBAR Contacts"

    # سطر عنوان
    ws.append(["Acronym", "Type", "NGO Full Name", "Website", "Email", "Phone"])

    # سطرهای داده
    for m in members:
        ws.append([
            m.get("acronym", ""),
            m.get("type", ""),
            m.get("full_name", ""),
            m.get("website", ""),
            m.get("email", ""),
            m.get("phone", ""),
        ])

    wb.save(filename)
    print(f"[✓] نتیجه در فایل «{filename}» ذخیره شد. (تعداد ردیف: {len(members)})")


# ---------------------------------------------------------------------------
# اجرای اصلی برنامه
# ---------------------------------------------------------------------------
def main():
    # مرحله ۱
    members = collect_all_members()

    if not members:
        print("[!] هیچ عضوی استخراج نشد. ممکن است ساختار HTML سایت تغییر کرده باشد.")
        print("    تابع parse_members_from_page را بررسی/تنظیم کنید.")
        return

    # مرحله ۲
    print("=== مرحله ۲: جستجوی وبسایت و اطلاعات تماس ===")
    enriched = []
    for idx, member in enumerate(members, start=1):
        print(f"--- ({idx}/{len(members)}) ---")
        enriched.append(enrich_member(member))

    # مرحله ۳
    print("\n=== مرحله ۳: ذخیره‌سازی ===")
    save_to_excel(enriched, OUTPUT_FILE)


if __name__ == "__main__":
    main()
