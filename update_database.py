import sqlite3

# اتصال بقاعدة البيانات
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# إضافة أعمدة جديدة إلى جدول memorization
try:
    # إضافة عمود start_page
    cursor.execute('ALTER TABLE memorization ADD COLUMN start_page INTEGER')
    print("تم إضافة عمود 'start_page' بنجاح")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e).lower():
        print("عمود 'start_page' موجود بالفعل")
    else:
        print(f"خطأ: {e}")

try:
    # إضافة عمود end_page
    cursor.execute('ALTER TABLE memorization ADD COLUMN end_page INTEGER')
    print("تم إضافة عمود 'end_page' بنجاح")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e).lower():
        print("عمود 'end_page' موجود بالفعل")
    else:
        print(f"خطأ: {e}")

# تحديث البيانات الموجودة (تعيين قيم للبيانات الحالية بناءً على الصفحات وأرقام السور)
print("تحديث السجلات الموجودة...")
try:
    # الحصول على جميع السجلات التي تحتاج إلى تحديث
    cursor.execute('''
        SELECT m.id, m.surah_id, m.pages, s.start_page, s.end_page
        FROM memorization m
        JOIN surahs s ON m.surah_id = s.id
        WHERE m.start_page IS NULL OR m.end_page IS NULL
    ''')
    records = cursor.fetchall()
    
    updated_count = 0
    for record in records:
        record_id, surah_id, pages, surah_start, surah_end = record
        
        # إذا كان عدد الصفحات معروفاً، قم بتقدير نطاق الصفحات
        if pages:
            start_page = surah_start
            end_page = min(surah_start + pages - 1, surah_end)
        else:
            # إذا لم يكن عدد الصفحات معروفاً، استخدم بداية ونهاية السورة
            start_page = surah_start
            end_page = surah_start
            pages = 1  # تعيين قيمة افتراضية

        # تحديث السجل
        cursor.execute('''
            UPDATE memorization
            SET start_page = ?, end_page = ?, pages = ?
            WHERE id = ?
        ''', (start_page, end_page, pages, record_id))
        
        updated_count += 1
    
    print(f"تم تحديث {updated_count} سجل")
    
except Exception as e:
    print(f"خطأ في تحديث السجلات: {e}")

# تحديث نمط إنشاء الجدول لعمليات التثبيت المستقبلية
try:
    with open('init_db.py', 'r', encoding='utf-8') as file:
        content = file.read()
    
    # البحث عن نمط إنشاء جدول memorization
    start_idx = content.find("CREATE TABLE memorization")
    end_idx = content.find(")", start_idx) + 1
    
    table_def = content[start_idx:end_idx]
    
    # التحقق مما إذا كانت الأعمدة الجديدة موجودة بالفعل
    if "start_page" not in table_def:
        # إضافة الأعمدة الجديدة قبل القوس الأخير
        new_table_def = table_def.replace("favorite BOOLEAN DEFAULT 0", 
                                          "favorite BOOLEAN DEFAULT 0,\n    start_page INTEGER,\n    end_page INTEGER")
        
        # استبدال تعريف الجدول القديم بالجديد
        new_content = content.replace(table_def, new_table_def)
        
        # حفظ الملف المعدل
        with open('init_db.py', 'w', encoding='utf-8') as file:
            file.write(new_content)
        
        print("تم تحديث ملف init_db.py بنجاح")
    else:
        print("الأعمدة الجديدة موجودة بالفعل في ملف init_db.py")

except Exception as e:
    print(f"خطأ في تحديث ملف init_db.py: {e}")

# إغلاق الاتصال
conn.commit()
conn.close()

print("تم الانتهاء من تحديث قاعدة البيانات")