import sqlite3

def create_db():
    conn = sqlite3.connect('kutuphane.db')
    c = conn.cursor()

    # Mevcut tabloları sil (yeniden oluşturmadan önce temizlik)
    c.execute('DROP TABLE IF EXISTS kullanicilar')
    c.execute('DROP TABLE IF EXISTS personel')
    c.execute('DROP TABLE IF EXISTS kitaplar')
    c.execute('DROP TABLE IF EXISTS odunc')

    # Kullanıcılar tablosu
    c.execute(''' 
        CREATE TABLE kullanicilar (
            tc TEXT PRIMARY KEY,
            sifre TEXT NOT NULL,
            ad TEXT NOT NULL,
            soyad TEXT NOT NULL,
            foto TEXT
        )
    ''')

    # Personel tablosu
    c.execute(''' 
        CREATE TABLE personel (
            id INTEGER PRIMARY KEY,
            tc TEXT UNIQUE NOT NULL,
            sifre TEXT NOT NULL,
            ad TEXT NOT NULL,
            soyad TEXT NOT NULL,
            guvenlik_cevap TEXT NOT NULL,
            foto TEXT
        )
    ''')

    c.execute(''' 
    CREATE TABLE kitaplar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kitap_adi TEXT NOT NULL,
        yazar TEXT NOT NULL,
        sayfa_sayisi INTEGER NOT NULL,
        kategori TEXT NOT NULL,
        stok INTEGER NOT NULL DEFAULT 1
    )
''')

    # Ödünç tablosu
    c.execute(''' 
    CREATE TABLE odunc (
        id INTEGER PRIMARY KEY,
        tc TEXT NOT NULL,
        kitap_id INTEGER NOT NULL,
        durum TEXT NOT NULL DEFAULT 'alindi',
        odunc_zamani TIMESTAMP,
        iade_zamani TIMESTAMP,
        FOREIGN KEY (kitap_id) REFERENCES kitaplar (id)
    )
''')

    # Örnek kullanıcı ve personel ekleme
    c.execute("INSERT OR IGNORE INTO kullanicilar (tc, sifre, ad, soyad, foto) VALUES (?, ?, ?, ?, ?)", 
             ('11111111111', '11', 'Ahmet', 'Yılmaz', None))
    c.execute("INSERT OR IGNORE INTO personel (tc, sifre, ad, soyad, guvenlik_cevap, foto) VALUES (?, ?, ?, ?, ?, ?)", 
             ('99999999999', '11', 'Mehmet', 'Demir', '2024', None))

    # Örnek kitaplar
    ornek_kitaplar = [
        ('Suç ve Ceza', 'Fyodor Dostoyevski', 700, 'Roman', 5),
        ('1984', 'George Orwell', 328, 'Distopya', 3),
        ('Şeker Portakalı', 'Jose Mauro de Vasconcelos', 180, 'Roman', 2),
        ('Küçük Prens', 'Antoine de Saint-Exupéry', 96, 'Çocuk', 4),
        ('Fareler ve İnsanlar', 'John Steinbeck', 120, 'Roman', 3),
        ('Yüzüklerin Efendisi', 'J.R.R. Tolkien', 1178, 'Fantastik', 6),
        ('Harry Potter ve Felsefe Taşı', 'J.K. Rowling', 223, 'Fantastik', 8),
        ('Simyacı', 'Paulo Coelho', 208, 'Roman', 4),
        ('Dönüşüm', 'Franz Kafka', 74, 'Klasik', 3),
        ('Beyaz Diş', 'Jack London', 320, 'Macera', 2),
        ('Sefiller', 'Victor Hugo', 1463, 'Klasik', 4),
        ('Don Kişot', 'Miguel de Cervantes', 1072, 'Roman', 3),
        ('Dava', 'Franz Kafka', 216, 'Klasik', 2),
        ('Beyaz Gemi', 'Cengiz Aytmatov', 160, 'Roman', 3),
        ('Kürk Mantolu Madonna', 'Sabahattin Ali', 160, 'Roman', 4),
        ('İnce Memed', 'Yaşar Kemal', 460, 'Roman', 5),
        ('Tutunamayanlar', 'Oğuz Atay', 724, 'Roman', 3),
        ('Kara Kitap', 'Orhan Pamuk', 400, 'Roman', 2),
        ('Yaprak Dökümü', 'Reşat Nuri Güntekin', 200, 'Roman', 4),
        ('Çalıkuşu', 'Reşat Nuri Güntekin', 423, 'Roman', 5),
        ('Sinekli Bakkal', 'Halide Edip Adıvar', 240, 'Roman', 3),
        ('Ateşten Gömlek', 'Halide Edip Adıvar', 236, 'Tarih', 2),
        ('Kiralık Konak', 'Yakup Kadri Karaosmanoğlu', 240, 'Roman', 4),
        ('Yaban', 'Yakup Kadri Karaosmanoğlu', 208, 'Roman', 3),
        ('Fatih-Harbiye', 'Peyami Safa', 140, 'Roman', 2),
        ('Dokuzuncu Hariciye Koğuşu', 'Peyami Safa', 112, 'Roman', 3),
        ('Bir Bilim Adamının Romanı', 'Oğuz Atay', 300, 'Biyografi', 4),
        ('Tehlikeli Oyunlar', 'Oğuz Atay', 500, 'Roman', 3),
        ('Kurt Kanunu', 'Kemal Tahir', 368, 'Tarih', 5)
    ]

    c.executemany(''' 
        INSERT OR IGNORE INTO kitaplar (kitap_adi, yazar, sayfa_sayisi, kategori, stok) 
        VALUES (?, ?, ?, ?, ?)
    ''', ornek_kitaplar)
    
    conn.commit()
    conn.close()
    print("Veritabanı başarıyla oluşturuldu!")

def kitaplari_getir(kitap_adi=None, yazar=None, min_sayfa=None, max_sayfa=None, kategori=None):
    conn = sqlite3.connect('kutuphane.db')
    c = conn.cursor()

    # Temel sorgu
    sorgu = "SELECT * FROM kitaplar WHERE 1=1"
    parametreler = []

    # Kitap adı filtresi
    if kitap_adi:
        sorgu += " AND kitap_adi LIKE ?"
        parametreler.append(f"%{kitap_adi}%")

    # Yazar filtresi
    if yazar:
        sorgu += " AND yazar LIKE ?"
        parametreler.append(f"%{yazar}%")

    # Sayfa sayısı filtresi
    if min_sayfa:
        sorgu += " AND sayfa_sayisi >= ?"
        parametreler.append(min_sayfa)
    if max_sayfa:
        sorgu += " AND sayfa_sayisi <= ?"
        parametreler.append(max_sayfa)

    # Kategori filtresi
    if kategori:
        sorgu += " AND kategori = ?"
        parametreler.append(kategori)

    # Sorguyu çalıştır
    c.execute(sorgu, parametreler)
    kitaplar = c.fetchall()

    conn.close()
    return kitaplar


if __name__ == '__main__':
    create_db()