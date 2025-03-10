from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from typing import Dict, Any, Union
import os
import base64
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'gizli_anahtar'

# Dosya yükleme ayarları
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Güvenlik sorusu sabiti
GUVENLIK_SORUSU = "Kütüphanemizin kuruluş yılı kaçtır?"

def veritabani_baglantisi() -> sqlite3.Connection:
    """Veritabanı bağlantısını oluşturur ve döndürür."""
    conn = sqlite3.connect('kutuphane.db')
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    """Dosya uzantısının izin verilenler arasında olup olmadığını kontrol eder."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def kullanici_giris():
    """Kullanıcı giriş sayfası ve giriş işlemleri."""
    if request.method == 'POST':
        tc: str = request.form.get('tc')
        sifre: str = request.form.get('sifre')
        rol: str = request.form.get('rol')
        
        if not tc or not sifre or not rol:
            flash('Lütfen tüm alanları doldurun!')
            return render_template('kullanici_giris.html')

        conn = veritabani_baglantisi()
        cur = conn.cursor()
        
        try:
            if rol == 'personel':
                cur.execute('SELECT * FROM personel WHERE tc = ? AND sifre = ?', (tc, sifre))
                kullanici = cur.fetchone()
                if kullanici:
                    session['tc'] = tc
                    session['rol'] = 'personel'
                    session['ad_soyad'] = f"{kullanici['ad']} {kullanici['soyad']}"
                    return redirect(url_for('kutuphane_personel'))
                flash('Geçersiz yönetici bilgileri!')
            elif rol == 'kullanici':
                cur.execute('SELECT * FROM kullanicilar WHERE tc = ? AND sifre = ?', (tc, sifre))
                kullanici = cur.fetchone()
                if kullanici:
                    session['tc'] = tc
                    session['rol'] = 'kullanici'
                    session['ad_soyad'] = f"{kullanici['ad']} {kullanici['soyad']}"
                    return redirect(url_for('kutuphane_kullanici'))
                flash('Geçersiz kullanıcı bilgileri!')
        except Exception as e:
            flash(f'Hata: {str(e)}')
        finally:
            conn.close()
    
    return render_template('kullanici_giris.html')

@app.route('/kullanici_kayit', methods=['GET', 'POST'])
def kullanici_kayit():
    """Kullanıcı kayıt sayfası ve kayıt işlemleri."""
    if request.method == 'POST':
        tc: str = request.form['tc']
        sifre: str = request.form['sifre']
        sifre_tekrar: str = request.form['sifre_tekrar']
        ad: str = request.form['ad']
        soyad: str = request.form['soyad']

        # Fotoğraf yükleme kontrolü
        foto = request.files.get('foto')
        foto_data = None

        if foto and allowed_file(foto.filename):
            foto_data = base64.b64encode(foto.read()).decode('utf-8')

        if sifre != sifre_tekrar:
            flash('Şifreler eşleşmiyor!')
            return render_template('kullanici_kayit.html')

        conn = veritabani_baglantisi()
        cur = conn.cursor()
        
        try:
            cur.execute(""" 
                INSERT INTO kullanicilar (tc, sifre, ad, soyad, foto) 
                VALUES (?, ?, ?, ?, ?)
            """, (tc, sifre, ad, soyad, foto_data))
            conn.commit()
            flash('Kayıt başarılı! Giriş yapabilirsiniz.')
            return redirect(url_for('kullanici_giris'))
        except sqlite3.IntegrityError:
            flash('Bu TC kimlik numarası zaten kayıtlı!')
        finally:
            conn.close()

    return render_template('kullanici_kayit.html')

@app.route('/personel_giris', methods=['GET', 'POST'])
def personel_giris():
    """Yönetici giriş sayfası ve giriş işlemleri."""
    if request.method == 'POST':
        tc: str = request.form['tc']
        sifre: str = request.form['sifre']
        
        conn = veritabani_baglantisi()
        cur = conn.cursor()
        
        cur.execute('SELECT * FROM personel WHERE tc = ? AND sifre = ?', (tc, sifre))
        kullanici = cur.fetchone()
        
        if kullanici:
            session['tc'] = tc
            session['rol'] = 'personel'
            session['ad_soyad'] = f"{kullanici['ad']} {kullanici['soyad']}"
            conn.close()
            return redirect(url_for('kutuphane_personel'))
        
        flash('Geçersiz yönetici bilgileri!')
        conn.close()
    
    return render_template('personel_giris.html')

@app.route('/personel_kayit', methods=['GET', 'POST'])
def personel_kayit():
    """Yönetici kayıt sayfası ve kayıt işlemleri."""
    if request.method == 'POST':
        tc: str = request.form['tc']
        sifre: str = request.form['sifre']
        sifre_tekrar: str = request.form['sifre_tekrar']
        ad: str = request.form['ad']
        soyad: str = request.form['soyad']
        guvenlik_cevap: str = request.form['guvenlik_cevap']

        if sifre != sifre_tekrar:
            flash('Şifreler eşleşmiyor!')
            return render_template('personel_kayit.html', guvenlik_sorusu=GUVENLIK_SORUSU)

        if guvenlik_cevap != "2024":
            flash('Güvenlik sorusu cevabı yanlış!')
            return render_template('personel_kayit.html', guvenlik_sorusu=GUVENLIK_SORUSU)

        conn = veritabani_baglantisi()
        cur = conn.cursor()
        
        try:
            cur.execute(""" 
                INSERT INTO personel (tc, sifre, ad, soyad, guvenlik_cevap, foto) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (tc, sifre, ad, soyad, guvenlik_cevap, None))
            conn.commit()
            flash('Yönetici kaydı başarılı! Giriş yapabilirsiniz.')
            return redirect(url_for('personel_giris'))
        except sqlite3.IntegrityError:
            flash('Bu TC kimlik numarası zaten kayıtlı!')
        finally:
            conn.close()

    return render_template('personel_kayit.html', guvenlik_sorusu=GUVENLIK_SORUSU)

@app.route('/kutuphane_personel', methods=['GET'])
def kutuphane_personel():
    """Personel kütüphane ana sayfası ve kitap işlemleri."""
    if 'tc' not in session or session.get('rol') != 'personel':
        return redirect(url_for('personel_giris'))

    conn = veritabani_baglantisi()
    cur = conn.cursor()

    sayfa = request.args.get('sayfa', 1, type=int)
    sayfa_basi = 10

    # Mevcut kitaplar
    cur.execute('SELECT COUNT(*) as toplam FROM kitaplar')
    toplam_kitap = cur.fetchone()['toplam']
    toplam_sayfa = (toplam_kitap + sayfa_basi - 1) // sayfa_basi

    offset = (sayfa - 1) * sayfa_basi
    cur.execute('SELECT * FROM kitaplar LIMIT ? OFFSET ?', (sayfa_basi, offset))
    kitaplar = cur.fetchall()

    conn.close()
    return render_template('kutuphane_personel.html', 
                         kitaplar=kitaplar,
                         sayfa=sayfa,
                         toplam_sayfa=toplam_sayfa)

@app.route('/kutuphane_kullanici', methods=['GET'])
def kutuphane_kullanici():
    """Kullanıcı kütüphane sayfası ve kitap işlemleri."""
    if 'tc' not in session or session.get('rol') != 'kullanici':
        flash('Bu sayfaya erişim yetkiniz yok!')
        return redirect(url_for('kullanici_giris')) 

    conn = veritabani_baglantisi()
    cur = conn.cursor()

    # Arama parametrelerini al
    sayfa = request.args.get('sayfa', 1, type=int)
    kitap_adi = request.args.get('kitap_adi', '')
    yazar = request.args.get('yazar', '')
    min_sayfa = request.args.get('min_sayfa', type=int)
    max_sayfa = request.args.get('max_sayfa', type=int)
    kategori = request.args.get('kategori', '')

    sayfa_basi = 10

    # Kitaplar için sorgu oluştur
    query = ''' 
        SELECT k.id, k.kitap_adi, k.yazar, k.sayfa_sayisi, k.kategori, k.stok,
               (SELECT COUNT(*) FROM odunc 
                WHERE kitap_id = k.id AND tc = ? AND durum = 'alindi') as alinmis 
        FROM kitaplar k 
        WHERE 1=1
    '''
    params = [session['tc']]

    if kitap_adi:
        query += " AND k.kitap_adi LIKE ?"
        params.append(f"%{kitap_adi}%")
    if yazar:
        query += " AND k.yazar LIKE ?"
        params.append(f"%{yazar}%")
    if min_sayfa is not None:
        query += " AND k.sayfa_sayisi >= ?"
        params.append(min_sayfa)
    if max_sayfa is not None:
        query += " AND k.sayfa_sayisi <= ?"
        params.append(max_sayfa)
    if kategori:
        query += " AND k.kategori = ?"
        params.append(kategori)

    # Tüm kitapları çek
    cur.execute(query, params)
    tum_kitaplar = cur.fetchall()

    # Sayfalama
    toplam_kitap = len(tum_kitaplar)
    toplam_sayfa = (toplam_kitap + sayfa_basi - 1) // sayfa_basi
    kitaplar = tum_kitaplar[(sayfa - 1) * sayfa_basi : sayfa * sayfa_basi]

    # Ödünç alınan kitaplar
    cur.execute(''' 
        SELECT k.kitap_adi, k.yazar, o.odunc_zamani 
        FROM odunc o 
        JOIN kitaplar k ON o.kitap_id = k.id 
        WHERE o.tc = ? AND o.durum = 'alindi'
    ''', (session['tc'],))
    odunc_kitaplar = cur.fetchall()

    # Kullanıcının fotoğrafını al
    cur.execute('SELECT foto FROM kullanicilar WHERE tc = ?', (session['tc'],))
    foto_sonuc = cur.fetchone()
    foto = foto_sonuc['foto'] if foto_sonuc else None

    # Kategorileri al
    cur.execute("SELECT DISTINCT kategori FROM kitaplar WHERE kategori IS NOT NULL")
    kategoriler = [row['kategori'] for row in cur.fetchall()]

    conn.close()
    
    return render_template('kutuphane_kullanici.html', 
                           kitaplar=kitaplar, 
                           odunc_kitaplar=odunc_kitaplar,
                           sayfa=sayfa, 
                           toplam_sayfa=toplam_sayfa,
                           foto=foto,
                           kategoriler=kategoriler)

@app.route('/kitap_ekle_guncelle', methods=['POST'])
def kitap_ekle_guncelle():
    """Kitap ekleme ve güncelleme işlemleri."""
    if 'tc' not in session or session.get('rol') != 'personel':
        return redirect(url_for('personel_giris'))
    
    kitap_id = request.form.get('kitap_id')
    kitap_adi = request.form.get('kitap_adi', '').strip()
    yazar = request.form.get('yazar', '').strip()
    sayfa_sayisi = request.form.get('sayfa_sayisi')
    kategori = request.form.get('kategori', '').strip()
    stok = request.form.get('stok')
    
    conn = veritabani_baglantisi()
    cur = conn.cursor()
    
    if kitap_id:  # Güncelleme işlemi
        cur.execute('SELECT * FROM kitaplar WHERE id = ?', (kitap_id,))
        kitap = cur.fetchone()
        if not kitap:
            flash('Bu ID ile bir kitap bulunamadı!')
            conn.close()
            return redirect(url_for('kutuphane_personel'))

        update_query = 'UPDATE kitaplar SET '
        params = []
        updates = []

        if kitap_adi:
            updates.append('kitap_adi = ?')
            params.append(kitap_adi)
        if yazar:
            updates.append('yazar = ?')
            params.append(yazar)
        if sayfa_sayisi:
            updates.append('sayfa_sayisi = ?')
            params.append(sayfa_sayisi)
        if kategori:
            updates.append('kategori = ?')
            params.append(kategori)
        if stok:
            updates.append('stok = ?')
            params.append(stok)

        if not updates:
            flash('Güncellemek için en az bir alan doldurun!')
            conn.close()
            return redirect(url_for('kutuphane_personel'))

        update_query += ', '.join(updates) + ' WHERE id = ?'
        params.append(kitap_id)

        cur.execute(update_query, params)
        conn.commit()
        flash('Kitap başarıyla güncellendi!')
    else:  # Yeni kitap ekleme
        if not (kitap_adi and yazar and sayfa_sayisi and kategori and stok):
            flash('Yeni kitap eklemek için tüm alanları doldurun!')
            conn.close()
            return redirect(url_for('kutuphane_personel'))

        cur.execute(''' 
            INSERT INTO kitaplar (kitap_adi, yazar, sayfa_sayisi, kategori, stok)
            VALUES (?, ?, ?, ?, ?)
        ''', (kitap_adi, yazar, sayfa_sayisi, kategori, stok))
        conn.commit()
        flash('Kitap başarıyla eklendi!')
    
    conn.close()
    return redirect(url_for('kutuphane_personel'))

@app.route('/kitap_guncelle_form', methods=['POST'])
def kitap_guncelle_form():
    """Kitap güncelleme formunu doldurmak için yönlendirme."""
    if 'tc' not in session or session.get('rol') != 'personel':
        return redirect(url_for('personel_giris'))
    
    kitap_id = request.form['kitap_id']
    conn = veritabani_baglantisi()
    cur = conn.cursor()
    
    cur.execute('SELECT * FROM kitaplar WHERE id = ?', (kitap_id,))
    kitap = cur.fetchone()
    conn.close()
    
    flash('Kitap ID alanına ID\'yi girerek güncelleyin.')
    return redirect(url_for('kutuphane_personel'))

@app.route('/kitap_sil', methods=['POST'])
def kitap_sil():
    """Kitap silme işlemi ve ID'lerin yeniden numaralandırılması."""
    if 'tc' not in session or session.get('rol') != 'personel':
        return redirect(url_for('personel_giris'))
    
    kitap_id = request.form['kitap_id']
    
    conn = veritabani_baglantisi()
    cur = conn.cursor()
    
    cur.execute('SELECT COUNT(*) FROM odunc WHERE kitap_id = ? AND durum = ?', (kitap_id, 'alindi'))
    odunc_sayisi = cur.fetchone()[0]
    
    if odunc_sayisi > 0:
        flash('Bu kitap şu anda ödünç alınmış, silinemez!')
        conn.close()
        return redirect(url_for('kutuphane_personel'))
    
    try:
        cur.execute('DELETE FROM kitaplar WHERE id = ?', (kitap_id,))
        
        cur.execute(''' 
            CREATE TABLE temp_kitaplar AS 
            SELECT * FROM kitaplar ORDER BY id
        ''')
        
        cur.execute('DELETE FROM kitaplar')
        
        cur.execute('SELECT * FROM temp_kitaplar')
        kalan_kitaplar = cur.fetchall()
        for i, kitap in enumerate(kalan_kitaplar, start=1):
            cur.execute(''' 
                INSERT INTO kitaplar (id, kitap_adi, yazar, sayfa_sayisi, kategori, stok)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (i, kitap['kitap_adi'], kitap['yazar'], kitap['sayfa_sayisi'], kitap['kategori'], kitap['stok']))
        
        cur.execute('DROP TABLE temp_kitaplar')
        
        cur.execute(''' 
            UPDATE odunc 
            SET kitap_id = (
                SELECT ROW_NUMBER() OVER (ORDER BY k.id) 
                FROM kitaplar k 
                WHERE k.kitap_adi = (
                    SELECT kitap_adi 
                    FROM kitaplar 
                    WHERE id = odunc.kitap_id
                ) LIMIT 1
            )
            WHERE kitap_id > ?
        ''', (kitap_id,))
        
        conn.commit()
        flash('Kitap başarıyla silindi ve ID\'ler yeniden düzenlendi!')
    except Exception as e:
        conn.rollback()
        flash(f'Hata oluştu: {str(e)}')
    
    conn.close()
    return redirect(url_for('kutuphane_personel'))

@app.route('/kitap_odunc_ver', methods=['POST'])
def kitap_odunc_ver():
    """Kitap ödünç verme işlemi."""
    if 'tc' not in session or session.get('rol') != 'personel':
        return redirect(url_for('personel_giris'))
    
    kitap_id = request.form['kitap_id']
    kullanici_tc = request.form['kullanici_tc']
    odunc_zamani = request.form.get('odunc_zamani', 'CURRENT_TIMESTAMP')
    iade_zamani = request.form.get('iade_zamani', None)
    
    conn = veritabani_baglantisi()
    cur = conn.cursor()
    
    cur.execute('SELECT stok FROM kitaplar WHERE id = ?', (kitap_id,))
    stok = cur.fetchone()['stok']
    
    if stok > 0:
        cur.execute(''' 
            INSERT INTO odunc (tc, kitap_id, odunc_zamani, iade_zamani, durum) 
            VALUES (?, ?, ?, ?, 'alindi')
        ''', (kullanici_tc, kitap_id, odunc_zamani, iade_zamani))
        cur.execute('UPDATE kitaplar SET stok = stok - 1 WHERE id = ?', (kitap_id,))
        conn.commit()
        flash('Kitap başarıyla ödünç verildi!')
    else:
        flash('Bu kitap stokta yok!')
    
    conn.close()
    return redirect(url_for('kutuphane_personel'))

@app.route('/kitap_iade_et', methods=['POST'])
def kitap_iade_et():
    """Kitap iade etme işlemi."""
    if 'tc' not in session or session.get('rol') != 'personel':
        flash('Bu işlemi gerçekleştirmek için personel olarak giriş yapmalısınız!')
        return redirect(url_for('personel_giris'))
    
    kitap_id = request.form.get('kitap_id')
    kullanici_tc = request.form.get('tc')
    
    if not kitap_id or not kullanici_tc:
        flash('Kitap ID ve TC kimlik numarası gereklidir!')
        return redirect(request.referrer or url_for('kullanici_yonetim'))
    
    conn = veritabani_baglantisi()
    cur = conn.cursor()
    
    try:
        cur.execute(''' 
            SELECT COUNT(*) 
            FROM odunc 
            WHERE kitap_id = ? AND tc = ? AND durum = 'alindi'
        ''', (kitap_id, kullanici_tc))
        odunc_var_mi = cur.fetchone()[0]
        
        if odunc_var_mi == 0:
            flash('Bu kitap bu kullanıcı tarafından ödünç alınmamış!')
            conn.close()
            return redirect(request.referrer or url_for('kullanici_yonetim'))
        
        cur.execute(''' 
            UPDATE odunc 
            SET durum = 'iade', iade_zamani = CURRENT_TIMESTAMP 
            WHERE kitap_id = ? AND tc = ? AND durum = 'alindi'
        ''', (kitap_id, kullanici_tc))
        
        cur.execute('UPDATE kitaplar SET stok = stok + 1 WHERE id = ?', (kitap_id,))
        
        conn.commit()
        flash('Kitap başarıyla iade edildi!')
    
    except Exception as e:
        conn.rollback()
        flash(f'İade işlemi sırasında hata oluştu: {str(e)}')
    
    finally:
        conn.close()
    
    return redirect(request.referrer or url_for('kullanici_yonetim'))

@app.route('/profil')
def profil():
    """Profil sayfası."""
    if 'tc' not in session:
        return redirect(url_for('kullanici_giris'))
    return render_template('kutuphane_kullanici.html')

@app.route('/sifre_degistir', methods=['POST'])
def sifre_degistir():
    """Şifre değiştirme işlemi."""
    if 'tc' not in session:
        return redirect(url_for('kullanici_giris'))
    
    eski_sifre = request.form['eski_sifre']
    yeni_sifre = request.form['yeni_sifre']
    yeni_sifre_tekrar = request.form['yeni_sifre_tekrar']
    
    if yeni_sifre != yeni_sifre_tekrar:
        flash('Yeni şifreler eşleşmiyor!')
        return redirect(url_for('kutuphane_kullanici'))
    
    conn = veritabani_baglantisi()
    cur = conn.cursor()
    
    rol = session['rol']
    tablo = 'kullanicilar' if rol == 'kullanici' else 'personel'
    cur.execute(f'SELECT sifre FROM {tablo} WHERE tc = ?', (session['tc'],))
    mevcut_sifre = cur.fetchone()['sifre']
    
    if mevcut_sifre != eski_sifre:
        flash('Eski şifre yanlış!')
    else:
        cur.execute(f'UPDATE {tablo} SET sifre = ? WHERE tc = ?', (yeni_sifre, session['tc']))
        conn.commit()
        flash('Şifre başarıyla değiştirildi!')
    
    conn.close()
    return redirect(url_for('kutuphane_kullanici' if session['rol'] == 'kullanici' else 'kutuphane_personel'))

@app.route('/foto_degistir', methods=['POST'])
def foto_degistir():
    """Profil fotoğrafı değiştirme işlemi."""
    if 'tc' not in session:
        return redirect(url_for('kullanici_giris'))

    if 'foto' not in request.files:
        flash('Dosya seçilmedi!')
        return redirect(url_for('kutuphane_kullanici'))

    file = request.files['foto']
    if file.filename == '':
        flash('Dosya seçilmedi!')
        return redirect(url_for('kutuphane_kullanici'))

    if file and allowed_file(file.filename):
        file_data = base64.b64encode(file.read()).decode('utf-8')

        conn = veritabani_baglantisi()
        cur = conn.cursor()
        rol = session['rol']
        tablo = 'kullanicilar' if rol == 'kullanici' else 'personel'
        cur.execute(f'UPDATE {tablo} SET foto = ? WHERE tc = ?', (file_data, session['tc']))
        conn.commit()
        conn.close()

        flash('Fotoğraf başarıyla güncellendi!')
        return redirect(url_for('kutuphane_kullanici' if session['rol'] == 'kullanici' else 'kutuphane_personel'))
    
    flash('Geçersiz dosya formatı! Yalnızca PNG, JPG, JPEG, GIF kabul edilir.')
    return redirect(url_for('kutuphane_kullanici' if session['rol'] == 'kullanici' else 'kutuphane_personel'))

@app.route('/kullanici_yonetim', methods=['GET', 'POST'])
def kullanici_yonetim():
    if 'tc' not in session or session.get('rol') != 'personel':
        return redirect(url_for('personel_giris'))

    conn = veritabani_baglantisi()
    cur = conn.cursor()

    odunc_kitaplar = None
    tc = None
    mevcut_kitaplar = None

    if request.method == 'POST':
        if 'tc' in request.form and 'sifre' in request.form and 'ad' in request.form and 'soyad' in request.form:
            tc = request.form['tc']
            sifre = request.form['sifre']
            ad = request.form['ad']
            soyad = request.form['soyad']
            try:
                cur.execute("INSERT INTO kullanicilar (tc, sifre, ad, soyad) VALUES (?, ?, ?, ?)", (tc, sifre, ad, soyad))
                conn.commit()
                flash('Kullanıcı başarıyla eklendi!')
            except sqlite3.IntegrityError:
                flash('Bu TC kimlik numarası zaten kayıtlı!')

        elif 'sil_tc' in request.form:
            tc = request.form['sil_tc']
            try:
                cur.execute('DELETE FROM kullanicilar WHERE tc = ?', (tc,))
                conn.commit()
                flash('Kullanıcı başarıyla silindi!')
            except Exception as e:
                flash(f'Hata: {str(e)}')

        elif 'tc' in request.form and 'sifre' in request.form:
            tc = request.form['tc']
            sifre = request.form['sifre']
            cur.execute('SELECT * FROM kullanicilar WHERE tc = ? AND sifre = ?', (tc, sifre))
            kullanici = cur.fetchone()
            if not kullanici:
                flash('Geçersiz TC veya şifre!')
            else:
                cur.execute(''' 
                    SELECT k.kitap_adi, k.yazar, o.odunc_zamani, o.iade_zamani, o.kitap_id
                    FROM odunc o 
                    JOIN kitaplar k ON o.kitap_id = k.id 
                    WHERE o.tc = ? AND o.durum = 'alindi'
                ''', (tc,))
                odunc_kitaplar = cur.fetchall()
                cur.execute('SELECT id, kitap_adi, yazar, stok FROM kitaplar WHERE stok > 0')
                mevcut_kitaplar = cur.fetchall()

    cur.execute('SELECT tc, ad, soyad FROM kullanicilar')
    kullanicilar = cur.fetchall()

    conn.close()
    return render_template('kullanici_yonetim.html', 
                         odunc_kitaplar=odunc_kitaplar, 
                         tc=tc,
                         mevcut_kitaplar=mevcut_kitaplar,
                         kullanicilar=kullanicilar)

@app.route('/search_books', methods=['POST'])
def search_books():
    data = request.get_json()
    query = data.get('query', '').lower()

    conn = veritabani_baglantisi()
    cur = conn.cursor()

    # Kitapları büyük-küçük harf duyarlılığı olmadan arama
    cur.execute('''
        SELECT id, kitap_adi, stok 
        FROM kitaplar 
        WHERE LOWER(kitap_adi) LIKE ? 
        ORDER BY kitap_adi
    ''', (f'%{query}%',))

    kitaplar = cur.fetchall()
    conn.close()

    # Kitapları JSON formatında döndür
    kitaplar_list = [dict(kitap) for kitap in kitaplar]
    return jsonify(kitaplar_list)

@app.route('/islemler', methods=['GET', 'POST'])
def islemler():
    if request.method == 'POST':
        tc = request.form['tc']
        conn = veritabani_baglantisi()
        cur = conn.cursor()
        cur.execute('SELECT ad, soyad FROM kullanicilar WHERE tc = ?', (tc,))
        kullanici = cur.fetchone()
        conn.close()
        if kullanici:
            kullanici_dict = dict(kullanici)  # SQLite Row nesnesini sözlüğe çevir
            kullanici_dict['ad_soyad'] = f"{kullanici['ad']} {kullanici['soyad']}"
            return render_template('islemler.html', kullanici=kullanici_dict)
        else:
            flash('Kullanıcı bulunamadı!', 'error')
    return render_template('islemler.html')

@app.route('/kitap_odunc_al', methods=['POST'])
def kitap_odunc_al():
    if 'tc' not in session or session.get('rol') != 'personel':
        return redirect(url_for('personel_giris'))
    
    kitap_id = request.form['kitap_id']
    kullanici_tc = request.form['kullanici_tc']
    
    conn = veritabani_baglantisi()
    cur = conn.cursor()
    
    cur.execute('SELECT stok FROM kitaplar WHERE id = ?', (kitap_id,))
    stok = cur.fetchone()['stok']
    
    if stok > 0:
        cur.execute(''' 
            INSERT INTO odunc (tc, kitap_id, durum) 
            VALUES (?, ?, 'alindi')
        ''', (kullanici_tc, kitap_id))
        cur.execute('UPDATE kitaplar SET stok = stok - 1 WHERE id = ?', (kitap_id,))
        conn.commit()
        flash('Kitap başarıyla ödünç verildi!')
    else:
        flash('Bu kitap stokta yok!')
    
    conn.close()
    return redirect(url_for('islemler'))

@app.route('/kullanici_cikis')
def kullanici_cikis():
    """Kullanıcılar için oturum kapatma işlemi."""
    session.clear()
    return redirect(url_for('kullanici_giris'))

@app.route('/personel_cikis')
def personel_cikis():
    """Personeller için oturum kapatma işlemi."""
    session.clear()
    return redirect(url_for('personel_giris'))

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)