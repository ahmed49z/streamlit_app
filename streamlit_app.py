import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io

# إعداد الصفحة
st.set_page_config(
    page_title="برنامج محاسبي متكامل",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تنسيق النصوص العربية
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700&display=swap');
    
    * {
        font-family: 'Tajawal', sans-serif;
        text-align: right;
    }
    
    .stButton > button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
    }
    
    .stTextInput > div > div > input {
        text-align: right;
    }
    
    .reportview-container .main .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# العنوان الرئيسي
st.title("📊 البرنامج المحاسبي المتكامل")
st.markdown("---")

# تهيئة قاعدة البيانات
def init_db():
    conn = sqlite3.connect('accounting.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # جدول العملاء
    cursor.execute('''CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        country TEXT,
        contact TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # جدول الفواتير
    cursor.execute('''CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        client_name TEXT,
        amount REAL NOT NULL,
        tax REAL DEFAULT 0,
        description TEXT,
        date DATE DEFAULT CURRENT_DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES clients(id)
    )''')
    
    # جدول الإيرادات
    cursor.execute('''CREATE TABLE IF NOT EXISTS revenue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT NOT NULL,
        amount REAL NOT NULL,
        description TEXT,
        date DATE DEFAULT CURRENT_DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # جدول المصروفات
    cursor.execute('''CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT NOT NULL,
        amount REAL NOT NULL,
        category TEXT,
        date DATE DEFAULT CURRENT_DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.commit()
    return conn

# الشريط الجانبي
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
    st.title("لوحة التحكم")
    
    menu = st.radio(
        "القائمة الرئيسية",
        ["🏠 الرئيسية", "👥 العملاء", "🧾 الفواتير", "💰 الإيرادات", "💸 المصروفات", "📈 التقارير"]
    )
    
    st.markdown("---")
    st.info("إصدار 1.0 | برنامج محاسبي متكامل")

# تهيئة قاعدة البيانات
conn = init_db()
cursor = conn.cursor()

# الصفحة الرئيسية
if menu == "🏠 الرئيسية":
    st.header("مرحباً بك في البرنامج المحاسبي")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cursor.execute("SELECT COUNT(*) FROM clients")
        clients_count = cursor.fetchone()[0]
        st.metric("عدد العملاء", clients_count)
    
    with col2:
        cursor.execute("SELECT SUM(amount) FROM invoices")
        invoices_total = cursor.fetchone()[0] or 0
        st.metric("إجمالي الفواتير", f"{invoices_total:,.2f}")
    
    with col3:
        cursor.execute("SELECT SUM(amount) FROM revenue")
        revenue_total = cursor.fetchone()[0] or 0
        st.metric("إجمالي الإيرادات", f"{revenue_total:,.2f}")
    
    with col4:
        cursor.execute("SELECT SUM(amount) FROM expenses")
        expenses_total = cursor.fetchone()[0] or 0
        st.metric("إجمالي المصروفات", f"{expenses_total:,.2f}")
    
    # الميزانية
    profit = revenue_total - expenses_total
    st.subheader("📊 الميزانية")
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**الإيرادات:** {revenue_total:,.2f}")
        st.info(f"**المصروفات:** {expenses_total:,.2f}")
        st.success(f"**صافي الربح:** {profit:,.2f}")
    
    with col2:
        if revenue_total > 0:
            expense_ratio = (expenses_total / revenue_total) * 100
            st.progress(min(int(expense_ratio), 100) / 100, text=f"نسبة المصروفات: {expense_ratio:.1f}%")

# إدارة العملاء
elif menu == "👥 العملاء":
    st.header("إدارة العملاء")
    
    tab1, tab2 = st.tabs(["إضافة عميل", "قائمة العملاء"])
    
    with tab1:
        with st.form("add_client_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("اسم العميل *", key="client_name")
                contact = st.text_input("رقم التواصل *", key="client_contact")
            
            with col2:
                country = st.selectbox(
                    "الدولة",
                    ["البحرين", "السعودية", "الإمارات", "عُمان", "قطر", "الكويت", "أخرى"],
                    key="client_country"
                )
            
            if st.form_submit_button("إضافة العميل", use_container_width=True):
                if name and contact:
                    cursor.execute(
                        "INSERT INTO clients (name, country, contact) VALUES (?, ?, ?)",
                        (name, country, contact)
                    )
                    conn.commit()
                    st.success(f"تمت إضافة العميل {name} بنجاح!")
                else:
                    st.error("يرجى ملء جميع الحقول الإلزامية (*)")
    
    with tab2:
        cursor.execute("SELECT id, name, country, contact, created_at FROM clients ORDER BY created_at DESC")
        clients = cursor.fetchall()
        
        if clients:
            df_clients = pd.DataFrame(clients, columns=["ID", "الاسم", "الدولة", "التواصل", "تاريخ الإضافة"])
            st.dataframe(df_clients, use_container_width=True)
            
            # خيارات التصدير
            csv = df_clients.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 تحميل قائمة العملاء (CSV)",
                data=csv,
                file_name="clients.csv",
                mime="text/csv"
            )
        else:
            st.info("لا يوجد عملاء مسجلين بعد")

# إدارة الفواتير
elif menu == "🧾 الفواتير":
    st.header("إدارة الفواتير")
    
    # الحصول على قائمة العملاء
    cursor.execute("SELECT id, name FROM clients")
    clients = cursor.fetchall()
    client_dict = {name: id for id, name in clients}
    
    tab1, tab2 = st.tabs(["إضافة فاتورة", "الفواتير المسجلة"])
    
    with tab1:
        with st.form("add_invoice_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                if client_dict:
                    client_name = st.selectbox("اختر العميل *", list(client_dict.keys()))
                else:
                    st.warning("لا يوجد عملاء. يرجى إضافة عميل أولاً.")
                    client_name = None
                
                amount = st.number_input("المبلغ *", min_value=0.0, step=0.01)
                tax_rate = st.slider("نسبة الضريبة %", 0, 20, 5)
            
            with col2:
                description = st.text_area("وصف الفاتورة")
                date = st.date_input("تاريخ الفاتورة", datetime.now())
            
            if st.form_submit_button("إضافة الفاتورة", use_container_width=True):
                if client_name and amount > 0:
                    client_id = client_dict[client_name]
                    tax_amount = amount * (tax_rate / 100)
                    total_amount = amount + tax_amount
                    
                    cursor.execute(
                        """INSERT INTO invoices 
                        (client_id, client_name, amount, tax, description, date) 
                        VALUES (?, ?, ?, ?, ?, ?)""",
                        (client_id, client_name, amount, tax_amount, description, date)
                    )
                    conn.commit()
                    st.success(f"تمت إضافة فاتورة بقيمة {total_amount:,.2f} (بما فيها ضريبة {tax_amount:,.2f})")
                else:
                    st.error("يرجى ملء جميع الحقول الإلزامية (*)")
    
    with tab2:
        cursor.execute("""
            SELECT i.id, c.name, i.amount, i.tax, i.description, i.date 
            FROM invoices i 
            JOIN clients c ON i.client_id = c.id 
            ORDER BY i.date DESC
        """)
        invoices = cursor.fetchall()
        
        if invoices:
            df_invoices = pd.DataFrame(invoices, columns=["ID", "العميل", "المبلغ", "الضريبة", "الوصف", "التاريخ"])
            df_invoices["الإجمالي"] = df_invoices["المبلغ"] + df_invoices["الضريبة"]
            
            # الإحصائيات
            total_invoices = df_invoices["الإجمالي"].sum()
            st.metric("إجمالي قيمة الفواتير", f"{total_invoices:,.2f}")
            
            st.dataframe(df_invoices, use_container_width=True)
            
            # تحميل البيانات
            csv = df_invoices.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 تحميل الفواتير (CSV)",
                data=csv,
                file_name="invoices.csv",
                mime="text/csv"
            )
        else:
            st.info("لا توجد فواتير مسجلة")

# الإيرادات والمصروفات (مشابه للفواتير - يمكنك إكمالها)
elif menu == "💰 الإيرادات":
    st.header("إدارة الإيرادات")
    # كود مشابه للفواتير

elif menu == "💸 المصروفات":
    st.header("إدارة المصروفات")
    # كود مشابه للفواتير

elif menu == "📈 التقارير":
    st.header("التقارير والإحصائيات")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("الإيرادات مقابل المصروفات")
        cursor.execute("SELECT date, SUM(amount) FROM revenue GROUP BY date")
        revenue_data = cursor.fetchall()
        
        cursor.execute("SELECT date, SUM(amount) FROM expenses GROUP BY date")
        expenses_data = cursor.fetchall()
        
        if revenue_data or expenses_data:
            # يمكنك إضافة رسم بياني هنا
            st.info("رسم بياني للإيرادات والمصروفات")
    
    with col2:
        st.subheader("العملاء الأكثر إنفاقاً")
        cursor.execute("""
            SELECT c.name, SUM(i.amount) as total 
            FROM invoices i 
            JOIN clients c ON i.client_id = c.id 
            GROUP BY c.name 
            ORDER BY total DESC 
            LIMIT 5
        """)
        top_clients = cursor.fetchall()
        
        if top_clients:
            for client, total in top_clients:
                st.write(f"**{client}:** {total:,.2f}")

# إغلاق الاتصال
conn.close()