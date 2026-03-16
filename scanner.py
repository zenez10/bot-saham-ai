import yfinance as yf
import pandas as pd
import requests
import os
import time
from datetime import datetime

# Ambil konfigurasi dari GitHub Secrets
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# DAFTAR 30 SAHAM LQ45 PALING AKTIF
watchlist_lq45 = [
    'ADRO.JK', 'AMMN.JK', 'AMRT.JK', 'ASII.JK', 'BBCA.JK', 'BBNI.JK', 'BBRI.JK', 'BBTN.JK',
    'BMRI.JK', 'BRIS.JK', 'BRPT.JK', 'CPIN.JK', 'GOTO.JK', 'HRUM.JK', 'ICBP.JK',
    'INCO.JK', 'INDF.JK', 'INKP.JK', 'ITMG.JK', 'KLBF.JK', 'MDKA.JK', 'MEDC.JK', 
    'MBMA.JK', 'PGAS.JK', 'PTBA.JK', 'SMGR.JK', 'TLKM.JK', 'TPIA.JK', 'UNTR.JK', 'UNVR.JK'
]

def kirim_telegram(pesan):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': pesan, 'parse_mode': 'Markdown'}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Gagal kirim Telegram: {e}")

def get_kondisi_ihsg():
    try:
        ihsg = yf.Ticker("^JKSE")
        h = ihsg.history(period="2d")
        last_close = h['Close'].iloc[-1]
        prev_close = h['Close'].iloc[-2]
        perubahan = ((last_close - prev_close) / prev_close) * 100
        status = "🟢 BULLISH" if perubahan > 0 else "🔴 BEARISH"
        return f"{status} ({perubahan:.2f}%)"
    except:
        return "⚪ TIDAK TERDETEKSI"

def analisa_sentimen(berita_list):
    if not berita_list:
        return "⚪ NETRAL (No News)"
    # Keyword Indonesia & Inggris (karena Yahoo sering campur)
    pos = ['laba', 'naik', 'untung', 'dividen', 'ekspansi', 'akuisisi', 'positif', 'rekor', 'profit', 'growth', 'buyback']
    neg = ['rugi', 'turun', 'anjlok', 'sengketa', 'denda', 'kasus', 'negatif', 'suspensi', 'loss', 'lawsuit', 'debt']
    skor = 0
    for n in berita_list:
        txt = n['title'].lower()
        skor += sum(1 for p in pos if p in txt)
        skor -= sum(1 for n_ in neg if n_ in txt)
    return f"🟢 BULLISH (Score: {skor})" if skor > 0 else (f"🔴 BEARISH (Score: {skor})" if skor < 0 else "⚪ NETRAL")

def cari_bintang_kemarin():
    bintang = []
    print("Menganalisis performa perdagangan kemarin...")
    for kode in watchlist_lq45:
        try:
            h = yf.Ticker(kode).history(period="5d")
            if len(h) < 3: continue
            # Perubahan harga hari terakhir yg sudah tutup (iloc[-2])
            chg = ((h['Close'].iloc[-2] - h['Close'].iloc[-3]) / h['Close'].iloc[-3]) * 100
            # Kriteria: Naik > 1.5% dan Volume > rata-rata 5 hari
            if chg > 1.5 and h['Volume'].iloc[-2] > h['Volume'].mean():
                bintang.append(kode)
        except: continue
    return bintang

def monitor():
    # --- LAPORAN PEMBUKAAN ---
    ihsg_info = get_kondisi_ihsg()
    saham_pantauan = cari_bintang_kemarin()
    
    msg_laporan = f"☀️ *MARKET PREPARATION REPORT*\n"
    msg_laporan += f"📅 Tanggal: {datetime.now().strftime('%d %b %Y')}\n"
    msg_laporan += f"──────────────────\n"
    msg_laporan += f"📈 *KONDISI IHSG:* {ihsg_info}\n\n"
    
    if not saham_pantauan:
        msg_laporan += "🔍 *ANALISA SAHAM:* \n"
        msg_laporan += "Tidak ditemukan saham bintang kemarin.\n"
        msg_laporan += "💡 *Saran:* Market sepi. 'Wait & See'.\n"
        saham_pantauan = ['BBCA.JK', 'BBRI.JK', 'BMRI.JK', 'TLKM.JK', 'ASII.JK']
    else:
        msg_laporan += "🎯 *TARGET MOMENTUM HARI INI:*\n"
        for s in saham_pantauan:
            msg_laporan += f"• `{s}`\n"
        msg_laporan += f"\n💡 *Saran:* Pantau konfirmasi beli."
    
    msg_laporan += f"\n──────────────────\n"
    msg_laporan += "🤖 *Status:* Monitoring Real-time Aktif..."
    kirim_telegram(msg_laporan)
    
    # --- LOOPING MONITORING REAL-TIME ---
    while True:
        # Stop jika sudah lewat jam 16:00 WIB (09:00 UTC)
        if datetime.utcnow().hour >= 9:
            kirim_telegram("🏁 *JAM BURSA BERAKHIR.* Sampai jumpa besok!")
            break

        try:
            # Load History
            try: df = pd.read_csv('history.csv')
            except: df = pd.DataFrame(columns=['kode', 't
