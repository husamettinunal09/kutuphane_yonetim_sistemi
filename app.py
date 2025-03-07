from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from typing import Dict, Any, Union
import os
import base64
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'gizli_anahtar'

# Dosya yükleme ayarları (artık sadece kontrol için kullanılacak)
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

@app.route('/kutuphane_personel', methods=['GET', 'POST'])
def kutuphane_personel():
    """Kütüphane ana sayfası ve kitap işlemleri."""
    if 'tc' not in session:
        return redirect(url_for('personel_giris'))

    conn = veritabani_baglantisi()
    cur = conn.cursor()

    sayfa = request.args.get('sayfa', 1, type=int)
    sayfa_basi = 10

    cur.execute('SELECT COUNT(*) as toplam FROM kitaplar')
    toplam_kitap = cur.fetchone()['toplam']
    toplam_sayfa = (toplam_kitap + sayfa_basi - 1) // sayfa_basi

    offset = (sayfa - 1) * sayfa_basi
    cur.execute(''' 
        SELECT k.*, 
               (SELECT COUNT(*) FROM odunc 
                WHERE kitap_id = k.id AND tc = ? AND durum = 'alindi') as alinmis 
        FROM kitaplar k
        LIMIT ? OFFSET ?
    ''', (session['tc'], sayfa_basi, offset))
    kitaplar = cur.fetchall()

    conn.close()
    return render_template('kutuphane_personel.html', 
                         kitaplar=kitaplar,
                         sayfa=sayfa,
                         toplam_sayfa=toplam_sayfa)

@app.route('/kutuphane_kullanici', methods=['GET', 'POST'])
def kutuphane_kullanici():
    """Kitap yönetim sayfası ve kitap işlemleri."""
    if 'tc' not in session or session.get('rol') != 'kullanici':
        flash('Bu sayfaya erişim yetkiniz yok!')
        return redirect(url_for('kullanici_giris')) 

    conn = veritabani_baglantisi()
    cur = conn.cursor()

    sayfa = request.args.get('sayfa', 1, type=int)
    sayfa_basi = 10

    cur.execute('SELECT COUNT(*) as toplam FROM kitaplar')
    toplam_kitap = cur.fetchone()['toplam']
    toplam_sayfa = (toplam_kitap + sayfa_basi - 1) // sayfa_basi

    offset = (sayfa - 1) * sayfa_basi
    cur.execute(''' 
        SELECT k.id, k.kitap_adi, k.yazar, k.sayfa_sayisi, k.kategori, k.stok,
               (SELECT COUNT(*) FROM odunc 
                WHERE kitap_id = k.id AND tc = ? AND durum = 'alindi') as alinmis 
        FROM kitaplar k
        LIMIT ? OFFSET ?
    ''', (session['tc'], sayfa_basi, offset))
    kitaplar = cur.fetchall()

    cur.execute(''' 
        SELECT k.kitap_adi, k.yazar, o.odunc_zamani 
        FROM odunc o 
        JOIN kitaplar k ON o.kitap_id = k.id 
        WHERE o.tc = ? AND o.durum = 'alindi'
    ''', (session['tc'],))
    odunc_kitaplar = cur.fetchall()

    # Kullanıcının fotoğrafını al
    cur.execute('SELECT foto FROM kullanicilar WHERE tc = ?', (session['tc'],))
    foto = cur.fetchone()['foto']

    conn.close()
    
    return render_template('kutuphane_kullanici.html', 
                           kitaplar=kitaplar, 
                           odunc_kitaplar=odunc_kitaplar,
                           sayfa=sayfa, 
                           toplam_sayfa=toplam_sayfa,
                           foto=foto)

@app.route('/kitap_odunc_ver', methods=['POST'])
def kitap_odunc_ver():
    if 'tc' not in session or session.get('rol') != 'personel':
        return redirect(url_for('personel_giris'))
    
    kitap_id = request.form['kitap_id']
    kullanici_tc = request.form['kullanici_tc']
    
    conn = veritabani_baglantisi()
    cur = conn.cursor()
    
    cur.execute('SELECT stok FROM kitaplar WHERE id = ?', (kitap_id,))
    stok = cur.fetchone()['stok']
    
    if stok > 0:
        cur.execute('INSERT INTO odunc (tc, kitap_id, odunc_zamani, durum) VALUES (?, ?, CURRENT_TIMESTAMP, "alindi")', 
                    (kullanici_tc, kitap_id))
        cur.execute('UPDATE kitaplar SET stok = stok - 1 WHERE id = ?', (kitap_id,))
        conn.commit()
        flash('Kitap başarıyla ödünç verildi!')
    else:
        flash('Bu kitap stokta yok!')
    
    conn.close()
    return redirect(url_for('kutuphane_personel'))

@app.route('/profil')
def profil():
    if 'tc' not in session:
        return redirect(url_for('kullanici_giris'))
    return render_template('kutuphane_kullanici.html')

@app.route('/sifre_degistir', methods=['POST'])
def sifre_degistir():
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
    return redirect(url_for('kutuphane_kullanici'))

@app.route('/foto_degistir', methods=['POST'])
def foto_degistir():
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
        # Dosyayı base64 formatına çevir
        file_data = file.read()
        base64_image = base64.b64encode(file_data).decode('utf-8')

        conn = veritabani_baglantisi()
        cur = conn.cursor()
        rol = session['rol']
        tablo = 'kullanicilar' if rol == 'kullanici' else 'personel'
        cur.execute(f'UPDATE {tablo} SET foto = ? WHERE tc = ?', (base64_image, session['tc']))
        conn.commit()
        conn.close()

        flash('Fotoğraf başarıyla güncellendi!')
        return redirect(url_for('kutuphane_kullanici'))
    
    flash('Geçersiz dosya formatı! Yalnızca PNG, JPG, JPEG, GIF kabul edilir.')
    return redirect(url_for('kutuphane_kullanici'))

@app.route('/cikis')
def cikis():
    """Oturum kapatma işlemi."""
    session.clear()
    return redirect(url_for('kullanici_giris'))

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Upload klasörünü oluştur (hala varsayılan foto için kullanılabilir)
    app.run(debug=True)