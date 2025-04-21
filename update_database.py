import sqlite3

# اتصال بقاعدة البيانات
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# إضافة عمود favorite إلى جدول memorization
try:
    cursor.execute('ALTER TABLE memorization ADD COLUMN favorite BOOLEAN DEFAULT 0')
    print("تم إضافة عمود 'favorite' بنجاح")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e).lower():
        print("عمود 'favorite' موجود بالفعل")
    else:
        print(f"خطأ: {e}")

# تحديث نمط إنشاء الجدول لعمليات التثبيت المستقبلية
try:
    with open('init_db.py', 'r', encoding='utf-8') as file:
        content = file.read()
    
    # البحث عن نمط إنشاء جدول memorization
    start_idx = content.find("CREATE TABLE memorization")
    end_idx = content.find(")", start_idx) + 1
    
    table_def = content[start_idx:end_idx]
    
    # التحقق مما إذا كان عمود favorite موجود بالفعل
    if "favorite" not in table_def:
        # إضافة عمود favorite قبل القوس الأخير
        new_table_def = table_def.replace(")", ",\n    favorite BOOLEAN DEFAULT 0\n)")
        
        # استبدال تعريف الجدول القديم بالجديد
        new_content = content.replace(table_def, new_table_def)
        
        # حفظ الملف المعدل
        with open('init_db.py', 'w', encoding='utf-8') as file:
            file.write(new_content)
        
        print("تم تحديث ملف init_db.py بنجاح")
    else:
        print("عمود 'favorite' موجود بالفعل في ملف init_db.py")

except Exception as e:
    print(f"خطأ في تحديث ملف init_db.py: {e}")

# إغلاق الاتصال
conn.commit()
conn.close()

print("تم الانتهاء من تحديث قاعدة البيانات")