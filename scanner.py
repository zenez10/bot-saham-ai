import yfinance as yf
import pandas as pd
import requests
import os

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

daftar_saham = ['BBCA.JK', 'BBRI.JK', 'BMRI.JK', 'TLKM.JK', 'ASII.JK', 'GOTO.JK', 'BBNI.JK', 'UNTR.JK', 'ADRO.JK', 'ANTM.JK', 'PGAS.JK', 'MDKA.JK', 'ICBP.JK', 'AMRT.JK', 'KLBF.JK', 'PTBA.JK', 'ITMG.JK', 'BRIS.JK', 'CPIN.JK', 'UNVR.JK']

def kirim_telegram(pesan):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': pesan}
    requests.post(url, data=payload)

def scan():
    saham_lolos = 0
    print("Memulai scan...")
    
    for kode in daftar_saham:
        try:
            s = yf.Ticker(kode)
            h = s.history(period="5d")
            if len(h) < 2: continue

            harga_skrg = h['Close'].iloc[-1]
            vol_skrg = h['Volume'].iloc[-1]
            vol_rata = h['Volume'].mean()
            perubahan = ((harga_skrg - h['Close'].iloc[-2]) / h['Close'].iloc[-2]) * 100

            if perubahan > 0.5 and vol_skrg > vol_rata:
                saham_lolos += 1
                sl = harga_skrg * 0.975
                tp = harga_skrg * 1.075
                
                txt = f"SINYAL: {kode}\nHarga: {harga_skrg:,.0f}\nTP: {tp:,.0f}\nSL: {sl:,.0f}\n"
                
                # Coba ambil berita simpel
                try:
                    news = s.news
                    if news:
                        txt += f"Berita: {news[0]['title']}"
                except:
                    pass
                
                kirim_telegram(txt)
        except:
            continue
            
    kirim_telegram(f"Scan selesai. Ditemukan {saham_lolos} saham.")

if __name__ == "__main__":
    scan()
