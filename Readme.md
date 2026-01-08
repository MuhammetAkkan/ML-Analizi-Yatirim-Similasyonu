# ML Analizi ile Yatırım Simülasyonu

Bu proje, Python ile Parçacık Sürü Optimizasyonu (PSO) algoritması kullanarak altın ve gümüş ürünlerinden minimum komisyonla maksimum bütçe kullanımı sağlayan portföy önerisi sunar.

## Özellikler

- **Otomatik veri çekme:** Mayda.com ve Borsa İstanbul'dan güncel fiyatlar alınır.
- **PSO algoritması:** Komisyonu minimize ederek bütçeyi en verimli şekilde kullanır.
- **Görsel rapor:** Sonuçlar grafiklerle ve özetlerle görselleştirilir.
- **Konsol çıktısı:** Detaylı portföy ve finansal özet sunar.

## Kurulum

1. Python 3.10+ kurulu olmalıdır.
2. Gerekli paketleri yükleyin:
   ```
   pip install numpy matplotlib
   ```
3. Proje dosyalarını klonlayın:
   ```
   git clone https://github.com/MuhammetAkkan/ML-Analizi-Yatirim-Similasyonu.git
   ```

## Kullanım

1. Ana dizinde `main.py` dosyasını çalıştırın:
   ```
   python main.py
   ```
2. Bütçenizi TL cinsinden girin.
3. Sonuçları konsolda ve görsel raporda inceleyin.

## Dosya Yapısı

- `main.py`: Ana uygulama ve PSO algoritması.
- `mayda_scraper.py`: Mayda.com'dan veri çekme fonksiyonu.
- `borsa_scraper.py`: Borsa İstanbul'dan gümüş fiyatı çekme fonksiyonu.

## Katkı

Pull request'ler ve geri bildirimleriniz için teşekkürler! Katkı sağlamak için lütfen bir PR gönderin.

## Lisans

MIT Lisansı altında sunulmaktadır.

