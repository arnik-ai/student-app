import streamlit as st
import pandas as pd
import os, uuid
from datetime import datetime

# ---------- تنظیمات صفحه ----------
st.set_page_config(page_title="ثبت‌نام دانش‌آموزان", layout="wide")

# ---------- مسیرها ----------
CSV_FILE = "students.csv"
UPLOAD_DIR = "uploads"
GALLERY_DIR = os.path.join(UPLOAD_DIR, "gallery")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(GALLERY_DIR, exist_ok=True)

# ---------- ستون‌های استاندارد ----------
REQUIRED_COLS = [
    "نام","نام خانوادگی","سن","کلاس","ایمیل",
    "جنسیت","بازخورد","زمان ثبت","عکس","قبول قوانین"
]

# ---------- توابع کمکی ----------
def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    for c in REQUIRED_COLS:
        if c not in df.columns:
            df[c] = "" if c not in ["سن","قبول قوانین"] else (0 if c=="سن" else False)
    df = df[REQUIRED_COLS]
    df["عکس"] = df["عکس"].fillna("")
    return df

def load_df() -> pd.DataFrame:
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
        except UnicodeDecodeError:
            df = pd.read_csv(CSV_FILE, encoding="utf-8-sig")
        return ensure_columns(df)
    else:
        return pd.DataFrame(columns=REQUIRED_COLS)

def save_df(df: pd.DataFrame):
    df = ensure_columns(df)
    df.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")

def save_uploaded_file(uploaded_file, folder=UPLOAD_DIR) -> str:
    if uploaded_file is None:
        return ""
    name, ext = os.path.splitext(uploaded_file.name)
    unique_name = f"{uuid.uuid4().hex}{ext.lower()}"
    path = os.path.join(folder, unique_name)
    with open(path, "wb") as f:
        f.write(uploaded_file.read())
    return path

def show_table(df: pd.DataFrame, height=400):
    if df.empty:
        st.info("هیچ داده‌ای برای نمایش وجود ندارد.")
        return

    search_query = st.text_input("🔍 جستجو در کل جدول")
    filtered_df = df.copy()
    if search_query:
        filtered_df = df[df.apply(
            lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1
        )]

    sort_col = st.selectbox("📦 مرتب‌سازی بر اساس ستون", filtered_df.columns)
    sort_order = st.radio("ترتیب", ["صعودی", "نزولی"], horizontal=True)

    sorted_df = filtered_df.sort_values(
        by=sort_col,
        ascending=True if sort_order == "صعودی" else False
    )

    st.data_editor(sorted_df, use_container_width=True, height=height)

# ---------- داده اولیه ----------
students_df = load_df()

# ---------- Sidebar ----------
st.sidebar.title("منوی اصلی")
table_height = st.sidebar.slider("ارتفاع جدول", 200, 800, 380, step=20)
choice = st.sidebar.radio("menu :", ["📋 Form", "📊 CSV Uploader", "📷 Gallery"])

# =========================================================
# 📋 Form
# =========================================================
if choice == "📋 Form":
    st.title("📋 فرم ثبت‌نام دانش‌آموزان")

    with st.form("student_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("نام")
            age = st.number_input("سن", min_value=6, max_value=20, step=1, value=12)
            email = st.text_input("ایمیل یا شماره تماس")
            gender = st.radio("جنسیت", options=["دختر","پسر","دیگر"], horizontal=True)
        with col2:
            last_name = st.text_input("نام خانوادگی")
            grade = st.selectbox("پایه تحصیلی", ["هفتم","هشتم","نهم","دهم","یازدهم","دوازدهم"])
            photo = st.file_uploader("📷 عکس دانش‌آموز", type=["jpg","jpeg","png"])
            accept = st.checkbox("I accept (قوانین را می‌پذیرم)")

        feedback = st.text_area("🗒️ باکس بازخورد", placeholder="نکات خاص یا پیام برای مربی...")

        submitted = st.form_submit_button("ثبت اطلاعات")

        if submitted:
            if not first_name or not last_name:
                st.error("⚠️ لطفاً نام و نام خانوادگی را وارد کنید")
            elif not accept:
                st.error("⚠️ برای ادامه باید گزینه I accept را تیک بزنید")
            elif not email:
                st.error("⚠️ لطفاً ایمیل یا شماره تماس را وارد کنید")
            else:
                # جلوگیری از رکورد تکراری (بر اساس ایمیل)
                if not students_df[students_df["ایمیل"] == email].empty:
                    st.warning("⚠️ این ایمیل قبلاً ثبت شده است.")
                else:
                    photo_path = save_uploaded_file(photo) if photo else ""
                    new_row = {
                        "نام": first_name,
                        "نام خانوادگی": last_name,
                        "سن": int(age),
                        "کلاس": grade,
                        "ایمیل": email,
                        "جنسیت": gender,
                        "بازخورد": feedback,
                        "زمان ثبت": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "عکس": photo_path,
                        "قبول قوانین": True
                    }
                    students_df = pd.concat([students_df, pd.DataFrame([new_row])], ignore_index=True)
                    save_df(students_df)
                    st.success("✅ اطلاعات با موفقیت ثبت شد")

                    st.subheader("رکورد جدید:")
                    show_table(pd.DataFrame([new_row]), height=200)

    st.subheader("📊 لیست دانش‌آموزان")
    show_table(students_df, height=table_height)

# =========================================================
# 📊 CSV Uploader
# =========================================================
elif choice == "📊 CSV Uploader":
    st.title("📊 آپلود CSV و بروزرسانی داده‌ها")
    mode = st.radio("حالت:", ["Append (افزودن)", "Replace (جایگزینی کامل)"], horizontal=True)
    csv_file = st.file_uploader("📂 فایل CSV", type=["csv"])

    with st.expander("📥 دانلود قالب CSV"):
        templ = pd.DataFrame(columns=REQUIRED_COLS)
        st.download_button("دانلود قالب", data=templ.to_csv(index=False, encoding="utf-8-sig"),
                           file_name="students_template.csv", mime="text/csv")

    if csv_file is not None:
        try:
            df_new = pd.read_csv(csv_file)
        except UnicodeDecodeError:
            df_new = pd.read_csv(csv_file, encoding="utf-8-sig")

        df_new = ensure_columns(df_new)

        if mode.startswith("Replace"):
            students_df = df_new.copy()
            action_msg = "جایگزینی کامل انجام شد."
        else:
            # حذف رکوردهای تکراری بر اساس ایمیل
            combined = pd.concat([students_df, df_new], ignore_index=True)
            students_df = combined.drop_duplicates(subset=["ایمیل"])
            action_msg = f"افزودن {len(df_new)} ردیف انجام شد (تکراری‌ها حذف شدند)."

        save_df(students_df)
        st.success(f"✅ {action_msg} (کل ردیف‌ها: {len(students_df)})")
        show_table(students_df, height=table_height)

# =========================================================
# 📷 Gallery
# =========================================================
elif choice == "📷 Gallery":
    st.title("📷 گالری تصاویر")

    st.subheader("عکس‌های ثبت‌شده همراه فرم")
    if len(students_df) > 0:
        cols = st.columns(4)
        count = 0
        for idx, row in students_df.iterrows():
            photo_path = row.get("عکس", "")
            if isinstance(photo_path, str) and photo_path and os.path.exists(photo_path):
                with cols[count % 4]:
                    st.image(photo_path, use_column_width=True, caption=f"{row['نام']} {row['نام خانوادگی']}")
                count += 1
        if count == 0:
            st.info("فعلاً عکسی وجود ندارد.")
    else:
        st.info("هیچ دانش‌آموزی ثبت نشده.")

    st.markdown("---")
    st.subheader("➕ آپلود عکس‌های جدید")

    new_photos = st.file_uploader("چند عکس انتخاب کنید", type=["jpg","jpeg","png"], accept_multiple_files=True)
    if new_photos:
        saved = []
        for up in new_photos:
            p = save_uploaded_file(up, folder=GALLERY_DIR)
            saved.append(p)
        st.success(f"✅ {len(saved)} تصویر ذخیره شد.")
        cols2 = st.columns(4)
        for i, p in enumerate(saved):
            with cols2[i % 4]:
                st.image(p, use_column_width=True)

