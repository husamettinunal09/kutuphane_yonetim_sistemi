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
    kitap_adi = request.form['kitap_adi']
    yazar = request.form['yazar']
    sayfa_sayisi = request.form['sayfa_sayisi']
    kategori = request.form['kategori']
    stok = request.form['stok']
    
    conn = veritabani_baglantisi()
    cur = conn.cursor()
    
    if kitap_id:
        # Kitap güncelleme
        cur.execute(''' 
            UPDATE kitaplar 
            SET kitap_adi = ?, yazar = ?, sayfa_sayisi = ?, kategori = ?, stok = ?
            WHERE id = ?
        ''', (kitap_adi, yazar, sayfa_sayisi, kategori, stok, kitap_id))
        flash('Kitap başarıyla güncellendi!')
    else:
        # Yeni kitap ekleme
        cur.execute(''' 
            INSERT INTO kitaplar (kitap_adi, yazar, sayfa_sayisi, kategori, stok)
            VALUES (?, ?, ?, ?, ?)
        ''', (kitap_adi, yazar, sayfa_sayisi, kategori, stok))
        flash('Kitap başarıyla eklendi!')
    
    conn.commit()
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
    
    # Kitap bilgilerini forma otomatik doldurmak için burada bir çözüm uygulayabiliriz
    # Ancak bu örnekte basitlik adına doğrudan mevcut formu kullanıyoruz
    flash('Kitap ID alanına ID\'yi girerek güncelleyin.')
    return redirect(url_for('kutuphane_personel'))

@app.route('/kitap_sil', methods=['POST'])
def kitap_sil():
    """Kitap silme işlemi."""
    if 'tc' not in session or session.get('rol') != 'personel':
        return redirect(url_for('personel_giris'))
    
    kitap_id = request.form['kitap_id']
    
    conn = veritabani_baglantisi()
    cur = conn.cursor()
    
    # Kitabın ödünç alınıp alınmadığını kontrol et
    cur.execute('SELECT COUNT(*) FROM odunc WHERE kitap_id = ? AND durum = ?', (kitap_id, 'alindi'))
    odunc_sayisi = cur.fetchone()[0]
    
    if odunc_sayisi > 0:
        flash('Bu kitap şu anda ödünç alınmış, silinemez!')
    else:
        cur.execute('DELETE FROM kitaplar WHERE id = ?', (kitap_id,))
        conn.commit()
        flash('Kitap başarıyla silindi!')
    
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
        return redirect(url_for('personel_giris'))
    
    kitap_id = request.form['kitap_id']
    tc = request.form['tc']
    
    conn = veritabani_baglantisi()
    cur = conn.cursor()
    
    cur.execute(''' 
        UPDATE odunc 
        SET durum = 'iade', iade_zamani = CURRENT_TIMESTAMP 
        WHERE kitap_id = ? AND tc = ? AND durum = 'alindi'
    ''', (kitap_id, tc))
    cur.execute('UPDATE kitaplar SET stok = stok + 1 WHERE id = ?', (kitap_id,))
    conn.commit()
    
    flash('Kitap başarıyla iade edildi!')
    conn.close()
    return redirect(url_for('kullanici_yonetim'))

@app.route('/kullanici_yonetim', methods=['GET', 'POST'])
def kullanici_yonetim():
    """Kullanıcı yönetimi sayfası."""
    if 'tc' not in session or session.get('rol') != 'personel':
        return redirect(url_for('personel_giris'))

    conn = veritabani_baglantisi()
    cur = conn.cursor()

    odunc_kitaplar = None
    tc = None
    mevcut_kitaplar = None

    if request.method == 'POST':
        tc = request.form['tc']
        sifre = request.form['sifre']
        
        cur.execute('SELECT * FROM kullanicilar WHERE tc = ? AND sifre = ?', (tc, sifre))
        kullanici = cur.fetchone()
        
        if not kullanici:
            flash('Geçersiz TC veya şifre!')
            conn.close()
            return render_template('kullanici_yonetim.html', odunc_kitaplar=None)

        # Ödünç alınan kitaplar
        cur.execute(''' 
            SELECT k.kitap_adi, k.yazar, o.odunc_zamani, o.iade_zamani, o.kitap_id
            FROM odunc o 
            JOIN kitaplar k ON o.kitap_id = k.id 
            WHERE o.tc = ? AND o.durum = 'alindi'
        ''', (tc,))
        odunc_kitaplar = cur.fetchall()

        # Mevcut kitaplar (stok > 0 olanlar)
        cur.execute('SELECT id, kitap_adi, yazar, stok FROM kitaplar WHERE stok > 0')
        mevcut_kitaplar = cur.fetchall()

    conn.close()
    return render_template('kullanici_yonetim.html', 
                         odunc_kitaplar=odunc_kitaplar, 
                         tc=tc,
                         mevcut_kitaplar=mevcut_kitaplar)

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

@app.route('/cikis')
def cikis():
    """Oturum kapatma işlemi."""
    session.clear()
    return redirect(url_for('kullanici_giris'))

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)