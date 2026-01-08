#EndPoint aracılığıyla maydagold.com sitesinden altın ve gümüş fiyatlarını çeker
import requests
from datetime import datetime


def get_mayda_prices():
    """Mayda.com JSON endpoint'inden altın ve gümüş fiyatlarını çek"""
    url = "https://maydagold.com/kurlar/web.json"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()

        # JSON yapısı: data[0] -> ürünler listesi
        if not data or len(data) == 0 or not isinstance(data[0], list):
            print("Veri bulunamadı!")
            return None

        urunler_listesi = data[0]

        # Belirli ürünleri filtrele (JSON'daki adlarla)
        istenen_urunler = {
            'BİLEZİK': 'BİLEZİK',
            'ÇEYREK': 'ÇEYREK ALTIN',
            'EYREK': 'ÇEYREK ALTIN',
            'YARIM': 'YARIM ALTIN',
            'TAM': 'TAM ALTIN',
            'GREMSE': 'GREMSE ALTIN',
            'ATA LİRA': 'ATA LİRA',
            '1 GRAMLIK': '1 GRAMLIK ALTIN'
        }

        products = []

        for urun in urunler_listesi:
            urun_adi = urun.get('adi', '').upper()

            if urun_adi in istenen_urunler:
                # Alış ve satış fiyatlarını al (zaten TL cinsinden)
                alis = float(urun.get('alis', 0))
                satis = float(urun.get('satis', 0))

                # Tam sayıya çevir
                alis_fiyat = int(alis)
                satis_fiyat = int(satis)
                fark = satis_fiyat - alis_fiyat
                fark_yuzde = (fark / alis_fiyat) * 100 if alis_fiyat > 0 else 0

                # Açıklama alanını kullan, yoksa mapping'den al
                urun_tam_adi = urun.get('aciklama', istenen_urunler[urun_adi])

                product = {
                    'urun_adi': urun_tam_adi,
                    'alis_fiyati': alis_fiyat,
                    'satis_fiyati': satis_fiyat,
                    'fark': fark,
                    'fark_yuzde': round(fark_yuzde, 2)
                }

                products.append(product)

        return {
            'kaynak': 'Mayda.com API',
            'tarih': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'urunler': products
        }

    except Exception as e:
        print(f"Mayda.com API hatası: {e}")
        return None


if __name__ == "__main__":
    data = get_mayda_prices()
    if data:
        print(f"\n{data['kaynak']} - {data['tarih']}")
        print(f"{len(data['urunler'])} ürün bulundu\n")
        for i, u in enumerate(data['urunler'], 1):
            print(f"  {i}. {u['urun_adi']}: {u['alis_fiyati']:,.2f} TL (Komisyon: %{u['fark_yuzde']:.2f})")
