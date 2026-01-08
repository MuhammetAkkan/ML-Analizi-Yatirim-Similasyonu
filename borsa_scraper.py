# Borsa İstanbul'dan gümüş BYF fiyatını çekme ve default olarak % komisyon ekleme
import requests
from datetime import datetime


def get_borsa_silver_price():
    """Borsa İstanbul'dan gümüş BYF fiyatını JSON API'den çek"""
    url = "https://bigpara.hurriyet.com.tr/api/v1/borsa/hisseyuzeysel/GMSTR"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()

        # JSON yapısı: data.hisseYuzeysel.kapanis
        if 'data' not in data or 'hisseYuzeysel' not in data['data']:
            print("Fiyat verisi bulunamadı!")
            return None

        hisse_data = data['data']['hisseYuzeysel']
        fiyat = float(hisse_data.get('kapanis', 0))

        if fiyat == 0:
            print("Fiyat sıfır!")
            return None

        # %5 komisyon ekle
        satis_fiyat = fiyat * 1.03

        return {
            'kaynak': 'Borsa İstanbul API',
            'tarih': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'urun': {
                'urun_adi': 'BORSA - QNB PORTFÖY GÜMÜŞ KATILIM BYF',
                'alis_fiyati': int(fiyat),
                'satis_fiyati': int(satis_fiyat),
                'fark': int(satis_fiyat - fiyat),
                'fark_yuzde': 5.0
            }
        }

    except Exception as e:
        print(f"Borsa API hatası: {e}")
        return None


if __name__ == "__main__":
    data = get_borsa_silver_price()
    if data:
        print(f"\n{data['kaynak']} - {data['tarih']}")
        u = data['urun']
        print(f"{u['urun_adi']}: {u['alis_fiyati']:,.2f} TL (Komisyon: %{u['fark_yuzde']:.2f})")

