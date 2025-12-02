import streamlit as st
import pandas as pd
import sqlite3
import io
from datetime import datetime
from contextlib import closing

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
        direction: rtl;
    }
    
    .stButton > button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    
    .stTextInput > div > div > input {
        text-align: right;
    }
    
    .reportview-container .main .block-container {
        padding-top: 2rem;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #2c3e50;
    }
</style>
""", unsafe_allow_html=True)

# العنوان الرئيسي
st.title("📊 البرنامج المحاسبي المتكامل")
st.markdown("---")

# تهيئة قاعدة البيانات في الذاكرة
def init_db():
    conn = sqlite3.connect(':memory:', check_same_thread=False)
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
        client_name TEXT,
        amount REAL NOT NULL,
        tax REAL DEFAULT 0,
        description TEXT,
        date DATE DEFAULT CURRENT_DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    
    # إضافة بيانات تجريبية
    cursor.execute("INSERT OR IGNORE INTO clients (name, country, contact) VALUES (?, ?, ?)",
                  ('شركة التقنية المحدودة', 'السعودية', '0112345678'))
    cursor.execute("INSERT OR IGNORE INTO clients (name, country, contact) VALUES (?, ?, ?)",
                  ('مؤسسة النجاح', 'البحرين', '33221100'))
    
    cursor.execute("INSERT OR IGNORE INTO invoices (client_name, amount, tax, description) VALUES (?, ?, ?, ?)",
                  ('شركة التقنية المحدودة', 5000.00, 250.00, 'تصميم موقع إلكتروني'))
    
    conn.commit()
    return conn

# الاتصال بقاعدة البيانات
conn = init_db()

# الشريط الجانبي
with st.sidebar:
    st.image("📊", width=80)
    st.title("لوحة التحكم")
    
    menu = st.radio(
        "القائمة الرئيسية",
        ["🏠 الرئيسية", "👥 العملاء", "🧾 الفواتير", "💰 الإيرادات", "💸 المصروفات", "⚙️ الإعدادات"]
    )
    
    st.markdown("---")
    st.info("إصدار 1.0 | برنامج محاسبي متكامل")
    
    # إحصائيات سريعة
    with closing(conn.cursor()) as cursor:
        cursor.execute("SELECT COUNT(*) FROM clients")
        clients_count = cursor.fetchone()[0]
        st.caption(f"👥 العملاء: {clients_count}")
        
        cursor.execute("SELECT COUNT(*) FROM invoices")
        invoices_count = cursor.fetchone()[0]
        st.caption(f"🧾 الفواتير: {invoices_count}")

# الصفحة الرئيسية
if menu == "🏠 الرئيسية":
    st.header("🏠 لوحة التحكم الرئيسية")
    
    # بطاقات الإحصائيات
    col1, col2, col3, col4 = st.columns(4)
    
    with closing(conn.cursor()) as cursor:
        with col1:
            cursor.execute("SELECT COUNT(*) FROM clients")
            clients_count = cursor.fetchone()[0]
            st.metric("عدد العملاء", clients_count, "👥")
        
        with col2:
            cursor.execute("SELECT SUM(amount) FROM invoices")
            invoices_total = cursor.fetchone()[0] or 0
            st.metric("إجمالي الفواتير", f"{invoices_total:,.2f}", "💰")
        
        with col3:
            cursor.execute("SELECT SUM(amount) FROM revenue")
            revenue_total = cursor.fetchone()[0] or 0
            st.metric("إجمالي الإيرادات", f"{revenue_total:,.2f}", "📈")
        
        with col4:
            cursor.execute("SELECT SUM(amount) FROM expenses")
            expenses_total = cursor.fetchone()[0] or 0
            st.metric("إجمالي المصروفات", f"{expenses_total:,.2f}", "💸")
    
    # الميزانية
    st.subheader("📊 الميزانية")
    col1, col2 = st.columns(2)
    
    with col1:
        profit = revenue_total - expenses_total
        st.info(f"**الإيرادات:** {revenue_total:,.2f} ريال")
        st.info(f"**المصروفات:** {expenses_total:,.2f} ريال")
        st.success(f"**صافي الربح:** {profit:,.2f} ريال")
    
    with col2:
        if revenue_total > 0:
            expense_ratio = (expenses_total / revenue_total) * 100
            profit_ratio = 100 - expense_ratio
            st.metric("نسبة الربح", f"{profit_ratio:.1f}%")
        else:
            st.info("لا توجد إيرادات مسجلة")
    
    # العملاء الأخيرين
    st.subheader("👥 آخر العملاء المضافين")
    with closing(conn.cursor()) as cursor:
        cursor.execute("SELECT name, country, contact, created_at FROM clients ORDER BY created_at DESC LIMIT 5")
        clients = cursor.fetchall()
        
        if clients:
            df_clients = pd.DataFrame(clients, columns=["الاسم", "الدولة", "التواصل", "تاريخ الإضافة"])
            st.dataframe(df_clients, use_container_width=True)
        else:
            st.info("لا يوجد عملاء مسجلين بعد")

# إدارة العملاء
elif menu == "👥 العملاء":
    st.header("👥 إدارة العملاء")
    
    tab1, tab2 = st.tabs(["➕ إضافة عميل جديد", "📋 قائمة العملاء"])
    
    with tab1:
        with st.form("add_client_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("اسم العميل *", placeholder="أدخل اسم العميل الكامل")
                contact = st.text_input("رقم التواصل *", placeholder="رقم الهاتف أو البريد")
            
            with col2:
                country = st.selectbox(
                    "الدولة",
                    ["اختر الدولة", "البحرين", "السعودية", "الإمارات", "عُمان", "قطر", "الكويت", "أخرى"]
                )
            
            submitted = st.form_submit_button("✅ إضافة العميل", use_container_width=True)
            
            if submitted:
                if name and contact and country != "اختر الدولة":
                    try:
                        with closing(conn.cursor()) as cursor:
                            cursor.execute(
                                "INSERT INTO clients (name, country, contact) VALUES (?, ?, ?)",
                                (name, country, contact)
                            )
                            conn.commit()
                            st.success(f"✅ تمت إضافة العميل **{name}** بنجاح!")
                            st.balloons()
                    except Exception as e:
                        st.error(f"حدث خطأ: {e}")
                else:
                    st.error("⚠️ يرجى ملء جميع الحقول الإلزامية (*)")
    
    with tab2:
        with closing(conn.cursor()) as cursor:
            cursor.execute("SELECT id, name, country, contact, created_at FROM clients ORDER BY created_at DESC")
            clients = cursor.fetchall()
            
            if clients:
                df_clients = pd.DataFrame(clients, columns=["ID", "الاسم", "الدولة", "التواصل", "تاريخ الإضافة"])
                st.dataframe(df_clients, use_container_width=True, hide_index=True)
                
                # خيارات التصدير
                csv = df_clients.to_csv(index=False, encoding='utf-8-sig')
                col1, col2 = st.columns(2)
                
                with col1:
                    st.download_button(
                        label="📥 تحميل قائمة العملاء (CSV)",
                        data=csv,
                        file_name="clients.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with col2:
                    if st.button("🗑️ حذف جميع العملاء", use_container_width=True):
                        with closing(conn.cursor()) as cur:
                            cur.execute("DELETE FROM clients")
                            conn.commit()
                            st.success("تم حذف جميع العملاء")
                            st.rerun()
            else:
                st.info("📭 لا يوجد عملاء مسجلين بعد")

# إدارة الفواتير
elif menu == "🧾 الفواتير":
    st.header("🧾 إدارة الفواتير")
    
    # الحصول على قائمة العملاء
    with closing(conn.cursor()) as cursor:
        cursor.execute("SELECT name FROM clients")
        clients_list = [row[0] for row in cursor.fetchall()]
    
    tab1, tab2 = st.tabs(["➕ إضافة فاتورة جديدة", "📋 الفواتير المسجلة"])
    
    with tab1:
        with st.form("add_invoice_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                if clients_list:
                    client_name = st.selectbox("اختر العميل *", clients_list)
                else:
                    st.warning("⚠️ لا يوجد عملاء. يرجى إضافة عميل أولاً.")
                    client_name = None
                
                amount = st.number_input("المبلغ *", min_value=0.0, step=0.01, value=0.0)
                tax_rate = st.slider("نسبة الضريبة %", 0, 20, 5)
            
            with col2:
                description = st.text_area("وصف الفاتورة", placeholder="وصف الخدمة أو المنتج")
                date = st.date_input("تاريخ الفاتورة", datetime.now())
            
            submitted = st.form_submit_button("✅ إضافة الفاتورة", use_container_width=True)
            
            if submitted:
                if client_name and amount > 0:
                    tax_amount = amount * (tax_rate / 100)
                    total_amount = amount + tax_amount
                    
                    try:
                        with closing(conn.cursor()) as cursor:
                            cursor.execute(
                                """INSERT INTO invoices 
                                (client_name, amount, tax, description, date) 
                                VALUES (?, ?, ?, ?, ?)""",
                                (client_name, amount, tax_amount, description, date)
                            )
                            conn.commit()
                            st.success(f"✅ تمت إضافة فاتورة بقيمة **{total_amount:,.2f}** ريال")
                            st.info(f"المبلغ الأساسي: {amount:,.2f} | الضريبة: {tax_amount:,.2f}")
                    except Exception as e:
                        st.error(f"حدث خطأ: {e}")
                else:
                    st.error("⚠️ يرجى اختيار عميل وإدخال مبلغ صحيح")
    
    with tab2:
        with closing(conn.cursor()) as cursor:
            cursor.execute("""
                SELECT client_name, amount, tax, description, date 
                FROM invoices 
                ORDER BY date DESC
            """)
            invoices = cursor.fetchall()
            
            if invoices:
                df_invoices = pd.DataFrame(invoices, 
                    columns=["العميل", "المبلغ", "الضريبة", "الوصف", "التاريخ"])
                df_invoices["الإجمالي"] = df_invoices["المبلغ"] + df_invoices["الضريبة"]
                
                # الإحصائيات
                total_amount = df_invoices["الإجمالي"].sum()
                st.metric("💰 إجمالي قيمة الفواتير", f"{total_amount:,.2f} ريال")
                
                st.dataframe(df_invoices, use_container_width=True, hide_index=True)
                
                # تحميل البيانات
                csv = df_invoices.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 تحميل الفواتير (CSV)",
                    data=csv,
                    file_name="invoices.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.info("📭 لا توجد فواتير مسجلة")

# باقي القوائم (يمكنك إكمالها بنفس الطريقة)
elif menu == "💰 الإيرادات":
    st.header("💰 إدارة الإيرادات")
    st.info("قريباً... سيتم تفعيل هذه الصفحة في التحديث القادم")
    
elif menu == "💸 المصروفات":
    st.header("💸 إدارة المصروفات")
    st.info("قريباً... سيتم تفعيل هذه الصفحة في التحديث القادم")

elif menu == "⚙️ الإعدادات":
    st.header("⚙️ إعدادات النظام")
    
    st.subheader("تصدير جميع البيانات")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 تصدير العملاء", use_container_width=True):
            with closing(conn.cursor()) as cursor:
                cursor.execute("SELECT * FROM clients")
                data = cursor.fetchall()
                if data:
                    df = pd.DataFrame(data)
                    csv = df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="تحميل الآن",
                        data=csv,
                        file_name="clients_full.csv",
                        mime="text/csv"
                    )
    
    with col2:
        if st.button("📥 تصدير الفواتير", use_container_width=True):
            with closing(conn.cursor()) as cursor:
                cursor.execute("SELECT * FROM invoices")
                data = cursor.fetchall()
                if data:
                    df = pd.DataFrame(data)
                    csv = df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="تحميل الآن",
                        data=csv,
                        file_name="invoices_full.csv",
                        mime="text/csv"
                    )
    
    st.subheader("إحصائيات النظام")
    with closing(conn.cursor()) as cursor:
        cursor.execute("SELECT COUNT(*) FROM clients")
        clients = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM invoices")
        invoices = cursor.fetchone()[0]
        
        st.write(f"**عدد العملاء:** {clients}")
        st.write(f"**عدد الفواتير:** {invoices}")
        st.write(f"**تاريخ النظام:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# إغلاق الاتصال عند إنهاء الجلسة
conn.close()

# تذييل الصفحة
st.markdown("---")
st.caption("© 2026 البرنامج المحاسبي المتكامل | إصدار 1.0 | تطوير: ahmed49z")
