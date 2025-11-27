import requests
import re
import os
import random
from datetime import datetime

# Rastgele bir User-Agent listesi ekleyerek sunucu engellemesini aşmaya çalışıyoruz
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 10; SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/120.0"
]

def get_session():
    """Rastgele User-Agent içeren bir requests session'ı döndürür."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    })
    return session

print("IPTV Tarama Başlatılıyor...")
session = get_session()

active_domain = None
REF_SITE = None
DEBUG_INFO = [] # Debug için bilgileri buraya kaydedeceğiz

# --- Adım 1: Aktif siteyi bul (Sadece orijinal ontvizle{i}.live formatı kullanılıyor) ---

for i in range(1, 100):
    if active_domain:
        break
    site = f"https://ontvizle{i}.live"
    
    try:
        # SSL doğrulamasını devre dışı bıraktık, bazı sunucu sorunlarını çözer
        # allow_redirects=True ile yönlendirmeleri takip et
        r = session.get(site, timeout=5, verify=False, allow_redirects=True)
        if r.status_code == 200 and len(r.text) > 500:
            active_domain = site
            REF_SITE = site
            DEBUG_INFO.append(f"SUCCESS: Aktif domain bulundu: {active_domain}")
            print(f"Aktif domain bulundu: {active_domain}")
            break
        else:
            DEBUG_INFO.append(f"FAIL: {site} - Status Code: {r.status_code}")

    except requests.exceptions.RequestException as e:
        DEBUG_INFO.append(f"ERROR: {site} - İstek Hatası: {type(e).__name__}")
        pass

if not active_domain:
    DEBUG_INFO.append("FINAL STATUS: Hiçbir aktif domain bulunamadı. Script sonlanıyor.")
    print("Hiçbir aktif domain bulunamadı. Sadece debug dosyası oluşturulacak.")
    # Dosya oluşturma adımına gitmeden önce aktif domainin bulunmadığını belirtiyoruz.
    
else:
    # --- Adım 2 ve sonrası: Aktif domain bulunduysa devam et ---
    
    # 2. Kaynak koddan yayın sunucusunu (stream domain) çek
    print("Kaynak kod taranıyor...")
    try:
        html = session.get(active_domain, timeout=10, verify=False).text
        all_m3u8 = re.findall(r'https?://[^\'" ]+\.m3u8', html)
    except Exception as e:
        DEBUG_INFO.append(f"ERROR: Kaynak kod tarama hatası: {e}")
        all_m3u8 = []

    if not all_m3u8:
        DEBUG_INFO.append("FINAL STATUS: M3U8 linki bulunamadı. Script sonlanıyor.")
    else:
        domains = list(set([link.split("/")[0] + "//" + link.split("/")[2] for link in all_m3u8]))
        DEBUG_INFO.append(f"Found Stream Domains: {domains}")
        print(f"Bulunan yayın sunucuları: {domains}")

        working_stream_domain = None
        test_headers = {
            "Referer": REF_SITE,
            "Origin": REF_SITE,
            "User-Agent": session.headers["User-Agent"] # Session'dan gelen User-Agent'ı kullan
        }

        # 3. Hangi yayın sunucusu çalışıyor test et
        print("Domainler test ediliyor...")
        for domain in domains:
            # S sport 1 test kanalı (705)
            test_url = f"{domain}/705/mono.m3u8" 
            try:
                r = session.get(test_url, headers=test_headers, timeout=5, verify=False)
                if r.status_code == 200 and ("#EXTM3U" in r.text or "EXT-X-STREAM-INF" in r.text):
                    working_stream_domain = domain
                    DEBUG_INFO.append(f"SUCCESS: AKTİF YAYIN SUNUCUSU: {domain}")
                    print(f"AKTİF YAYIN SUNUCUSU: {domain}")
                    break
                else:
                    DEBUG_INFO.append(f"FAIL: {domain} - Pasif. Status: {r.status_code}")
            except:
                DEBUG_INFO.append(f"ERROR: {domain} - Test Hatası")

        if working_stream_domain:
            # 4. Kanal Listesi ve M3U oluşturma
            channels = {
                701: "beIN SPORTS 1", 702: "beIN SPORTS 2", 703: "beIN SPORTS 3", 704: "beIN SPORTS 4",
                705: "beIN SPORTS 5", 706: "Tivibu Spor 1", 707: "Smart Spor", 708: "Tivibu Spor",
                709: "A Spor", 710: "Spor Smart 2", 711: "Tivibu Spor 2", 712: "Tivibu Spor 3",
                713: "Tivibu Spor 4", 715: "beIN SPORTS Max 2", 729: "S Sport", 730: "S Sport 2",
                734: "NBA TV", 736: "Eurosport 1", 737: "Eurosport 2",
                "tabii": "Tabii Spor", "tabii1": "Tabii Spor 1", "tabii2": "Tabii Spor 2", 
                "tabii3": "Tabii Spor 3", "tabii4": "Tabii Spor 4", "tabii5": "Tabii Spor 5", 
                "tabii6": "Tabii Spor 6"
            }
            
            print("Kanallar ekleniyor...")
            guncelleme_zamani = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            m3u = f"#EXTM3U\n#EXTINF:-1, Guncelleme: {guncelleme_zamani} - Aktif Domain: {REF_SITE}\n\n"

            for cid, name in channels.items():
                stream_url = f"{working_stream_domain}/{cid}/mono.m3u8"
                
                m3u += f'#EXTINF:-1 tvg-logo="https://i.hizliresim.com/ska5t9e.jpg" group-title="SPOR", {name}\n'
                m3u += f'#EXTVLCOPT:http-referrer={REF_SITE}\n'
                m3u += f'#EXTVLCOPT:http-origin={REF_SITE}\n'
                m3u += f'#EXTVLCOPT:http-user-agent={test_headers["User-Agent"]}\n'
                m3u += f'{stream_url}\n\n'

            file_name = "iptv_list.m3u"
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(m3u)

            print("M3U Dosyası Başarıyla Oluşturuldu!")
            DEBUG_INFO.append("SUCCESS: iptv_list.m3u dosyası oluşturuldu.")
        else:
            DEBUG_INFO.append("FINAL STATUS: Çalışan stream domaini bulunamadı. iptv_list.m3u oluşturulamadı.")


# --- Debug Dosyasını Her Zaman Oluşturma (Git'in kaydetme adımı için kritik) ---
debug_file_name = "debug_log.txt"
with open(debug_file_name, "w", encoding="utf-8") as f:
    f.write(f"--- Debug Log: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
    f.write(f"Current User-Agent: {session.headers['User-Agent']}\n\n")
    f.write("\n".join(DEBUG_INFO))
    
print(f"Debug dosyası oluşturuldu: {debug_file_name}")

print("İşlem Tamamlandı!")
