from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import json
from datetime import datetime
import os

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
    total_pages = conn.execute('SELECT SUM(pages) as total FROM memorization').fetchone()
    total_pages = total_pages['total'] if total_pages['total'] else 0
    
    # Count of unique surahs with memorization
    unique_surahs = conn.execute('SELECT COUNT(DISTINCT surah_id) as count FROM memorization').fetchone()
    unique_surahs = unique_surahs['count'] if unique_surahs['count'] else 0
    
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
        SELECT m.id, m.date, s.name as surah_name, m.start_verse, m.end_verse, m.pages, m.rating
        FROM memorization m
        JOIN surahs s ON m.surah_id = s.id
        ORDER BY m.date DESC
        LIMIT 5
    ''').fetchall()
    
    conn.close()
    
    return {
        'total_verses': total_verses,
        'total_pages': total_pages,
        'unique_surahs': unique_surahs,
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
        pages = request.form.get('pages')
        rating = request.form.get('rating')
        notes = request.form.get('notes')
        
        # Validate data
        if not date or not surah_id or not start_verse or not end_verse or not rating:
            flash('جميع الحقول المطلوبة يجب ملؤها', 'error')
            return redirect(url_for('add_memorization'))
        
        try:
            surah_id = int(surah_id)
            start_verse = int(start_verse)
            end_verse = int(end_verse)
            pages = int(pages) if pages else None
            
            # Validate verse range
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
            
            # Insert into database
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO memorization (date, surah_id, start_verse, end_verse, pages, rating, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (date, surah_id, start_verse, end_verse, pages, rating, notes))
            conn.commit()
            conn.close()
            
            flash('تم إضافة الحفظ بنجاح', 'success')
            return redirect(url_for('memorization_log'))
            
        except ValueError:
            flash('قيم غير صالحة تم إدخالها', 'error')
            return redirect(url_for('add_memorization'))
    
    # GET request
    surahs = get_all_surahs()
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('add_memorization.html', surahs=surahs, today=today)

@app.route('/log')
def memorization_log():
    conn = get_db_connection()
    memorizations = conn.execute('''
        SELECT m.id, m.date, s.name as surah_name, s.id as surah_id, m.start_verse, m.end_verse, 
               (m.end_verse - m.start_verse + 1) as verse_count, m.pages, m.rating, m.notes
        FROM memorization m
        JOIN surahs s ON m.surah_id = s.id
        ORDER BY m.date DESC
    ''').fetchall()
    conn.close()
    
    return render_template('memorization_log.html', memorizations=memorizations)

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
        pages = request.form.get('pages')
        rating = request.form.get('rating')
        notes = request.form.get('notes')
        
        # Validate data
        if not date or not surah_id or not start_verse or not end_verse or not rating:
            flash('جميع الحقول المطلوبة يجب ملؤها', 'error')
            return redirect(url_for('edit_memorization', id=id))
        
        try:
            surah_id = int(surah_id)
            start_verse = int(start_verse)
            end_verse = int(end_verse)
            pages = int(pages) if pages else None
            
            # Validate verse range
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
            
            # Update database
            conn.execute('''
                UPDATE memorization
                SET date = ?, surah_id = ?, start_verse = ?, end_verse = ?, pages = ?, rating = ?, notes = ?
                WHERE id = ?
            ''', (date, surah_id, start_verse, end_verse, pages, rating, notes, id))
            conn.commit()
            
            flash('تم تحديث الحفظ بنجاح', 'success')
            return redirect(url_for('memorization_log'))
            
        except ValueError:
            flash('قيم غير صالحة تم إدخالها', 'error')
            return redirect(url_for('edit_memorization', id=id))
    
    # GET request
    surahs = get_all_surahs()
    return render_template('edit_memorization.html', memorization=memorization, surahs=surahs)

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
        
        surah_progress.append({
            'id': surah['id'],
            'name': surah['name'],
            'name_en': surah['name_en'],
            'total_verses': surah['verses'],
            'memorized_verses': len(memorized_verses),
            'memorized_pages': memorized_pages,
            'percentage': round(percentage, 2)
        })
    
    conn.close()
    return render_template('surah_progress.html', surahs=surah_progress)

@app.route('/juz-progress')
def juz_progress():
    conn = get_db_connection()
    all_juz = conn.execute('SELECT * FROM juz ORDER BY id').fetchall()
    
    juz_progress = []
    for juz in all_juz:
        # Get memorized verses in this juz range
        total_verses = 0
        memorized_verses = 0
        total_pages = juz['end_page'] - juz['start_page'] + 1
        memorized_pages = 0
        
        # Calculate total verses in this juz range
        if juz['start_surah'] == juz['end_surah']:
            # Juz within a single surah
            total_verses = juz['end_verse'] - juz['start_verse'] + 1
        else:
            # First surah
            first_surah = get_surah_by_id(juz['start_surah'])
            total_verses += first_surah['verses'] - juz['start_verse'] + 1
            
            # Middle surahs
            for s_id in range(juz['start_surah'] + 1, juz['end_surah']):
                surah = get_surah_by_id(s_id)
                total_verses += surah['verses']
            
            # Last surah
            total_verses += juz['end_verse']
        
        # Get all memorizations that might overlap with this juz
        memorizations = conn.execute('''
            SELECT m.surah_id, m.start_verse, m.end_verse, m.pages
            FROM memorization m
            WHERE m.surah_id >= ? AND m.surah_id <= ?
        ''', (juz['start_surah'], juz['end_surah'])).fetchall()
        
        # Count memorized verses and pages
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
                overlap_start = max(start_verse, juz['start_verse'])
                overlap_end = end_verse
                if overlap_start <= overlap_end:
                    memorized_verses += overlap_end - overlap_start + 1
                    
            elif surah_id == juz['end_surah']:
                # Only end surah matches
                overlap_start = start_verse
                overlap_end = min(end_verse, juz['end_verse'])
                if overlap_start <= overlap_end:
                    memorized_verses += overlap_end - overlap_start + 1
                    
            elif juz['start_surah'] < surah_id < juz['end_surah']:
                # Surah is completely within the juz
                memorized_verses += end_verse - start_verse + 1
            
            # Count pages (simplified approach)
            if memo['pages']:
                surah = get_surah_by_id(surah_id)
                if juz['start_page'] <= surah['end_page'] and juz['end_page'] >= surah['start_page']:
                    # Add pages proportionally
                    memorized_pages += memo['pages']
        
        # Calculate percentages
        verse_percentage = (memorized_verses / total_verses) * 100 if total_verses > 0 else 0
        page_percentage = (memorized_pages / total_pages) * 100 if total_pages > 0 else 0
        
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

if __name__ == '__main__':
    # Check if database exists, if not initialize it
    if not os.path.exists('database.db'):
        os.system('python init_db.py')
    
    app.run(debug=True)