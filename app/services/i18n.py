"""Bilingual (Persian/Dari ↔ English) translation layer.

Strings are translated by their Persian source text: ``t("ذخیره")`` returns
the Persian text in Persian mode and the English equivalent in English mode
(falling back to the Persian text when no translation exists, so nothing
ever breaks). Digits and dates also follow the active language.
"""

from __future__ import annotations

_LANG = "fa"

_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def set_language(lang: str) -> None:
    global _LANG
    _LANG = "en" if str(lang).lower().startswith("en") else "fa"


def get_language() -> str:
    return _LANG


def is_rtl() -> bool:
    return _LANG == "fa"


def digits(text) -> str:
    """Persian digits in Persian mode, ASCII digits in English mode."""
    s = str(text if text is not None else "")
    return s.translate(_FA_DIGITS) if _LANG == "fa" else s


def t(fa: str) -> str:
    """Translate a Persian source string for the active language."""
    if _LANG == "fa":
        return fa
    return _EN.get(fa, fa)


# ---------------------------------------------------------------------------
# Persian source  ->  English translation
# ---------------------------------------------------------------------------
_EN: dict[str, str] = {
    # App / branding
    "سیستم مدیریت کلینیک دندانپزشکی": "Dental Clinic Management System",
    "مدیریت کلینیک دندانپزشکی": "Dental Clinic Management",
    "نرم‌افزار مدیریت کلینیک دندانپزشکی — افغانستان":
        "Dental Clinic Management Software — Afghanistan",

    # Login
    "ورود به سیستم": "Sign In",
    "لطفاً نام کاربری و رمز عبور خود را وارد کنید":
        "Please enter your username and password",
    "نام کاربری": "Username",
    "رمز عبور": "Password",
    "ورود": "Login",
    "ورود پیش‌فرض مدیر:  admin / admin": "Default admin login:  admin / admin",
    "خطا": "Error",
    "نام کاربری و رمز عبور را وارد کنید": "Enter username and password.",
    "خطای ورود": "Login error",
    "نام کاربری یا رمز عبور اشتباه است.": "Incorrect username or password.",

    # Activation
    "فعال‌سازی": "Activate",
    "فعال‌سازی نرم‌افزار": "Software Activation",
    "این نسخه برای همین کمپیوتر قفل می‌شود. لطفاً «شناسه دستگاه» زیر را برای فروشنده بفرستید و «کلید محصول» دریافتی را وارد کنید.":
        "This copy is locked to this computer. Please send the Machine ID below to the vendor and enter the Product Key you receive.",
    "شناسه دستگاه شما:": "Your Machine ID:",
    "کپی شناسه دستگاه": "Copy Machine ID",
    "کلید محصول:": "Product Key:",
    "کلید محصول را اینجا وارد یا الصاق کنید ...": "Enter or paste the product key here ...",
    "بارگذاری فایل کلید (.lic)": "Load key file (.lic)",
    "کپی شد": "Copied",
    "شناسه دستگاه کپی شد.": "Machine ID copied.",
    "لطفاً کلید محصول را وارد کنید.": "Please enter the product key.",
    "فعال شد": "Activated",
    "نرم‌افزار با موفقیت فعال شد.": "The software has been activated successfully.",
    "کلید نامعتبر": "Invalid key",
    "کلید محصول برای این کمپیوتر معتبر نیست.\nلطفاً شناسه دستگاه را دوباره برای فروشنده بفرستید.":
        "The product key is not valid for this computer.\nPlease send the Machine ID to the vendor again.",

    # Navigation
    "داشبورد": "Dashboard",
    "نوبت‌دهی": "Appointments",
    "مریض‌ها": "Patients",
    "داکتران و کارمندان": "Doctors & Staff",
    "معاشات": "Salaries",
    "گدام و انبار": "Inventory",
    "مصارف و حسابداری": "Expenses & Accounting",
    "گزارش‌ها": "Reports",
    "خدمات و قیمت‌ها": "Services & Prices",
    "کاربران": "Users",
    "تنظیمات": "Settings",
    "خروج از حساب": "Log out",
    "خروج": "Log out",
    "از حساب کاربری خارج می‌شوید؟": "Log out of your account?",

    # Page titles
    "مدیریت مریض‌ها": "Patient Management",
    "معاشات کارمندان": "Staff Salaries",
    "مدیریت کاربران": "User Management",
    "پرونده مریض": "Patient File",

    # Roles
    "مدیر": "Admin",
    "داکتر": "Doctor",
    "پذیرش": "Receptionist",

    # Common buttons / words
    "ذخیره": "Save",
    "لغو": "Cancel",
    "حذف": "Delete",
    "ویرایش": "Edit",
    "چاپ": "Print",
    "بستن": "Close",
    "افزودن": "Add",
    "بازگشت": "Back",
    "→ بازگشت": "← Back",
    "امروز": "Today",
    "بله": "Yes",
    "نخیر": "No",
    "موفق": "Success",
    "ذخیره شد": "Saved",
    "باز کردن": "Open",
    "باز کردن پرونده": "Open file",
    "پرونده": "File",
    "عملیات": "Actions",
    "وضعیت": "Status",
    "فعال": "Active",
    "غیرفعال": "Inactive",
    "نوع": "Type",
    "تاریخ": "Date",
    "مبلغ": "Amount",
    "یادداشت": "Note",
    "یادداشت: ": "Note: ",
    "یادداشت (اختیاری)": "Note (optional)",
    "روش": "Method",
    "نقدی": "Cash",
    "کارت / انتقال": "Card / Transfer",
    "انتقال بانکی": "Bank transfer",
    "بانکی": "Bank",

    # Dashboard
    "مریض‌های امروز": "Today's patients",
    "نوبت‌های امروز": "Today's appointments",
    "مجموع مریض‌ها": "Total patients",
    "درآمد امروز": "Today's revenue",
    "درآمد این ماه": "This month's revenue",
    "مطالبات معوقه": "Outstanding balances",
    "ثبت‌نام امروز": "Registered today",
    "درآمد ماهانه": "Monthly revenue",
    "رشد مریض‌ها": "Patient growth",
    "رایج‌ترین معالجات": "Most common treatments",
    "داده‌ای موجود نیست": "No data",

    # Patients
    "🔍  جستجو با نام، شماره تلفن یا کود مریض ...":
        "🔍  Search by name, phone or patient code ...",
    "➕ مریض جدید": "➕ New patient",
    "مریض یافت شد": "patients found",
    "کود": "Code",
    "نام مکمل": "Full name",
    "نام مکمل *": "Full name *",
    "تلفن": "Phone",
    "شماره تلفن": "Phone number",
    "جنسیت": "Gender",
    "مرد": "Male",
    "زن": "Female",
    "سن": "Age",
    "آدرس": "Address",
    "تاریخ ثبت": "Registered on",
    "ثبت مریض جدید": "Register new patient",
    "ویرایش مریض": "Edit patient",
    "اطلاعات مریض جدید را وارد کنید": "Enter the new patient's information",
    "نام مریض الزامی است.": "Patient name is required.",
    "گروه خون": "Blood type",
    "⚠ حساسیت‌ها": "⚠ Allergies",
    "حساسیت‌ها": "Allergies",
    "سوابق طبی": "Medical history",
    "مثلاً حساسیت به پنسلین (در صورت وجود)": "e.g. allergic to penicillin (if any)",
    "بیماری‌های زمینه‌ای: فشار خون، دیابت، قلبی ...":
        "Chronic conditions: hypertension, diabetes, cardiac ...",

    # Patient file
    "✎ ویرایش": "✎ Edit",
    "🖨 چاپ پرونده": "🖨 Print file",
    "تعداد ویزیت": "Visits",
    "مجموع هزینه": "Total cost",
    "پرداخت شده": "Paid",
    "باقیمانده": "Balance",
    "آخرین مراجعه": "Last visit",
    "معلومات شخصی": "Personal info",
    "📋 جدول زمانی مراجعات": "📋 Visit timeline",
    "➕ ویزیت جدید": "➕ New visit",
    "نمای کلی و جدول زمانی": "Overview & timeline",
    "🦷 چارت دندان": "🦷 Dental chart",
    "ویزیت‌ها / معالجات": "Visits / treatments",
    "℞ نسخه‌ها": "℞ Prescriptions",
    "پرداخت‌ها": "Payments",
    "صورتحساب‌ها": "Invoices",
    "فایل‌ها و تصاویر": "Files & images",
    "➕ ثبت ویزیت": "➕ Add visit",
    "معالجه": "Treatment",
    "دندان": "Tooth",
    "هزینه": "Cost",
    "➕ ثبت پرداخت": "➕ Add payment",
    "➕ صدور صورتحساب": "➕ Issue invoice",
    "شماره": "Number",
    "مجموع": "Total",
    "℞ نسخه‌ی جدید": "℞ New prescription",
    "تعداد دوا": "Drugs",
    "چاپ صورتحساب": "Print invoice",
    "چاپ نسخه": "Print prescription",
    "چاپ ویزیت": "Print visit",
    "هنوز هیچ ویزیتی برای این مریض ثبت نشده است.":
        "No visits recorded for this patient yet.",

    # Visit dialog
    "ثبت ویزیت / معالجه": "Add visit / treatment",
    "ویرایش ویزیت": "Edit visit",
    "جزئیات معالجه و هزینه را وارد کنید": "Enter the treatment details and cost",
    "تاریخ ویزیت *": "Visit date *",
    "نوع معالجه": "Treatment type",
    "— انتخاب کنید —": "— Select —",
    "شماره دندان": "Tooth number",
    "ضمیمه‌ها (اختیاری)": "Attachments (optional)",
    "➕ افزودن فایل": "➕ Add file",
    "حذف فایل انتخاب‌شده": "Remove selected file",
    "تاریخ ویزیت نامعتبر است.": "Invalid visit date.",

    # Payment dialog
    "ثبت پرداخت": "Add payment",
    "ثبت پرداخت مریض": "Record patient payment",
    "باقیمانده فعلی: ": "Current balance: ",
    "مبلغ پرداخت *": "Payment amount *",
    "روش پرداخت": "Payment method",
    "مبلغ پرداخت باید بیشتر از صفر باشد.": "Payment amount must be greater than zero.",

    # Appointments
    "‹ روز قبل": "‹ Prev day",
    "روز بعد ›": "Next day ›",
    "➕ نوبت جدید": "➕ New appointment",
    "نوبت در این روز": "appointments on this day",
    "ساعت": "Time",
    "مریض": "Patient",
    "علت مراجعه": "Reason",
    "ثبت نوبت جدید": "New appointment",
    "ویرایش نوبت": "Edit appointment",
    "تعیین وقت ملاقات مریض": "Schedule a patient appointment",
    "— مریض جدید / مراجعه‌کننده —": "— New / walk-in patient —",
    "نام (در صورت جدید)": "Name (if new)",
    "تاریخ *": "Date *",
    "تاریخ نامعتبر است.": "Invalid date.",
    "نام مریض را وارد کنید.": "Enter the patient name.",
    "انجام": "Done",
    "انجام شد": "Done",
    "این نوبت حذف شود؟": "Delete this appointment?",
    "در انتظار": "Scheduled",
    "انجام‌شده": "Done",
    "لغو‌شده": "Cancelled",
    "حاضر نشد": "No-show",

    # Staff
    "ثبت داکتران و کارمندان کلینیک و مدیریت معاش و فیصدی آن‌ها":
        "Register clinic doctors and staff and manage their salary and commission",
    "➕ کارمند / داکتر جدید": "➕ New staff / doctor",
    "نوع پرداخت": "Pay type",
    "فیصدی کسب‌شده": "Commission earned",
    "پرداخت‌شده": "Paid",
    "حساب": "Account",
    "ثبت کارمند / داکتر جدید": "Register new staff / doctor",
    "ویرایش کارمند": "Edit staff",
    "یک کارمند یا داکتر جدید ثبت کنید": "Register a new staff member or doctor",
    "آیدی / کود *": "ID / Code *",
    "مثلاً ۱ یا د-۲ (دلخواه)": "e.g. 1 or D-2 (custom)",
    "وظیفه": "Position",
    "معاش ماهانه": "Monthly salary",
    "فیصدی از معالجات": "Commission on treatments",
    "این شخص معالجه انجام می‌دهد (در لیست داکتر ویزیت بیاید)":
        "This person performs treatments (appears in the visit doctor list)",
    "آیدی / کود الزامی است.": "ID / Code is required.",
    "نام مکمل الزامی است.": "Full name is required.",
    "این آیدی قبلاً ثبت شده است.": "This ID is already in use.",
    "معاش ثابت": "Fixed salary",
    "فیصدی": "Commission",
    "معاش + فیصدی": "Salary + commission",
    "معاش": "Salary",
    "پاداش": "Bonus",
    "ثبت پرداخت به کارمند": "Record staff payment",
    "فیصدی، معاش یا پاداش": "Commission, salary or bonus",
    "ثبت و رسید": "Save & receipt",
    "حساب و پرداخت‌های کارمند": "Staff account & payments",
    "➕ ثبت پرداخت": "➕ Add payment",
    "مجموع معالجات": "Total treatments",
    "فیصدی کسب‌شده": "Commission earned",
    "مجموع پرداخت‌شده": "Total paid",
    "باقیمانده فیصدی": "Commission balance",
    "رسید": "Receipt",
    "چاپ رسید": "Print receipt",
    "دوره": "Period",
    "مبلغ باید بیشتر از صفر باشد.": "Amount must be greater than zero.",

    # Salaries
    "دوره معاش:": "Salary period:",
    "🔍  جستجوی کارمند با نام، کود یا وظیفه ...":
        "🔍  Search staff by name, code or position ...",
    "معاش ماهانه": "Monthly salary",
    "پرداخت‌شده (دوره)": "Paid (period)",
    "پرداخت معاش": "Pay salary",
    "پرداخت": "Pay",
    "بدون معاش ثابت": "No fixed salary",
    "پرداخت‌نشده": "Unpaid",
    "ناقص": "Partial",
    "مبلغ معاش *": "Salary amount *",
    "مبلغ معاش باید بیشتر از صفر باشد.": "Salary amount must be greater than zero.",
    "رسید پرداخت معاش چاپ شود؟": "Print the salary receipt?",
    "رسید معاش": "Salary receipt",

    # Inventory
    "ثبت داکتران و کارمندان کلینیک": "Register clinic doctors and staff",
    "🔍  جستجوی نام دوا، تجهیزات یا تهیه‌کننده ...":
        "🔍  Search drug, equipment or supplier ...",
    "همه دسته‌ها": "All categories",
    "➕ قلم جدید": "➕ New item",
    "قلم": "items",
    "ارزش کل گدام: ": "Total store value: ",
    "نام": "Name",
    "دسته": "Category",
    "موجودی": "Stock",
    "حداقل": "Min",
    "قیمت فی واحد": "Unit price",
    "ارزش کل": "Total value",
    "تاریخ انقضا": "Expiry date",
    "دوا": "Medicine",
    "تجهیزات": "Equipment",
    "مواد مصرفی": "Consumables",
    "ورود": "Stock in",
    "خروج": "Stock out",
    "ثبت قلم جدید (دوا / تجهیزات)": "New item (medicine / equipment)",
    "ثبت قلم جدید": "New item",
    "ویرایش قلم": "Edit item",
    "دوا، تجهیزات یا مواد مصرفی گدام": "Store medicine, equipment or consumables",
    "نام قلم *": "Item name *",
    "واحد": "Unit",
    "موجودی اولیه": "Initial stock",
    "حداقل موجودی (هشدار)": "Minimum stock (alert)",
    "تهیه‌کننده": "Supplier",
    "این قلم تاریخ انقضا دارد": "This item has an expiry date",
    "نام قلم الزامی است.": "Item name is required.",
    "ورود به گدام": "Stock in",
    "خروج از گدام": "Stock out",
    "مقدار *": "Quantity *",
    "علت": "Reason",
    "ثبت": "Save",
    "خرید / ورود": "Purchase / in",
    "مصرف / خروج": "Use / out",
    "تصحیح موجودی": "Adjustment",
    "ضایعات / انقضا": "Waste / expiry",

    # Expenses
    "ثبت مصرف": "Add expense",
    "🖨 راپور روزانه صندوق": "🖨 Daily cash report",
    "➕ ثبت مصرف": "➕ Add expense",
    "درآمد (دریافتی‌ها)": "Income (receipts)",
    "مصارف": "Expenses",
    "پرداخت به کارمندان": "Paid to staff",
    "سود خالص": "Net profit",
    "شرح": "Description",
    "پرداخت به": "Paid to",
    "ثبت مصرف جدید": "New expense",
    "ویرایش مصرف": "Edit expense",
    "مصارف و هزینه‌های کلینیک": "Clinic expenses and costs",
    "شرح *": "Description *",
    "شرح مصرف الزامی است.": "Expense description is required.",
    "کرایه": "Rent",
    "برق / آب / انترنت": "Utilities / internet",
    "خرید مواد و تجهیزات": "Supplies & equipment",
    "معاش و تنخواه": "Salaries & wages",
    "ترمیم و نگهداری": "Maintenance",
    "تبلیغات": "Marketing",
    "متفرقه": "Other",
    "راپور روزانه": "Daily report",

    # Reports
    "گزارش‌ها و تحلیل‌ها": "Reports & analytics",
    "بازه:": "Range:",
    "۶ ماه اخیر": "Last 6 months",
    "۱۲ ماه اخیر": "Last 12 months",
    "رشد مریض‌ها (ثبت‌نام ماهانه)": "Patient growth (monthly registrations)",

    # Services
    "لیست قیمت خدمات": "Service price list",
    "انواع معالجه": "Treatment types",
    "➕ خدمت جدید": "➕ New service",
    "➕ نوع معالجه جدید": "➕ New treatment type",
    "نام خدمت": "Service name",
    "قیمت": "Price",
    "قیمت پیش‌فرض": "Default price",
    "خدمت جدید": "New service",
    "ویرایش خدمت": "Edit service",
    "نوع معالجه جدید": "New treatment type",
    "ویرایش معالجه": "Edit treatment",
    "نام *": "Name *",

    # Users
    "➕ کاربر جدید": "➕ New user",
    "کاربر جدید": "New user",
    "ویرایش کاربر": "Edit user",
    "نقش": "Role",
    "رمز عبور (خالی = بدون تغییر)": "Password (blank = no change)",
    "رمز عبور *": "Password *",
    "نام کاربری الزامی است.": "Username is required.",
    "رمز عبور الزامی است.": "Password is required.",
    "این نام کاربری قبلاً ثبت شده است.": "This username already exists.",

    # Settings
    "تنظیمات کلینیک": "Clinic Settings",
    "زبان برنامه": "Application language",
    "زبان": "Language",
    "فارسی / دری": "Persian / Dari",
    "انگلیسی": "English",
    "انتخاب لوگو": "Choose logo",
    "حذف لوگو": "Remove logo",
    "بدون لوگو": "No logo",
    "نام کلینیک *": "Clinic name *",
    "نام داکتر / مالک": "Doctor / owner name",
    "ایمیل (اختیاری)": "Email (optional)",
    "ذخیره تنظیمات": "Save settings",
    "نام کلینیک الزامی است.": "Clinic name is required.",
    "تنظیمات کلینیک ذخیره شد.": "Clinic settings saved.",
    "پشتیبان‌گیری و بازیابی": "Backup & restore",
    "نسخه پشتیبان به‌صورت خودکار هر روز گرفته می‌شود. می‌توانید به‌صورت دستی نیز پشتیبان بگیرید یا اطلاعات را بازیابی کنید.":
        "A backup is taken automatically every day. You can also back up manually or restore data.",
    "💾 پشتیبان‌گیری اکنون": "💾 Back up now",
    "📤 ذخیره در محل دلخواه": "📤 Save to a location",
    "♻ بازیابی از فایل": "♻ Restore from file",
    "تاریخچه پشتیبان‌ها:": "Backup history:",
    "حجم": "Size",
    "خودکار": "Automatic",
    "دستی": "Manual",
    "موجود": "Available",
    "حذف شده": "Deleted",
    "تغییر رمز عبور": "Change password",
    "کاربر: ": "User: ",
    "رمز عبور فعلی": "Current password",
    "رمز عبور جدید": "New password",
    "تکرار رمز جدید": "Repeat new password",
    "همه فیلدها را پر کنید.": "Fill in all fields.",
    "رمز جدید باید حداقل ۴ حرف باشد.": "New password must be at least 4 characters.",
    "رمز جدید و تکرار آن یکسان نیستند.": "New password and its repeat do not match.",
    "رمز عبور با موفقیت تغییر کرد.": "Password changed successfully.",
    "رمز عبور فعلی اشتباه است.": "Current password is incorrect.",
    "زبان برنامه تغییر کرد. برنامه دوباره بارگذاری می‌شود.":
        "Application language changed. The app will reload.",

    # Print document titles / sections
    "پرونده کامل مریض": "Complete Patient File",
    "معلومات مریض": "Patient Information",
    "سوابق معالجات و ویزیت‌ها (جدول زمانی)": "Treatment & Visit History (Timeline)",
    "خلاصه مالی": "Financial Summary",
    "وضعیت دندان‌ها": "Dental Chart",
    "تعداد ویزیت‌ها": "Number of visits",
    "مجموع پرداختی": "Total paid",
    "کود مریض": "Patient code",
    "گزارش ویزیت": "Visit Report",
    "مشخصات ویزیت": "Visit Details",
    "نام مریض": "Patient name",
    "هزینه این ویزیت: ": "Cost of this visit: ",
    "ضمیمه": "Attach.",
    "ضمیمه‌ها": "Attachments",
    "نام فایل": "File name",
    "تصویر": "Image",
    "سند": "Document",
    "صورتحساب": "Invoice",
    "مشخصات مریض": "Patient Details",
    "خدمات": "Services",
    "شرح خدمات": "Service description",
    "پرداخت شده: ": "Paid: ",
    "مجموع: ": "Total: ",
    "باقیمانده: ": "Balance: ",
    "رسید پرداخت": "Payment Receipt",
    "مشخصات پرداخت": "Payment Details",
    "دریافت‌کننده": "Recipient",
    "نوع پرداخت": "Payment type",
    "روش پرداخت": "Payment method",
    "مبلغ پرداخت‌شده: ": "Amount paid: ",
    "امضای دریافت‌کننده": "Recipient signature",
    "امضای پرداخت‌کننده / مدیر": "Payer / manager signature",
    "نسخه (℞)": "Prescription (℞)",
    "℞  داروهای تجویزشده": "℞  Prescribed Medicines",
    "مقدار مصرف": "Dosage",
    "تعداد تحویلی": "Quantity to dispense",
    "دستور مصرف": "Instructions",
    "⚠ حساسیت‌ها: ": "⚠ Allergies: ",
    "امضای داکتر": "Doctor's signature",
    "راپور روزانه صندوق": "Daily Cash Report",
    "خلاصه روز": "Day Summary",
    "تعداد پرداخت‌ها": "Number of payments",
    "دریافت نقدی": "Cash received",
    "دریافت کارت/انتقال": "Card / transfer received",
    "مجموع دریافتی‌ها": "Total received",
    "مجموع مصارف امروز": "Today's total expenses",
    "باقی نقد صندوق (تقریبی)": "Cash on hand (approx.)",
    "کلینیک دندانپزشکی": "Dental Clinic",
    "داکتر: ": "Doctor: ",
    "تلفن: ": "Phone: ",
}
