import yfinance as yf
import pandas as pd
import requests
import os

# Ambil data rahasia dari GitHub Secrets
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Daftar 20 Saham Pilihan
daftar_saham = [
    'BBCA.JK', 'BBRI.JK', 'BMRI.JK', 'TLKM.JK', 'ASII.JK', 'GOTO.JK', 
    'BBNI.JK', 'UNTR.JK', 'ADRO.JK', 'ANTM.JK', 'PGAS.JK', 'MDKA.JK', 
    'ICBP.JK', 'AMRT.JK', 'KLBF.JK', 'PTBA.JK', 'ITMG.JK', 'BRIS.JK', 
    'CPIN.JK', 'UNVR.JK'
]

def kirim_telegram(pesan):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': pesan, 'parse_mode': 'Markdown'}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Gagal kirim Telegram: {e}")

def scan():
    total_scan = len(daftar_saham)
    saham_lolos = 0
    
    print(f"Memulai pemindaian {total_scan} saham...")

    for kode in daftar_saham:
        try:
            s = yf.Ticker(kode)
            h = s.history(period="14d")
            if len(h) < 5: continue

            harga_skrg = h['Close'].iloc[-1]
            vol_skrg = h['Volume'].iloc[-1]
            vol_rata = h['Volume'].mean()
            perubahan = ((harga_skrg - h['Close'].iloc[-2]) / h['Close'].iloc[-2]) * 100

            # FILTER UTAMA: Harga Naik & Volume di atas rata-rata
            if perubahan > 0.5 and vol_skrg > vol_rata:
                saham_lolos += 1
                sl = harga_skrg * 0.975 # Stop Loss 2.5%
                tp = harga_skrg * 1.075 # Take Profit 7.5%

                txt = f"🚀 *SINYAL: {kode}*\n"
                txt += f"💰 Harga: Rp {harga_skrg:,.0f} ({perubahan:.2f}%)\n"
                txt += f"🎯 *Target Profit: Rp {tp:,.0f}*\n"
                txt += f"🛡️ *Stop Loss: Rp {sl:,.0f}*\n"
                txt += f"📊 Vol: {vol_skrg/vol_rata:.1f}x rata-rata\n\n"
                
                # Bagian Berita
                try:
                    berita = s.news
                    if berita and len(berita) > 0:
                        txt += "📰 *Berita Terkait:*\n"
                        for n in berita[:2]:
                            txt += f"• {n['title']}\n"
                    else:
                        txt += "📰 *Berita:* Tidak ada berita signifikan minggu ini.\n"
                except:
                    txt += "📰 *Berita:* Gagal memuat berita.\n"
                
                txt += "\n----------------------------"
                kirim_telegram(txt)
        except:
            continue

    # LAPORAN STATUS AKHIR
    summary = f"📊 *LAPORAN STATUS SCANNER*\n"
    summary += f"✅ Selesai memeriksa {total_scan} saham.\n"
    summary += f"📈 Sinyal ditemukan: {saham_lolos}\n"
    if saham_lolos == 0:
        summary += "\n😴 Pasar cenderung sepi, tidak ada saham yang masuk kriteria 'Sangat Layak' hari ini."
    
    kirim_telegram(summary)

if __name__ == "__main__":
    scan()
