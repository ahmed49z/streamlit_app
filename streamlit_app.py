import streamlit as st
import sqlite3
import pandas as pd
import csv
import io
from datetime import datetime

# إعداد الصفحة
st.set_page_config(
    page_title="برنامج محاسبي متكامل",
    page_icon="💰",
    layout="wide"
)

# تنسيق عربي
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700&display=swap');
    
    * {
        font-family: 'Tajawal', sans-serif !important;
        text-align: right !important;
        direction: rtl !important;
    }
    
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        border-radius: 5px;
        border: none;
        padding: 10px 20px;
    }
    
    .stButton > button:hover {
        background-color: #45a049;
    }
    
    .stSelectbox > div > div {
        text-align: right;
    }
    
    .stNumberInput > div > div > input {
        text-align: right;
    }
    
    h1, h2, h3 {
        color: #2c3e50;
    }
</style>
""", unsafe_allow_html=True)

# تهيئة قاعدة البيانات
@st.cache_resource
def init_db():
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    cursor = conn.cursor()
    
    # إنشاء الجداول
    cursor.execute('''CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client TEXT,
        country TEXT,
        amount REAL,
        tax REAL,
        date TEXT DEFAULT CURRENT_DATE
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT,
        amount REAL,
        date TEXT DEFAULT CURRENT_DATE
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS revenue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        amount REAL,
        date TEXT DEFAULT CURRENT_DATE
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        country TEXT,
        contact TEXT
    )''')
    
    # بيانات تجريبية
    cursor.execute("INSERT OR IGNORE INTO clients (name, country, contact) VALUES (?, ?, ?)", 
                   ('شركة النجاح', 'السعودية', '0112345678'))
    cursor.execute("INSERT OR IGNORE INTO clients (name, country, contact) VALUES (?, ?, ?)", 
                   ('مؤسسة التميز', 'البحرين', '33221100'))
    
    conn.commit()
    return conn

# الاتصال بقاعدة البيانات
conn = init_db()

# العنوان الرئيسي
st.title("💰 برنامج محاسبي متكامل")
st.markdown("---")

# تحميل العملاء
def load_clients():
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, country, contact FROM clients ORDER BY name")
    return cursor.fetchall()

# الواجهة الرئيسية
clients = load_clients()

if clients:
    # اختيار العميل
    client_options = [f"{name} - {country}" for _, name, country, _ in clients]
    selected_client = st.selectbox("👥 اختر العميل:", client_options)
    
    # استخراج اسم العميل المختار
    client_name = selected_client.split(" - ")[0] if selected_client else ""
    
    # عرض معلومات العميل
    for client in clients:
        if client[1] == client_name:
            st.info(f"**العميل:** {client[1]} | **الدولة:** {client[2]} | **التواصل:** {client[3]}")
            break
else:
    st.warning("⚠️ لا يوجد عملاء. الرجاء إضافة عميل أولاً.")
    client_name = ""

# أزرار التنقل بين العملاء
if len(clients) > 1:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("◀ السابق"):
            # يمكن إضافة منطق التنقل هنا
            st.rerun()
    with col2:
        if st.button("التالي ▶"):
            st.rerun()

# تبويبات الوظائف
tab1, tab2, tab3, tab4 = st.tabs(["📋 الفواتير", "💰 الإيرادات", "💸 المصروفات", "👥 الإدارة"])

# تبويب الفواتير
with tab1:
    st.header("إدارة الفواتير")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.form("add_invoice_form"):
            st.subheader("إضافة فاتورة جديدة")
            
            if not clients:
                st.error("يجب إضافة عميل أولاً")
            else:
                client_names = [name for _, name, _, _ in clients]
                selected_invoice_client = st.selectbox("العميل:", client_names, key="invoice_client")
            
            country = st.selectbox("الدولة:", ["البحرين", "السعودية", "الإمارات", "عُمان", "قطر", "الكويت"])
            amount = st.number_input("المبلغ (ر.س):", min_value=0.0, step=0.01)
            
            if st.form_submit_button("➕ إضافة فاتورة"):
                if amount > 0 and selected_invoice_client:
                    tax = amount * 0.05
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO invoices (client, country, amount, tax, date) VALUES (?, ?, ?, ?, DATE('now'))",
                        (selected_invoice_client, country, amount, tax)
                    )
                    conn.commit()
                    st.success(f"✅ تمت إضافة فاتورة بقيمة {amount:.2f} ريال")
                    st.rerun()
                else:
                    st.error("يرجى ملء جميع الحقول")
    
    with col2:
        st.subheader("تصدير الفواتير")
        if client_name:
            cursor = conn.cursor()
            cursor.execute("SELECT client, country, amount, tax, date FROM invoices WHERE client=?", (client_name,))
            invoices = cursor.fetchall()
            
            if invoices:
                df = pd.DataFrame(invoices, columns=["العميل", "الدولة", "المبلغ", "الضريبة", "التاريخ"])
                st.dataframe(df, use_container_width=True)
                
                # تحويل إلى CSV
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                csv_str = csv_buffer.getvalue()
                
                st.download_button(
                    label="📥 تحميل CSV",
                    data=csv_str,
                    file_name=f"فواتير_{client_name}.csv",
                    mime="text/csv"
                )
            else:
                st.info("لا توجد فواتير لهذا العميل")

# تبويب الإيرادات
with tab2:
    st.header("إدارة الإيرادات")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.form("add_revenue_form"):
            st.subheader("إضافة إيراد جديد")
            source = st.text_input("مصدر الإيراد:")
            amount = st.number_input("المبلغ (ر.س):", min_value=0.0, step=0.01, key="rev_amount")
            
            if st.form_submit_button("➕ إضافة إيراد"):
                if source and amount > 0:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO revenue (source, amount, date) VALUES (?, ?, DATE('now'))",
                        (source, amount)
                    )
                    conn.commit()
                    st.success(f"✅ تمت إضافة إيراد بقيمة {amount:.2f} ريال")
                    st.rerun()
                else:
                    st.error("يرجى ملء جميع الحقول")
    
    with col2:
        st.subheader("تصدير الإيرادات")
        cursor = conn.cursor()
        cursor.execute("SELECT source, amount, date FROM revenue ORDER BY date DESC")
        revenue = cursor.fetchall()
        
        if revenue:
            df = pd.DataFrame(revenue, columns=["المصدر", "المبلغ", "التاريخ"])
            st.dataframe(df, use_container_width=True)
            
            total_revenue = df["المبلغ"].sum()
            st.metric("إجمالي الإيرادات", f"{total_revenue:.2f} ر.س")
            
            # تحويل إلى CSV
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
            csv_str = csv_buffer.getvalue()
            
            st.download_button(
                label="📥 تحميل CSV",
                data=csv_str,
                file_name="الإيرادات.csv",
                mime="text/csv",
                key="rev_csv"
            )
        else:
            st.info("لا توجد إيرادات مسجلة")

# تبويب المصروفات
with tab3:
    st.header("إدارة المصروفات")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.form("add_expense_form"):
            st.subheader("إضافة مصروف جديد")
            description = st.text_input("وصف المصروف:")
            amount = st.number_input("المبلغ (ر.س):", min_value=0.0, step=0.01, key="exp_amount")
            
            if st.form_submit_button("➕ إضافة مصروف"):
                if description and amount > 0:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO expenses (description, amount, date) VALUES (?, ?, DATE('now'))",
                        (description, amount)
                    )
                    conn.commit()
                    st.success(f"✅ تمت إضافة مصروف بقيمة {amount:.2f} ريال")
                    st.rerun()
                else:
                    st.error("يرجى ملء جميع الحقول")
    
    with col2:
        st.subheader("تصدير المصروفات")
        cursor = conn.cursor()
        cursor.execute("SELECT description, amount, date FROM expenses ORDER BY date DESC")
        expenses = cursor.fetchall()
        
        if expenses:
            df = pd.DataFrame(expenses, columns=["الوصف", "المبلغ", "التاريخ"])
            st.dataframe(df, use_container_width=True)
            
            total_expenses = df["المبلغ"].sum()
            st.metric("إجمالي المصروفات", f"{total_expenses:.2f} ر.س")
            
            # تحويل إلى CSV
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
            csv_str = csv_buffer.getvalue()
            
            st.download_button(
                label="📥 تحميل CSV",
                data=csv_str,
                file_name="المصروفات.csv",
                mime="text/csv",
                key="exp_csv"
            )
        else:
            st.info("لا توجد مصروفات مسجلة")

# تبويب الإدارة (العملاء)
with tab4:
    st.header("إدارة العملاء")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.form("add_client_form"):
            st.subheader("إضافة عميل جديد")
            name = st.text_input("اسم العميل:")
            country = st.selectbox("الدولة:", ["البحرين", "السعودية", "الإمارات", "عُمان", "قطر", "الكويت", "أخرى"], key="client_country")
            contact = st.text_input("رقم التواصل:")
            
            if st.form_submit_button("➕ إضافة عميل"):
                if name and contact:
                    try:
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO clients (name, country, contact) VALUES (?, ?, ?)",
                            (name, country, contact)
                        )
                        conn.commit()
                        st.success(f"✅ تمت إضافة العميل {name} بنجاح!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("⚠️ اسم العميل موجود مسبقاً")
                else:
                    st.error("يرجى ملء جميع الحقول")
    
    with col2:
        st.subheader("قائمة العملاء")
        clients_list = load_clients()
        
        if clients_list:
            df_clients = pd.DataFrame(clients_list, columns=["ID", "الاسم", "الدولة", "التواصل"])
            st.dataframe(df_clients[["الاسم", "الدولة", "التواصل"]], use_container_width=True)
            
            # خيار حذف عميل
            client_to_delete = st.selectbox(
                "اختر عميل لحذفه:",
                [name for _, name, _, _ in clients_list],
                key="delete_client"
            )
            
            if st.button("🗑️ حذف العميل", type="secondary"):
                cursor = conn.cursor()
                cursor.execute("DELETE FROM clients WHERE name = ?", (client_to_delete,))
                conn.commit()
                st.success(f"تم حذف العميل {client_to_delete}")
                st.rerun()
        else:
            st.info("لا يوجد عملاء مسجلين")

# تذييل الصفحة - الإحصائيات
st.markdown("---")
st.header("📊 الإحصائيات الكلية")

col1, col2, col3, col4 = st.columns(4)

with col1:
    cursor = conn.cursor()
    if client_name:
        cursor.execute("SELECT SUM(amount) FROM invoices WHERE client=?", (client_name,))
        total_invoices = cursor.fetchone()[0] or 0
        st.metric("فواتير العميل", f"{total_invoices:.2f} ر.س")
    else:
        st.metric("فواتير العميل", "0.00 ر.س")

with col2:
    cursor.execute("SELECT SUM(amount) FROM revenue")
    total_revenue = cursor.fetchone()[0] or 0
    st.metric("إجمالي الإيرادات", f"{total_revenue:.2f} ر.س")

with col3:
    cursor.execute("SELECT SUM(amount) FROM expenses")
    total_expenses = cursor.fetchone()[0] or 0
    st.metric("إجمالي المصروفات", f"{total_expenses:.2f} ر.س")

with col4:
    remaining = total_revenue - total_expenses
    color = "normal" if remaining >= 0 else "inverse"
    st.metric("المتبقي", f"{remaining:.2f} ر.س", delta_color=color)

# زر تصدير تقرير شامل
st.markdown("---")
if st.button("📊 إنشاء تقرير شامل (PDF)"):
    st.info("""
    **معلومات حول التقرير:**
    
    لتصدير تقرير PDF، يمكنك تثبيت مكتبة `reportlab`:
    
    ```bash
    pip install reportlab
    ```
    
    أو استخدم خيار CSV المتاح في كل قسم.
    """)

# تذييل
st.markdown("---")
st.caption("© 2026 البرنامج المحاسبي المتكامل | إصدار Streamlit 1.0")
