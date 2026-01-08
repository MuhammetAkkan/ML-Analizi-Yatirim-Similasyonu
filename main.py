"""
ALTIN-GÜMÜŞ PORTFÖY OPTİMİZASYONU
PSO ile en düşük komisyonlu ürünleri seçerek minimum komisyonlu ürünleri alma ve maximum bütçe kullanımıyla alma
"""
import numpy as np
import random
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')

from mayda_scraper import get_mayda_prices
from borsa_scraper import get_borsa_silver_price


class ProductBasedPSO:
    """PSO ile komisyon minimize ederek maksimum ürün alımı"""

    def __init__(self, n_particles=30, n_iterations=50, w=0.7, c1=1.5, c2=1.5):
        self.n_particles = n_particles
        self.n_iterations = n_iterations
        self.w = w
        self.c1 = c1
        self.c2 = c2

    def greedy_solution(self, urunler, maas):
        """
        Greedy Çözüm: Düşük komisyonlu ürünlerden sırayla al
        Strateji:
        1. En düşük komisyonlu üründen maksimum al
        2. Kalan parayla bir sonraki düşük komisyonlu üründen al
        3. Bütçeyi tamamen kullanana kadar devam et
        """
        n_urunler = len(urunler)
        solution = np.zeros(n_urunler, dtype=int)
        kalan_butce = maas

        # Ürünler zaten komisyona göre sıralı (en düşükten en yükseğe)
        for i in range(n_urunler):
            urun = urunler[i]
            if urun['alis_fiyati'] > 0 and kalan_butce >= urun['alis_fiyati']:
                # Bu üründen maksimum kaç adet alınabilir?
                max_adet = int(kalan_butce / urun['alis_fiyati'])
                solution[i] = max_adet
                kalan_butce -= max_adet * urun['alis_fiyati']

                # Kalan para çok azsa dur
                if kalan_butce < min(u['alis_fiyati'] for u in urunler if u['alis_fiyati'] > 0):
                    break

        return solution

    def fitness_function(self, urun_adetleri, urunler, maas):
        """
        Fitness: ALICI perspektifi
        1. Düşük komisyon (en önemli)
        2. Yüksek bütçe kullanımı (nakiti 0'a yaklaştır)
        3. Minimize edilmiş komisyon kaybı

        NOT: Biz ürünleri SATIŞ fiyatından alıyoruz, ALIŞ fiyatından satıyoruz
        Yani komisyon bizim için KAYIP (negatif)
        """
        toplam_alis = 0
        toplam_satis = 0
        toplam_komisyon_kaybi = 0

        for i, adet in enumerate(urun_adetleri):
            if adet > 0:
                urun = urunler[i]
                alis_maliyet = adet * urun['alis_fiyati']
                satis_gelir = adet * urun['satis_fiyati']
                toplam_alis += alis_maliyet
                toplam_satis += satis_gelir
                toplam_komisyon_kaybi += (satis_gelir - alis_maliyet)

        # Bütçe kontrolü
        if toplam_alis > maas:
            return -1e10

        # Minimum %90 bütçe kullanımı şartı
        if toplam_alis == 0 or toplam_alis < maas * 0.90:
            return -1e10

        # Ortalama komisyon oranı (ne kadar düşükse o kadar iyi)
        avg_komisyon = abs(toplam_komisyon_kaybi / toplam_alis) * 100 if toplam_alis > 0 else 100

        # Bütçe kullanım oranı (%100'e ne kadar yakınsa o kadar iyi)
        kullanim_orani = toplam_alis / maas

        # FITNESS HESAPLAMA:
        komisyon_faktor = max(0.1, (20 - avg_komisyon)) ** 4

        # 2. Bütçe kullanımı önemli: %100'e yakın olmalı
        #    %100 -> 1.0, %95 -> 0.95, %90 -> 0.90
        butce_faktor = kullanim_orani ** 2  # Karesini alarak %100'e yakınlığı ödüllendiriyoruz

        # 3. Komisyon kaybını minimize et (negatif, bu yüzden ekliyoruz)
        komisyon_kaybi_faktor = toplam_komisyon_kaybi

        # Final fitness: Düşük Komisyon >> Yüksek Bütçe Kullanımı >> Minimize Komisyon Kaybı
        fitness = komisyon_faktor * 1000000 + butce_faktor * 10000 + komisyon_kaybi_faktor

        return fitness

    def optimize(self, urunler, maas):
        """PSO algoritması ile optimizasyon"""
        n_urunler = len(urunler)

        # Maksimum adetler
        max_adetler = [int(maas / u['alis_fiyati']) if u['alis_fiyati'] > 0 else 0 for u in urunler]

        # Parçacıkları başlat
        particles_pos = np.zeros((self.n_particles, n_urunler), dtype=int)
        particles_vel = np.zeros((self.n_particles, n_urunler), dtype=float)

        # İlk parçacık: Greedy çözüm
        particles_pos[0] = self.greedy_solution(urunler, maas)

        # Diğer parçacıklar: Rastgele
        for i in range(1, self.n_particles):
            kalan_butce = maas
            for j in range(n_urunler):
                if kalan_butce > 0 and max_adetler[j] > 0:
                    max_adet = min(max_adetler[j], int(kalan_butce / urunler[j]['alis_fiyati']))
                    if max_adet > 0:
                        adet = random.randint(0, max_adet)
                        particles_pos[i, j] = adet
                        kalan_butce -= adet * urunler[j]['alis_fiyati']

        # Kişisel en iyi
        pbest_pos = particles_pos.copy()
        pbest_fitness = np.array([self.fitness_function(p, urunler, maas) for p in particles_pos])

        # Global en iyi
        gbest_idx = np.argmax(pbest_fitness)
        gbest_pos = pbest_pos[gbest_idx].copy()
        gbest_fitness = pbest_fitness[gbest_idx]

        fitness_history = [gbest_fitness]

        # PSO iterasyonları
        for iteration in range(self.n_iterations):
            for i in range(self.n_particles):
                r1, r2 = random.random(), random.random()

                particles_vel[i] = (
                    self.w * particles_vel[i] +
                    self.c1 * r1 * (pbest_pos[i] - particles_pos[i]) +
                    self.c2 * r2 * (gbest_pos - particles_pos[i])
                )

                particles_pos[i] = particles_pos[i] + np.round(particles_vel[i]).astype(int)

                # Sınırları kontrol et
                for j in range(n_urunler):
                    particles_pos[i, j] = np.clip(particles_pos[i, j], 0, max_adetler[j])

                # Bütçe kontrolü
                toplam = sum(particles_pos[i, j] * urunler[j]['alis_fiyati'] for j in range(n_urunler))
                while toplam > maas:
                    max_idx = np.argmax(particles_pos[i])
                    if particles_pos[i, max_idx] > 0:
                        particles_pos[i, max_idx] -= 1
                        toplam = sum(particles_pos[i, j] * urunler[j]['alis_fiyati'] for j in range(n_urunler))
                    else:
                        break

                current_fitness = self.fitness_function(particles_pos[i], urunler, maas)

                if current_fitness > pbest_fitness[i]:
                    pbest_fitness[i] = current_fitness
                    pbest_pos[i] = particles_pos[i].copy()

                if current_fitness > gbest_fitness:
                    gbest_fitness = current_fitness
                    gbest_pos = particles_pos[i].copy()

            fitness_history.append(gbest_fitness)

        # Kalan parayla EN DÜŞÜK KOMİSYONLU ürünlerden ek al (ürünler zaten sıralı)
        # Bütçeyi ASLA aşmamak için dikkatli hesaplama
        kalan_para = maas - sum(gbest_pos[j] * urunler[j]['alis_fiyati'] for j in range(n_urunler))

        for i in range(n_urunler):
            # Ürünler zaten komisyona göre sıralı (en düşükten en yükseğe)
            # Kalan parayla bu üründen alabildiğimiz kadar al
            while kalan_para >= urunler[i]['alis_fiyati'] and urunler[i]['alis_fiyati'] > 0:
                gbest_pos[i] += 1
                kalan_para -= urunler[i]['alis_fiyati']

        # Sonuçları hazırla
        sonuc_urunler = []
        toplam_alis = 0  # Bizim harcamamız (alış fiyatından)
        toplam_satis = 0  # Bizim gelir (satış fiyatından)

        for i, adet in enumerate(gbest_pos):
            if adet > 0:
                urun = urunler[i]
                alis_maliyet = adet * urun['alis_fiyati']  # Biz alış fiyatından alıyoruz
                satis_gelir = adet * urun['satis_fiyati']  # Biz satış fiyatından satıyoruz

                sonuc_urunler.append({
                    'urun_adi': urun['urun_adi'],
                    'adet': int(adet),
                    'birim_alis': urun['alis_fiyati'],  # Bizim alış fiyatımız
                    'birim_satis': urun['satis_fiyati'],  # Bizim satış fiyatımız
                    'alis_maliyet': alis_maliyet,
                    'satis_gelir': satis_gelir,
                    'komisyon_kaybi': alis_maliyet - satis_gelir,  # Pozitif olacak (komisyon kaybı)
                    'fark_yuzde': urun['fark_yuzde']
                })

                toplam_alis += alis_maliyet
                toplam_satis += satis_gelir

        return {
            'urunler': sonuc_urunler,
            'toplam_alis': toplam_alis,
            'toplam_satis': toplam_satis,
            'komisyon_kaybi': toplam_alis - toplam_satis,  # Pozitif = kayıp
            'kalan': maas - toplam_alis,
            'kullanim_orani': (toplam_alis / maas) * 100,
            'fitness_history': fitness_history
        }


def create_visual_report(sonuc, maas):
    """Basit görsel rapor"""
    plt.style.use('seaborn-v0_8-darkgrid')
    fig = plt.figure(figsize=(14, 8))
    fig.suptitle('ALTIN-GÜMÜŞ PORTFÖY OPTİMİZASYONU', fontsize=14, fontweight='bold')

    # 1. Fitness Grafiği
    ax1 = plt.subplot(2, 2, 1)
    ax1.plot(sonuc['fitness_history'], linewidth=2, color='#2E86AB')
    ax1.set_title('PSO Fitness Evrimi', fontweight='bold')
    ax1.set_xlabel('İterasyon')
    ax1.set_ylabel('Fitness')
    ax1.grid(True, alpha=0.3)

    # 2. Bütçe Kullanımı
    ax2 = plt.subplot(2, 2, 2)
    kategoriler = ['Kullanılan', 'Kalan']
    degerler = [sonuc['toplam_alis'], sonuc['kalan']]
    renkler = ['#06A77D', '#D62246']
    bars = ax2.bar(kategoriler, degerler, color=renkler, alpha=0.7, edgecolor='black')
    ax2.set_title('Bütçe Kullanımı', fontweight='bold')
    ax2.set_ylabel('Tutar (TL)')
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:,.0f} TL', ha='center', va='bottom', fontweight='bold')

    # 3. Komisyon Oranları + Adetler + Fiyatlar
    ax3 = plt.subplot(2, 2, 3)
    if sonuc['urunler']:
        urun_adlari = [f"{u['urun_adi'][:20]} (x{u['adet']})" for u in sonuc['urunler']]
        komisyonlar = [u['fark_yuzde'] for u in sonuc['urunler']]
        bars = ax3.barh(urun_adlari, komisyonlar, color='#F18F01', alpha=0.7)
        ax3.set_title('Komisyon Oranları, Adetler ve Fiyatlar', fontweight='bold')
        ax3.set_xlabel('Komisyon (%)')
        for i, bar in enumerate(bars):
            width = bar.get_width()
            urun = sonuc['urunler'][i]
            # Komisyon oranı ve birim alış fiyatı göster
            ax3.text(width, bar.get_y() + bar.get_height()/2.,
                    f'%{width:.2f} | {urun["birim_alis"]:.2f}₺', ha='left', va='center', fontsize=8)

    # 4. Özet + Ürün Detayları
    ax4 = plt.subplot(2, 2, 4)
    ax4.axis('off')

    komisyon_orani = abs(sonuc['komisyon_kaybi']/sonuc['toplam_alis']*100) if sonuc['toplam_alis'] > 0 else 0

    # Ürün detaylarını ekle
    urun_detaylari = ""
    if sonuc['urunler']:
        urun_detaylari = "\n    ALINAN ÜRÜNLER:\n"
        for u in sonuc['urunler'][:5]:  # İlk 5 ürünü göster
            urun_detaylari += f"    • {u['urun_adi'][:25]}\n"
            urun_detaylari += f"      {u['adet']}x{u['birim_alis']:.2f}₺ = {u['alis_maliyet']:.2f}₺\n"
        if len(sonuc['urunler']) > 5:
            urun_detaylari += f"    ... ve {len(sonuc['urunler']) - 5} ürün daha\n"

    ozet_text = f"""
    BUTCE: {maas:,.2f} TL
    
    TOPLAM ALIS: {sonuc['toplam_alis']:,.2f} TL
    TOPLAM SATIS: {sonuc['toplam_satis']:,.2f} TL
    
    KOMISYON KAYBI: {sonuc['komisyon_kaybi']:,.2f} TL
    ORT. KOMISYON: %{komisyon_orani:.2f}
    
    KALAN: {sonuc['kalan']:,.2f} TL
    KULLANIM: %{sonuc['kullanim_orani']:.2f}
    {urun_detaylari}
    """

    ax4.text(0.05, 0.5, ozet_text, fontsize=9,
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
             verticalalignment='center')
    ax4.set_title('Finansal Ozet ve Urun Detaylari', fontweight='bold')

    plt.tight_layout()

    plt.show()


def main():
    """Ana program akışı"""
    print("=" * 10)
    print("ALTIN-GÜMÜŞ PORTFÖY OPTİMİZASYONU (PSO)")
    print("=" * 10)

    # 1. Fiyatları çek
    print("\nMayda.com'dan fiyatlar çekiliyor...")
    mayda_data = get_mayda_prices()

    print("Borsa İstanbul'dan gümüş fiyatı çekiliyor...")
    borsa_data = get_borsa_silver_price()

    if not mayda_data:
        print("Mayda.com'dan veri çekilemedi!")
        return

    # 2. Tüm ürünleri birleştir ve komisyona göre sırala
    tum_urunler = mayda_data['urunler'].copy()
    if borsa_data:
        tum_urunler.append(borsa_data['urun'])

    tum_urunler.sort(key=lambda x: x['fark_yuzde'])

    print(f"\n{len(tum_urunler)} ürün bulundu")

    # 3. Kullanıcı girdisi
    print("\n" + "=" * 10)
    try:
        maas = float(input("Bütçeniz (TL): "))
        if maas <= 0:
            print("Bütçe pozitif olmalı!")
            return
    except ValueError:
        print("Geçersiz giriş!")
        return

    # 4. PSO Optimizasyon
    print("\nPSO ile optimizasyon yapılıyor...")
    pso = ProductBasedPSO(n_particles=50, n_iterations=100, w=0.7, c1=1.5, c2=1.5)
    sonuc = pso.optimize(tum_urunler, maas)

    # 5. Konsol Çıktısı
    print("\n" + "=" * 10)
    print("OPTİMİZASYON SONUÇLARI")
    print("=" * 10)

    print(f"\nTarih: {mayda_data['tarih']}")
    print(f"Bütçe: {maas:,.2f} TL")

    print(f"\nÖNERİLEN PORTFÖY:")
    for urun in sonuc['urunler']:
        print(f"•{urun['urun_adi']}")
        print(f"Adet: {urun['adet']} | Alış: {urun['alis_maliyet']:,.2f} TL | Komisyon: %{urun['fark_yuzde']:.2f}")

    print(f"\nÖZET:")
    print(f"Toplam Alış: {sonuc['toplam_alis']:,.2f} TL")
    print(f"Komisyon Kaybı: {sonuc['komisyon_kaybi']:,.2f} TL")
    print(f"Kullanım: %{sonuc['kullanim_orani']:.2f}")
    print(f"Kalan: {sonuc['kalan']:,.2f} TL")

    if sonuc['toplam_alis'] > 0:
        komisyon_orani = abs(sonuc['komisyon_kaybi'] / sonuc['toplam_alis']) * 100
        print(f"Ortalama Komisyon: %{komisyon_orani:.2f}")

    # 6. Görsel Rapor
    print("\nGörsel rapor oluşturuluyor...")
    create_visual_report(sonuc, maas)

    print("\nİşlem tamamlandı!")


if __name__ == "__main__":
    main()

