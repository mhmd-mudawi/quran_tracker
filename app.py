from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, Response
import sqlite3
import json
from datetime import datetime
import os
import shutil
import zipfile
import io
import tempfile

app = Flask(__name__)
app.secret_key = 'quran_memorization_tracker'

# Helper functions
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_all_surahs():
    conn = get_db_connection()
    surahs = conn.execute('SELECT * FROM surahs ORDER BY id').fetchall()
    conn.close()
    return surahs

def get_all_reciters():
    conn = get_db_connection()
    reciters = conn.execute('SELECT * FROM reciters ORDER BY name').fetchall()
    conn.close()
    return reciters

def get_surah_by_id(surah_id):
    conn = get_db_connection()
    surah = conn.execute('SELECT * FROM surahs WHERE id = ?', (surah_id,)).fetchone()
    conn.close()
    return surah

def get_juz_by_id(juz_id):
    conn = get_db_connection()
    juz = conn.execute('SELECT * FROM juz WHERE id = ?', (juz_id,)).fetchone()
    conn.close()
    return juz

def get_all_juz():
    conn = get_db_connection()
    juz = conn.execute('SELECT * FROM juz ORDER BY id').fetchall()
    conn.close()
    return juz

def get_memorization_stats():
    conn = get_db_connection()
    
    # Total verses memorized
    total_verses = conn.execute('SELECT SUM(end_verse - start_verse + 1) as total FROM memorization').fetchone()
    total_verses = total_verses['total'] if total_verses['total'] else 0
    
    # Total pages memorized
    total_pages = conn.execute('SELECT SUM(end_page - start_page + 1) as total FROM memorization').fetchone()
    total_pages = total_pages['total'] if total_pages['total'] else 0
    
    # تعديل: حساب عدد السور المكتملة (محفوظة بالكامل) فقط بدلاً من السور المحفوظة جزئياً
    surahs_data = []
    all_surahs = get_all_surahs()
    
    for surah in all_surahs:
        # الحصول على جميع آيات السورة المحفوظة
        memorized_verses = set()
        memorizations = conn.execute('''
            SELECT start_verse, end_verse 
            FROM memorization 
            WHERE surah_id = ?
        ''', (surah['id'],)).fetchall()
        
        # حساب الآيات المحفوظة الفريدة
        for memo in memorizations:
            for v in range(memo['start_verse'], memo['end_verse'] + 1):
                memorized_verses.add(v)
        
        # إضافة معلومات السورة للقائمة فقط إذا كانت مكتملة
        surah_data = {
            'id': surah['id'],
            'name': surah['name'],
            'total_verses': surah['verses'],
            'memorized_verses': len(memorized_verses),
            'percentage': (len(memorized_verses) / surah['verses']) * 100 if surah['verses'] > 0 else 0
        }
        surahs_data.append(surah_data)
    
    # حساب عدد السور المكتملة (100%)
    completed_surahs = sum(1 for s in surahs_data if s['percentage'] == 100)
    
    # Calculate total Quran verses and pages for percentage calculation
    total_quran_verses = conn.execute('SELECT SUM(verses) as total FROM surahs').fetchone()
    total_quran_verses = total_quran_verses['total'] if total_quran_verses['total'] else 6236  # Fallback to traditional count
    
    # Last page of the Quran
    last_page = conn.execute('SELECT MAX(end_page) as last_page FROM surahs').fetchone()
    total_quran_pages = last_page['last_page'] if last_page['last_page'] else 604  # Fallback to traditional count
    
    # Calculate percentages
    verse_percentage = (total_verses / total_quran_verses) * 100 if total_quran_verses > 0 else 0
    page_percentage = (total_pages / total_quran_pages) * 100 if total_quran_pages > 0 else 0
    
    # Recent memorizations
    recent_memorizations = conn.execute('''
        SELECT m.id, m.date, s.name as surah_name, m.start_verse, m.end_verse, m.start_page, m.end_page, 
               (m.end_page - m.start_page + 1) as pages, m.rating, m.reciter
        FROM memorization m
        JOIN surahs s ON m.surah_id = s.id
        ORDER BY m.date DESC
        LIMIT 5
    ''').fetchall()
    
    conn.close()
    
    return {
        'total_verses': total_verses,
        'total_pages': total_pages,
        'unique_surahs': completed_surahs,  # تم تغييرها لتعرض عدد السور المكتملة فقط
        'verse_percentage': round(verse_percentage, 2),
        'page_percentage': round(page_percentage, 2),
        'recent_memorizations': recent_memorizations
    }

def get_memorization_data_for_chart():
    conn = get_db_connection()
    
    # Get memorization data by juz
    juz_data = []
    all_juz = get_all_juz()
    
    for juz in all_juz:
        # Calculate total verses in this juz
        total_juz_verses = 0
        
        # Find all surahs in this juz
        if juz['start_surah'] == juz['end_surah']:
            # If juz is within a single surah
            total_juz_verses = juz['end_verse'] - juz['start_verse'] + 1
        else:
            # If juz spans multiple surahs
            # Get first surah's verses (from start_verse to end of surah)
            first_surah = get_surah_by_id(juz['start_surah'])
            total_juz_verses += first_surah['verses'] - juz['start_verse'] + 1
            
            # Get middle surahs' verses (all verses)
            for s_id in range(juz['start_surah'] + 1, juz['end_surah']):
                surah = get_surah_by_id(s_id)
                total_juz_verses += surah['verses']
            
            # Get last surah's verses (from start to end_verse)
            total_juz_verses += juz['end_verse']
        
        # Get memorized verses in this juz range
        memorized_verses = 0
        memorizations = conn.execute('''
            SELECT m.surah_id, m.start_verse, m.end_verse
            FROM memorization m
            WHERE m.surah_id >= ? AND m.surah_id <= ?
        ''', (juz['start_surah'], juz['end_surah'])).fetchall()
        
        for memo in memorizations:
            surah_id = memo['surah_id']
            start_verse = memo['start_verse']
            end_verse = memo['end_verse']
            
            # Check if memorization is within the juz
            if surah_id == juz['start_surah'] and surah_id == juz['end_surah']:
                # Both start and end surah are the same as the juz
                overlap_start = max(start_verse, juz['start_verse'])
                overlap_end = min(end_verse, juz['end_verse'])
                if overlap_start <= overlap_end:
                    memorized_verses += overlap_end - overlap_start + 1
                    
            elif surah_id == juz['start_surah']:
                # Only start surah matches
                if start_verse <= juz['start_verse']:
                    memorized_verses += end_verse - juz['start_verse'] + 1
                else:
                    memorized_verses += end_verse - start_verse + 1
                    
            elif surah_id == juz['end_surah']:
                # Only end surah matches
                if end_verse >= juz['end_verse']:
                    memorized_verses += juz['end_verse'] - start_verse + 1
                else:
                    memorized_verses += end_verse - start_verse + 1
                    
            elif juz['start_surah'] < surah_id < juz['end_surah']:
                # Surah is completely within the juz
                memorized_verses += end_verse - start_verse + 1
        
        percentage = (memorized_verses / total_juz_verses) * 100 if total_juz_verses > 0 else 0
        
        juz_data.append({
            'juz_number': juz['id'],
            'juz_name': juz['name'],
            'percentage': round(percentage, 2)
        })
    
    conn.close()
    return juz_data

# Routes
@app.route('/')
def dashboard():
    stats = get_memorization_stats()
    chart_data = get_memorization_data_for_chart()
    return render_template('dashboard.html', stats=stats, chart_data=json.dumps(chart_data))

@app.route('/add', methods=['GET', 'POST'])
def add_memorization():
    if request.method == 'POST':
        date = request.form.get('date')
        surah_id = request.form.get('surah_id')
        start_verse = request.form.get('start_verse')
        end_verse = request.form.get('end_verse')
        start_page = request.form.get('start_page')
        end_page = request.form.get('end_page')
        rating = request.form.get('rating')
        reciter = request.form.get('reciter')
        notes = request.form.get('notes')
        favorite = 1 if request.form.get('favorite') else 0
        
        # Validate data
        if not date or not surah_id or not start_verse or not end_verse or not start_page or not end_page or not rating:
            flash('جميع الحقول المطلوبة يجب ملؤها', 'error')
            return redirect(url_for('add_memorization'))
        
        try:
            surah_id = int(surah_id)
            start_verse = int(start_verse)
            end_verse = int(end_verse)
            start_page = int(start_page)
            end_page = int(end_page)
            
            # Calculate pages automatically
            pages = end_page - start_page + 1
            
            # Validate verse and page ranges
            surah = get_surah_by_id(surah_id)
            if not surah:
                flash('السورة غير موجودة', 'error')
                return redirect(url_for('add_memorization'))
                
            if start_verse < 1 or start_verse > surah['verses']:
                flash('رقم الآية الأولى غير صحيح', 'error')
                return redirect(url_for('add_memorization'))
                
            if end_verse < start_verse or end_verse > surah['verses']:
                flash('رقم الآية الأخيرة غير صحيح', 'error')
                return redirect(url_for('add_memorization'))
                
            if start_page < surah['start_page'] or start_page > surah['end_page']:
                flash('رقم الصفحة الأولى غير صحيح', 'error')
                return redirect(url_for('add_memorization'))
                
            if end_page < start_page or end_page > surah['end_page']:
                flash('رقم الصفحة الأخيرة غير صحيح', 'error')
                return redirect(url_for('add_memorization'))
            
            # Check for overlapping memorization ranges
            overlap = check_verse_overlap(surah_id, start_verse, end_verse)
            if overlap['overlap']:
                flash('هناك تداخل مع سجل حفظ موجود، يرجى تعديل النطاق', 'error')
                return redirect(url_for('add_memorization'))
            
            # Insert into database
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO memorization (date, surah_id, start_verse, end_verse, start_page, end_page, pages, rating, reciter, notes, favorite)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (date, surah_id, start_verse, end_verse, start_page, end_page, pages, rating, reciter, notes, favorite))
            conn.commit()
            conn.close()
            
            flash('تم إضافة الحفظ بنجاح', 'success')
            return redirect(url_for('memorization_log'))
            
        except ValueError:
            flash('قيم غير صالحة تم إدخالها', 'error')
            return redirect(url_for('add_memorization'))
    surahs = get_all_surahs()
    reciters = get_all_reciters()
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('add_memorization.html', surahs=surahs, reciters=reciters, today=today)

@app.route('/log')
def memorization_log():
    conn = get_db_connection()
    
    # الحصول على معلمات البحث والفلترة
    search_query = request.args.get('search', '')
    filter_surah = request.args.get('surah_id', '')
    filter_rating = request.args.get('rating', '')
    filter_favorites = request.args.get('favorites', '')
    
    # بناء استعلام SQL الأساسي
    query = '''
        SELECT m.id, m.date, s.name as surah_name, s.id as surah_id, m.start_verse, m.end_verse, 
               (m.end_verse - m.start_verse + 1) as verse_count, m.start_page, m.end_page, 
               (m.end_page - m.start_page + 1) as pages, m.rating, m.reciter, m.notes, m.favorite
        FROM memorization m
        JOIN surahs s ON m.surah_id = s.id
        WHERE 1=1
    '''
    params = []
    
    # إضافة شروط البحث إذا تم تقديمها
    if search_query:
        query += " AND (s.name LIKE ? OR m.notes LIKE ? OR m.reciter LIKE ?)"
        search_term = f"%{search_query}%"
        params.extend([search_term, search_term, search_term])
    
    if filter_surah:
        query += " AND m.surah_id = ?"
        params.append(filter_surah)
    
    if filter_rating:
        query += " AND m.rating = ?"
        params.append(filter_rating)
    
    if filter_favorites == '1':
        query += " AND m.favorite = 1"
    
    # إكمال الاستعلام مع الترتيب
    query += " ORDER BY m.date DESC"
    
    # تنفيذ الاستعلام
    memorizations = conn.execute(query, params).fetchall()
    
    # الحصول على جميع السور للفلترة
    surahs = conn.execute('SELECT id, name FROM surahs ORDER BY id').fetchall()
    
    conn.close()
    
    return render_template('memorization_log.html', 
                           memorizations=memorizations, 
                           surahs=surahs,
                           search_query=search_query,
                           filter_surah=filter_surah,
                           filter_rating=filter_rating,
                           filter_favorites=filter_favorites)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_memorization(id):
    conn = get_db_connection()
    memorization = conn.execute('SELECT * FROM memorization WHERE id = ?', (id,)).fetchone()
    
    if not memorization:
        flash('سجل الحفظ غير موجود', 'error')
        return redirect(url_for('memorization_log'))
    
    if request.method == 'POST':
        date = request.form.get('date')
        surah_id = request.form.get('surah_id')
        start_verse = request.form.get('start_verse')
        end_verse = request.form.get('end_verse')
        start_page = request.form.get('start_page')
        end_page = request.form.get('end_page')
        rating = request.form.get('rating')
        reciter = request.form.get('reciter')
        notes = request.form.get('notes')
        favorite = 1 if request.form.get('favorite') else 0
        
        # Validate data
        if not date or not surah_id or not start_verse or not end_verse or not start_page or not end_page or not rating:
            flash('جميع الحقول المطلوبة يجب ملؤها', 'error')
            return redirect(url_for('edit_memorization', id=id))
        
        try:
            surah_id = int(surah_id)
            start_verse = int(start_verse)
            end_verse = int(end_verse)
            start_page = int(start_page)
            end_page = int(end_page)
            
            # Calculate pages automatically
            pages = end_page - start_page + 1
            
            # Validate verse and page ranges
            surah = get_surah_by_id(surah_id)
            if not surah:
                flash('السورة غير موجودة', 'error')
                return redirect(url_for('edit_memorization', id=id))
                
            if start_verse < 1 or start_verse > surah['verses']:
                flash('رقم الآية الأولى غير صحيح', 'error')
                return redirect(url_for('edit_memorization', id=id))
                
            if end_verse < start_verse or end_verse > surah['verses']:
                flash('رقم الآية الأخيرة غير صحيح', 'error')
                return redirect(url_for('edit_memorization', id=id))
                
            if start_page < surah['start_page'] or start_page > surah['end_page']:
                flash('رقم الصفحة الأولى غير صحيح', 'error')
                return redirect(url_for('edit_memorization', id=id))
                
            if end_page < start_page or end_page > surah['end_page']:
                flash('رقم الصفحة الأخيرة غير صحيح', 'error')
                return redirect(url_for('edit_memorization', id=id))
            
            # Check for overlapping memorization ranges (excluding current record)
            overlap = check_verse_overlap(surah_id, start_verse, end_verse, id)
            if overlap['overlap']:
                flash('هناك تداخل مع سجل حفظ آخر، يرجى تعديل النطاق', 'error')
                return redirect(url_for('edit_memorization', id=id))
            
            # Update database
            conn.execute('''
                UPDATE memorization
                SET date = ?, surah_id = ?, start_verse = ?, end_verse = ?, start_page = ?, end_page = ?, 
                    pages = ?, rating = ?, reciter = ?, notes = ?, favorite = ?
                WHERE id = ?
            ''', (date, surah_id, start_verse, end_verse, start_page, end_page, pages, rating, reciter, notes, favorite, id))
            conn.commit()
            
            flash('تم تحديث الحفظ بنجاح', 'success')
            return redirect(url_for('memorization_log'))
            
        except ValueError:
            flash('قيم غير صالحة تم إدخالها', 'error')
            return redirect(url_for('edit_memorization', id=id))
    
    surahs = get_all_surahs()
    reciters = get_all_reciters()
    return render_template('edit_memorization.html', memorization=memorization, surahs=surahs, reciters=reciters)

@app.route('/toggle-favorite/<int:id>')
def toggle_favorite(id):
    """تبديل حالة المفضلة لسجل حفظ معين"""
    conn = get_db_connection()
    memo = conn.execute('SELECT favorite FROM memorization WHERE id = ?', (id,)).fetchone()
    
    if not memo:
        conn.close()
        return jsonify({'success': False, 'message': 'سجل الحفظ غير موجود'})
    
    # تبديل حالة المفضلة
    new_status = 0 if memo['favorite'] else 1
    conn.execute('UPDATE memorization SET favorite = ? WHERE id = ?', (new_status, id))
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True, 
        'favorite': new_status,
        'message': 'تمت إضافة الحفظ للمفضلة' if new_status else 'تمت إزالة الحفظ من المفضلة'
    })

@app.route('/delete/<int:id>')
def delete_memorization(id):
    conn = get_db_connection()
    memorization = conn.execute('SELECT * FROM memorization WHERE id = ?', (id,)).fetchone()
    
    if not memorization:
        flash('سجل الحفظ غير موجود', 'error')
    else:
        conn.execute('DELETE FROM memorization WHERE id = ?', (id,))
        conn.commit()
        flash('تم حذف سجل الحفظ بنجاح', 'success')
    
    conn.close()
    return redirect(url_for('memorization_log'))

@app.route('/surah-progress')
def surah_progress():
    conn = get_db_connection()
    
    # الحصول على معلمات الفلترة
    filter_query = request.args.get('search', '')
    filter_progress = request.args.get('progress', '')  # 'completed', 'in-progress', 'not-started'
    
    # الحصول على جميع السور
    surahs = conn.execute('SELECT * FROM surahs ORDER BY id').fetchall()
    
    # Get memorized verses for each surah
    surah_progress = []
    for surah in surahs:
        # Get all memorizations for this surah
        memorizations = conn.execute('''
            SELECT start_verse, end_verse 
            FROM memorization 
            WHERE surah_id = ?
            ORDER BY start_verse
        ''', (surah['id'],)).fetchall()
        
        # Count unique memorized verses
        memorized_verses = set()
        for memo in memorizations:
            for v in range(memo['start_verse'], memo['end_verse'] + 1):
                memorized_verses.add(v)
        
        # Calculate pages
        memorized_pages = 0
        for memo in conn.execute('SELECT pages FROM memorization WHERE surah_id = ?', (surah['id'],)).fetchall():
            if memo['pages']:
                memorized_pages += memo['pages']
        
        # Calculate percentage
        percentage = (len(memorized_verses) / surah['verses']) * 100 if surah['verses'] > 0 else 0
        percentage_rounded = round(percentage, 2)
        
        # تحديد حالة الحفظ
        if percentage_rounded == 100:
            status = 'completed'  # مكتمل
        elif percentage_rounded > 0:
            status = 'in-progress'  # جاري الحفظ
        else:
            status = 'not-started'  # لم يبدأ
        
        # إضافة معلومات السورة إلى القائمة
        surah_data = {
            'id': surah['id'],
            'name': surah['name'],
            'name_en': surah['name_en'],
            'total_verses': surah['verses'],
            'memorized_verses': len(memorized_verses),
            'memorized_pages': memorized_pages,
            'percentage': percentage_rounded,
            'status': status
        }
        surah_progress.append(surah_data)
    
    # تطبيق الفلترة
    filtered_progress = []
    for surah in surah_progress:
        # فلترة البحث النصي (اسم السورة)
        name_match = filter_query.lower() in surah['name'].lower() or filter_query.lower() in (surah['name_en'].lower() if surah['name_en'] else '')
        
        # فلترة حالة التقدم
        progress_match = True
        if filter_progress:
            progress_match = surah['status'] == filter_progress
        
        # إضافة السورة للنتائج إذا تطابقت مع جميع الفلاتر
        if name_match and progress_match:
            filtered_progress.append(surah)
    
    conn.close()
    
    # حساب إحصائيات للسور المفلترة
    total_verses = sum(surah['total_verses'] for surah in filtered_progress)
    memorized_verses = sum(surah['memorized_verses'] for surah in filtered_progress)
    overall_percentage = round((memorized_verses / total_verses * 100) if total_verses > 0 else 0, 2)
    
    return render_template('surah_progress.html', 
                           surahs=filtered_progress,
                           filter_query=filter_query,
                           filter_progress=filter_progress,
                           stats={
                               'completed': sum(1 for s in filtered_progress if s['status'] == 'completed'),
                               'in_progress': sum(1 for s in filtered_progress if s['status'] == 'in-progress'),
                               'not_started': sum(1 for s in filtered_progress if s['status'] == 'not-started'),
                               'total_verses': total_verses,
                               'memorized_verses': memorized_verses,
                               'overall_percentage': overall_percentage
                           })

@app.route('/juz-progress')
def juz_progress():
    conn = get_db_connection()
    all_juz = conn.execute('SELECT * FROM juz ORDER BY id').fetchall()
    
    juz_progress = []
    for juz in all_juz:
        # الخصائص الثابتة للجزء
        total_verses = 0
        memorized_verses = 0
        total_pages = juz['end_page'] - juz['start_page'] + 1
        memorized_pages = 0
        
        # حساب عدد الآيات الكلي في الجزء
        if juz['start_surah'] == juz['end_surah']:
            # الجزء ضمن سورة واحدة
            total_verses = juz['end_verse'] - juz['start_verse'] + 1
        else:
            # السورة الأولى
            first_surah = get_surah_by_id(juz['start_surah'])
            total_verses += first_surah['verses'] - juz['start_verse'] + 1
            
            # السور الوسطى
            for s_id in range(juz['start_surah'] + 1, juz['end_surah']):
                surah = get_surah_by_id(s_id)
                total_verses += surah['verses']
            
            # السورة الأخيرة
            total_verses += juz['end_verse']
        
        # الحصول على سجلات الحفظ التي قد تتداخل مع هذا الجزء
        # بناءً على نطاق الصفحات
        memorizations = conn.execute('''
            SELECT m.start_page, m.end_page, m.surah_id, m.start_verse, m.end_verse
            FROM memorization m
            WHERE NOT (m.end_page < ? OR m.start_page > ?)
        ''', (juz['start_page'], juz['end_page'])).fetchall()
        
        # حساب الصفحات المحفوظة
        pages_set = set()  # مجموعة لتتبع الصفحات المحفوظة دون تكرار
        
        for memo in memorizations:
            # حساب نطاق الصفحات المشترك مع هذا الجزء
            overlap_start_page = max(memo['start_page'], juz['start_page'])
            overlap_end_page = min(memo['end_page'], juz['end_page'])
            
            # إضافة الصفحات إلى المجموعة (لتجنب العد المتكرر)
            for page in range(overlap_start_page, overlap_end_page + 1):
                pages_set.add(page)
                
            # حساب الآيات المحفوظة: فقط إذا كانت السورة ضمن نطاق الجزء
            surah_id = memo['surah_id']
            
            if juz['start_surah'] <= surah_id <= juz['end_surah']:
                start_verse = memo['start_verse']
                end_verse = memo['end_verse']
                
                # حساب التداخل بناءً على موقع السورة
                if surah_id == juz['start_surah'] and surah_id == juz['end_surah']:
                    # السورة هي نفسها سورة البداية والنهاية للجزء
                    overlap_start = max(start_verse, juz['start_verse'])
                    overlap_end = min(end_verse, juz['end_verse'])
                    if overlap_start <= overlap_end:
                        memorized_verses += overlap_end - overlap_start + 1
                        
                elif surah_id == juz['start_surah']:
                    # السورة هي سورة البداية فقط
                    overlap_start = max(start_verse, juz['start_verse'])
                    if overlap_start <= end_verse:
                        memorized_verses += end_verse - overlap_start + 1
                        
                elif surah_id == juz['end_surah']:
                    # السورة هي سورة النهاية فقط
                    overlap_end = min(end_verse, juz['end_verse'])
                    if start_verse <= overlap_end:
                        memorized_verses += overlap_end - start_verse + 1
                        
                elif juz['start_surah'] < surah_id < juz['end_surah']:
                    # السورة بالكامل ضمن نطاق الجزء
                    memorized_verses += end_verse - start_verse + 1
        
        # تعيين عدد الصفحات المحفوظة
        memorized_pages = len(pages_set)
        
        # حساب النسب المئوية
        verse_percentage = (memorized_verses / total_verses) * 100 if total_verses > 0 else 0
        page_percentage = (memorized_pages / total_pages) * 100 if total_pages > 0 else 0
        
        # إضافة معلومات الجزء للقائمة
        juz_progress.append({
            'id': juz['id'],
            'name': juz['name'],
            'total_verses': total_verses,
            'memorized_verses': memorized_verses,
            'total_pages': total_pages,
            'memorized_pages': memorized_pages,
            'verse_percentage': round(verse_percentage, 2),
            'page_percentage': round(page_percentage, 2)
        })
    
    conn.close()
    return render_template('juz_progress.html', juz_data=juz_progress)

@app.route('/reciters')
def reciters():
    conn = get_db_connection()
    all_reciters = conn.execute('SELECT * FROM reciters ORDER BY name').fetchall()
    
    # Convert Row objects to dictionaries and add count
    reciters_list = []
    for reciter in all_reciters:
        # Convert sqlite3.Row to dict
        reciter_dict = dict(reciter)
        # Get count
        count = conn.execute('SELECT COUNT(*) as count FROM memorization WHERE reciter = ?', 
                           (reciter['name'],)).fetchone()
        reciter_dict['count'] = count['count'] if count else 0
        reciters_list.append(reciter_dict)
    
    conn.close()
    return render_template('reciters.html', reciters=reciters_list)

@app.route('/add-reciter', methods=['GET', 'POST'])
def add_reciter():
    if request.method == 'POST':
        name = request.form.get('name')
        info = request.form.get('info')
        
        if not name:
            flash('اسم القارئ مطلوب', 'error')
            return redirect(url_for('add_reciter'))
        
        # Check if reciter already exists
        conn = get_db_connection()
        existing = conn.execute('SELECT * FROM reciters WHERE name = ?', (name,)).fetchone()
        
        if existing:
            flash('هذا القارئ موجود بالفعل', 'error')
            conn.close()
            return redirect(url_for('add_reciter'))
        
        # Add new reciter
        conn.execute('INSERT INTO reciters (name, info) VALUES (?, ?)', (name, info))
        conn.commit()
        conn.close()
        
        flash('تمت إضافة القارئ بنجاح', 'success')
        return redirect(url_for('reciters'))
    
    return render_template('add_reciter.html')

@app.route('/edit-reciter/<int:id>', methods=['GET', 'POST'])
def edit_reciter(id):
    conn = get_db_connection()
    reciter = conn.execute('SELECT * FROM reciters WHERE id = ?', (id,)).fetchone()
    
    if not reciter:
        flash('القارئ غير موجود', 'error')
        return redirect(url_for('reciters'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        info = request.form.get('info')
        
        if not name:
            flash('اسم القارئ مطلوب', 'error')
            return redirect(url_for('edit_reciter', id=id))
        
        # Check if another reciter with same name exists
        existing = conn.execute('SELECT * FROM reciters WHERE name = ? AND id != ?', (name, id)).fetchone()
        
        if existing:
            flash('يوجد قارئ آخر بهذا الاسم', 'error')
            conn.close()
            return redirect(url_for('edit_reciter', id=id))
        
        # Update reciter
        conn.execute('UPDATE reciters SET name = ?, info = ? WHERE id = ?', (name, info, id))
        
        # Update all memorization records that use this reciter's old name
        conn.execute('UPDATE memorization SET reciter = ? WHERE reciter = ?', (name, reciter['name']))
        
        conn.commit()
        conn.close()
        
        flash('تم تحديث القارئ بنجاح', 'success')
        return redirect(url_for('reciters'))
    
    conn.close()
    return render_template('edit_reciter.html', reciter=reciter)

@app.route('/delete-reciter/<int:id>')
def delete_reciter(id):
    conn = get_db_connection()
    reciter = conn.execute('SELECT * FROM reciters WHERE id = ?', (id,)).fetchone()
    
    if not reciter:
        flash('القارئ غير موجود', 'error')
    else:
        # Check if reciter is used in any memorization records
        count = conn.execute('SELECT COUNT(*) as count FROM memorization WHERE reciter = ?', 
                            (reciter['name'],)).fetchone()['count']
        
        if count > 0:
            flash(f'لا يمكن حذف هذا القارئ لأنه مستخدم في {count} سجلات حفظ', 'error')
        else:
            conn.execute('DELETE FROM reciters WHERE id = ?', (id,))
            conn.commit()
            flash('تم حذف القارئ بنجاح', 'success')
    
    conn.close()
    return redirect(url_for('reciters'))

@app.route('/reciter-stats/<int:id>')
def reciter_stats(id):
    conn = get_db_connection()
    reciter = conn.execute('SELECT * FROM reciters WHERE id = ?', (id,)).fetchone()
    
    if not reciter:
        flash('القارئ غير موجود', 'error')
        conn.close()
        return redirect(url_for('reciters'))
    
    # Get all memorizations for this reciter
    memorizations = conn.execute('''
        SELECT m.id, m.date, s.name as surah_name, m.start_verse, m.end_verse, 
               (m.end_verse - m.start_verse + 1) as verse_count, m.pages, m.rating
        FROM memorization m
        JOIN surahs s ON m.surah_id = s.id
        WHERE m.reciter = ?
        ORDER BY m.date DESC
    ''', (reciter['name'],)).fetchall()
    
    # Calculate statistics
    total_verses = conn.execute('''
        SELECT SUM(end_verse - start_verse + 1) as total
        FROM memorization 
        WHERE reciter = ?
    ''', (reciter['name'],)).fetchone()['total'] or 0
    
    total_pages = conn.execute('''
        SELECT SUM(pages) as total
        FROM memorization 
        WHERE reciter = ?
    ''', (reciter['name'],)).fetchone()['total'] or 0
    
    # Get surah distribution
    surah_distribution = conn.execute('''
        SELECT s.name, COUNT(*) as count, SUM(m.end_verse - m.start_verse + 1) as verses
        FROM memorization m
        JOIN surahs s ON m.surah_id = s.id
        WHERE m.reciter = ?
        GROUP BY s.name
        ORDER BY count DESC
    ''', (reciter['name'],)).fetchall()
    
    conn.close()
    
    return render_template('reciter_stats.html', 
                           reciter=reciter, 
                           memorizations=memorizations,
                           total_verses=total_verses,
                           total_pages=total_pages,
                           surah_distribution=surah_distribution)

@app.route('/export-database')
def export_database():
    """تصدير ملف قاعدة البيانات مباشرة"""
    try:
        # إنشاء نسخة من ملف قاعدة البيانات في الذاكرة
        db_path = os.path.abspath('database.db')
        
        # التأكد من إغلاق أي اتصالات مفتوحة مع قاعدة البيانات
        # (هذا يساعد في تجنب مشاكل القفل على الملف)
        
        # إرجاع الملف للتنزيل مباشرة
        return send_file(
            db_path,
            mimetype='application/x-sqlite3',
            as_attachment=True,
            download_name='quran_memorization_database_{}.db'.format(datetime.now().strftime('%Y-%m-%d'))
        )
        
    except Exception as e:
        flash('حدث خطأ أثناء تصدير قاعدة البيانات: {}'.format(str(e)), 'error')
        return redirect(url_for('dashboard'))

@app.route('/import-database', methods=['GET', 'POST'])
def import_database():
    """استيراد ملف قاعدة البيانات مباشرة"""
    if request.method == 'POST':
        # التحقق من وجود ملف
        if 'database_file' not in request.files:
            flash('لم يتم تحديد ملف', 'error')
            return redirect(request.url)
        
        file = request.files['database_file']
        
        # التحقق من اختيار ملف
        if file.filename == '':
            flash('لم يتم اختيار ملف', 'error')
            return redirect(request.url)
        
        if file and file.filename.endswith('.db'):
            try:
                # إغلاق الاتصال الحالي بقاعدة البيانات
                # لكي نتمكن من استبدال الملف
                db_path = os.path.abspath('database.db')
                
                # إنشاء نسخة احتياطية من قاعدة البيانات الحالية
                backup_path = os.path.abspath('database.db.bak')
                if os.path.exists(db_path):
                    shutil.copy2(db_path, backup_path)
                
                # حفظ الملف المستورد واستبداله بقاعدة البيانات الحالية
                file.save(db_path)
                
                flash('تم استيراد قاعدة البيانات بنجاح', 'success')
                return redirect(url_for('dashboard'))
                
            except Exception as e:
                # استعادة النسخة الاحتياطية إذا حدث خطأ
                if os.path.exists(backup_path):
                    shutil.copy2(backup_path, db_path)
                
                flash('حدث خطأ أثناء استيراد قاعدة البيانات: {}'.format(str(e)), 'error')
                return redirect(request.url)
        else:
            flash('الرجاء تحميل ملف .db صالح', 'error')
            return redirect(request.url)
            
    return render_template('import_database.html')

@app.route('/database-management')
def database_management():
    """صفحة إدارة قاعدة البيانات للنسخ الاحتياطي والاستعادة"""
    return render_template('database_management.html')

@app.route('/get-surah-verses/<int:surah_id>')
def get_surah_verses(surah_id):
    surah = get_surah_by_id(surah_id)
    if surah:
        return jsonify({
            'surah_id': surah['id'],
            'name': surah['name'],
            'verses': surah['verses']
        })
    return jsonify({'error': 'Surah not found'}), 404

def check_verse_overlap(surah_id, start_verse, end_verse, exclude_id=None):
    """التحقق من تداخل نطاق آيات الحفظ مع سجلات موجودة"""
    conn = get_db_connection()
    
    query = '''
        SELECT id, start_verse, end_verse
        FROM memorization 
        WHERE surah_id = ?
    '''
    params = [surah_id]
    
    # استبعاد السجل الحالي في حالة التحرير
    if exclude_id:
        query += ' AND id != ?'
        params.append(exclude_id)
    
    memorizations = conn.execute(query, params).fetchall()
    conn.close()
    
    # التحقق من وجود تداخل
    for memo in memorizations:
        # حالات التداخل المختلفة
        if (start_verse <= memo['start_verse'] and end_verse >= memo['start_verse']) or \
           (start_verse >= memo['start_verse'] and start_verse <= memo['end_verse']) or \
           (start_verse <= memo['start_verse'] and end_verse >= memo['end_verse']):
            return {
                'overlap': True,
                'memorization_id': memo['id'],
                'start_verse': memo['start_verse'],
                'end_verse': memo['end_verse']
            }
    
    return {'overlap': False}

@app.route('/check-overlap')
def check_overlap():
    """API للتحقق من تداخل نطاق الحفظ"""
    surah_id = request.args.get('surah_id', type=int)
    start_verse = request.args.get('start_verse', type=int)
    end_verse = request.args.get('end_verse', type=int)
    exclude_id = request.args.get('exclude_id', type=int)  # معرف السجل للاستبعاد (عند التعديل)
    
    if not surah_id or not start_verse or not end_verse:
        return jsonify({'error': 'Missing parameters'}), 400
    
    overlap = check_verse_overlap(surah_id, start_verse, end_verse, exclude_id)
    
    if overlap['overlap']:
        # إضافة معلومات السورة للاستجابة
        surah = get_surah_by_id(surah_id)
        overlap['surah_name'] = surah['name'] if surah else 'غير معروف'
        
    return jsonify(overlap)

if __name__ == '__main__':
    # Check if database exists, if not initialize it
    if not os.path.exists('database.db'):
        os.system('python init_db.py')
    
    app.run(debug=True)