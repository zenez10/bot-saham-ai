import yfinance as yf
import pandas as pd
import requests
import os

# Mengambil data rahasia dari sistem
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Daftar 20 Saham Pilihan (Bisa Anda tambah/kurangi sendiri nanti)
daftar_saham = [
    'BBCA.JK', 'BBRI.JK', 'BMRI.JK', 'TLKM.JK', 'ASII.JK', 'GOTO.JK', 
    'BBNI.JK', 'UNTR.JK', 'ADRO.JK', 'ANTM.JK', 'PGAS.JK', 'MDKA.JK', 
    'ICBP.JK', 'AMRT.JK', 'KLBF.JK', 'PTBA.JK', 'ITMG.JK', 'BRIS.JK', 
    'CPIN.JK', 'UNVR.JK'
]

def kirim_telegram(pesan):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': pesan, 'parse_mode': 'Markdown'}
    requests.post(url, data=payload)

def scan():
    sinyal_ditemukan = False
    for kode in daftar_saham:
        try:
            s = yf.Ticker(kode)
            h = s.history(period="14d")
            if len(h) < 5: continue

            harga_skrg = h['Close'].iloc[-1]
            vol_skrg = h['Volume'].iloc[-1]
            vol_rata = h['Volume'].mean()
            perubahan = ((harga_skrg - h['Close'].iloc[-2]) / h['Close'].iloc[-2]) * 100

            # FILTER: Harga naik > 0.5% DAN Volume di atas rata-rata (Uang Besar Masuk)
            if perubahan > 0.5 and vol_skrg > vol_rata:
                sinyal_ditemukan = True
                sl = harga_skrg * 0.975 # Stop Loss 2.5%
                tp = harga_skrg * 1.075 # Take Profit 7.5% (Ratio 1:3)

                txt = f"🚀 *SINYAL: {kode}*\n"
                txt += f"💰 Harga: Rp {harga_skrg:,.0f} ({perubahan:.2f}%)\n"
                txt += f"🎯 *Target Profit: Rp {tp:,.0f}*\n"
                txt += f"🛡️ *Stop Loss: Rp {sl:,.0f}*\n\n"
                
                # Menambah Berita Seminggu Terakhir
                berita = s.news
                if berita:
                    txt += "📰 *Berita Terkait (Konteks):*\n"
                    for n in berita[:2]: # Ambil 2 berita teratas
                        txt += f"• {n['title']}\n"
                
                txt += "\n----------------------------"
                kirim_telegram(txt)
        except: continue

    if not sinyal_ditemukan:
        kirim_telegram("😴 Belum ada saham yang memenuhi kriteria 'Sangat Layak' hari ini.")

if __name__ == "__main__":
    scan()
