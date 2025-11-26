import requests
import re
import os
from datetime import datetime

print("IPTV Tarama Başlatılıyor...")

active_domain = None
REF_SITE = None

# 1. Adım: Aktif siteyi bul
for i in range(1, 100):
    test_site = f"https://ontvizle{i}.live"
    try:
        # Timeout süresini biraz kısalttık ki hızlı tarasın
        r = requests.get(test_site, timeout=3)
        if r.status_code == 200 and len(r.text) > 500:
            active_domain = test_site
            REF_SITE = test_site
            print(f"Aktif domain bulundu: {active_domain}")
            break
    except:
        pass

if not active_domain:
    print("Hiçbir aktif domain bulunamadı.")
    exit()

# 2. Adım: Kaynak koddan yayın sunucusunu (stream domain) çek
print("Kaynak kod taranıyor...")
try:
    html = requests.get(active_domain, timeout=10).text
    all_m3u8 = re.findall(r'https?://[^\'" ]+\.m3u8', html)
except Exception as e:
    print(f"Hata oluştu: {e}")
    exit()

if not all_m3u8:
    print("M3U8 linki bulunamadı.")
    exit()

# Domainleri temizle ve listele
domains = list(set([link.split("/")[0] + "//" + link.split("/")[2] for link in all_m3u8]))
print(f"Bulunan yayın sunucuları: {domains}")

working_stream_domain = None
test_headers = {
    "Referer": REF_SITE,
    "Origin": REF_SITE,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 3. Adım: Hangi yayın sunucusu çalışıyor test et
print("Domainler test ediliyor...")

for domain in domains:
    # Test için genellikle açık olan bir kanal ID'si veya yapısı denenir
    test_url = f"{domain}/705/mono.m3u8"
    try:
        r = requests.get(test_url, headers=test_headers, timeout=5)
        if r.status_code == 200 and ("#EXTM3U" in r.text or "EXT-X-STREAM-INF" in r.text):
            working_stream_domain = domain
            print(f"AKTİF YAYIN SUNUCUSU: {domain}")
            break
        else:
            print(f"Pasif: {domain}")
    except:
        print(f"Hata: {domain}")

if not working_stream_domain:
    print("Çalışan yayın sunucusu bulunamadı.")
    exit()

# 4. Adım: Kanal Listesi
channels = {
    701: "beIN SPORTS 1",
    702: "beIN SPORTS 2",
    703: "beIN SPORTS 3",
    704: "beIN SPORTS 4",
    705: "beIN SPORTS 5",
    706: "Tivibu Spor 1",
    707: "Smart Spor",
    708: "Tivibu Spor",
    709: "A Spor",
    710: "Spor Smart 2",
    711: "Tivibu Spor 2",
    712: "Tivibu Spor 3",
    713: "Tivibu Spor 4",
    715: "beIN SPORTS Max 2",
    729: "S Sport",
    730: "S Sport 2",
    734: "NBA TV",
    736: "Eurosport 1",
    737: "Eurosport 2",
    "tabii": "Tabii Spor",
    "tabii1": "Tabii Spor 1",
    "tabii2": "Tabii Spor 2", 
    "tabii3": "Tabii Spor 3",
    "tabii4": "Tabii Spor 4",
    "tabii5": "Tabii Spor 5",
    "tabii6": "Tabii Spor 6"
}

print("Kanallar ekleniyor...")

# Dosya başlığı ve tarih bilgisi
guncelleme_zamani = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
m3u = f"#EXTM3U\n#EXTINF:-1, Guncelleme: {guncelleme_zamani}\nhttps://raw.githubusercontent.com/github-logo.png\n\n"

for cid, name in channels.items():
    stream_url = f"{working_stream_domain}/{cid}/mono.m3u8"
    
    # Her kanalı tek tek kontrol etmek işlemi çok uzatabilir (github action süresi kısıtlıdır).
    # Bu yüzden direkt ekliyoruz, çalışmayanlar zaten TV'de açılmaz.
    # Ancak headerları linke gömmek (pipe yöntemi) VLC tabanlı oynatıcılar için gereklidir.
    
    m3u += f'#EXTINF:-1 tvg-logo="https://i.hizliresim.com/ska5t9e.jpg" group-title="SPOR", {name}\n'
    m3u += f'#EXTVLCOPT:http-referrer={REF_SITE}\n'
    m3u += f'#EXTVLCOPT:http-origin={REF_SITE}\n'
    m3u += f'#EXTVLCOPT:http-user-agent={test_headers["User-Agent"]}\n'
    m3u += f'{stream_url}\n\n'

file_name = "iptv_list.m3u"
with open(file_name, "w", encoding="utf-8") as f:
    f.write(m3u)

print("İşlem Tamamlandı!")
print(f"Dosya oluşturuldu: {file_name}")
