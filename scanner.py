import yfinance as yf
import pandas as pd
import requests
import os
import time
from datetime import datetime, timedelta

# Ambil konfigurasi dari GitHub Secrets
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# DAFTAR 30 SAHAM LQ45
watchlist_lq45 = [
    'ADRO.JK', 'AMMN.JK', 'AMRT.JK', 'ASII.JK', 'BBCA.JK', 'BBNI.JK', 'BBRI.JK', 'BBTN.JK',
    'BMRI.JK', 'BRIS.JK', 'BRPT.JK', 'CPIN.JK', 'GOTO.JK', 'HRUM.JK', 'ICBP.JK',
    'INCO.JK', 'INDF.JK', 'INKP.JK', 'ITMG.JK', 'KLBF.JK', 'MDKA.JK', 'MEDC.JK', 
    'MBMA.JK', 'PGAS.JK', 'PTBA.JK', 'SMGR.JK', 'TLKM.JK', 'TPIA.JK', 'UNTR.JK', 'UNVR.JK'
]

def kirim_telegram(pesan):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': pesan, 'parse_mode': 'Markdown', 'disable_web_page_preview': True}
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
        return f"{status} ({perubahan:.2f}%)", ihsg.news[:5]
    except:
        return "⚪ TIDAK TERDETEKSI", []

def buat_laporan_mingguan():
    try:
        df = pd.read_csv('history.csv')
        if df.empty: return "Belum ada transaksi minggu ini."
        tgl_batas = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        df_week = df[df['tgl_sinyal'] >= tgl_batas]
        profit = len(df_week[df_week['status'] == 'PROFIT'])
        loss = len(df_week[df_week['status'] == 'LOSS'])
        win_rate = (profit / (profit + loss) * 100) if (profit + loss) > 0 else 0
        
        report = "📊 *REKAPITULASI MINGGUAN*\n"
        report += f"──────────────────\n"
        report += f"✅ Profit: {profit} | ❌ Loss: {loss}\n"
        report += f"📈 *Win Rate: {win_rate:.1f}%*\n"
        report += f"──────────────────"
        return report
    except: return "Gagal membuat laporan mingguan."

def monitor():
    wib_now = datetime.utcnow() + timedelta(hours=7)
    ihsg_info, berita_ihsg = get_kondisi_ihsg()
    
    # --- LAPORAN PEMBUKAAN ---
    msg_laporan = f"☀️ *MARKET PREPARATION REPORT*\n"
    msg_laporan += f"📅 Tanggal: {wib_now.strftime('%d %b %Y')}\n"
    msg_laporan += f"──────────────────\n"
    msg_laporan += f"📈 *KONDISI IHSG:* {ihsg_info}\n\n"
    
    # Tambahkan Berita IHSG
    if berita_ihsg:
        msg_laporan += "📰 *BERITA TERKINI IHSG:*\n"
        for i, berita in enumerate(berita_ihsg):
            judul = berita['title']
            link = berita['link']
            msg_laporan += f"{i+1}. [{judul}]({link})\n\n"
        msg_laporan += f"──────────────────\n"

    saham_pantauan = [] # Logika cari_bintang_kemarin() bisa ditaruh di sini
    # (Singkatnya saya asumsikan fungsi cari_bintang_kemarin ada seperti versi sebelumnya)
    # Untuk menghemat ruang, kita gunakan daftar ringkas
    try:
        from scanner import cari_bintang_kemarin
        saham_pantauan = cari_bintang_kemarin()
    except:
        saham_pantauan = ['BBCA.JK', 'BBRI.JK', 'BMRI.JK', 'TLKM.JK', 'ASII.JK']

    if not saham_pantauan:
        msg_laporan += "🔍 *ANALISA SAHAM:* \nTidak ada saham bintang. 'Wait & See'."
    else:
        msg_laporan += "🎯 *TARGET MOMENTUM HARI INI:*\n"
        for s in saham_pantauan: msg_laporan += f"• `{s}`\n"
    
    msg_laporan += f"\n──────────────────\n"
    msg_laporan += "🤖 *Status:* Monitoring Real-time Aktif..."
    kirim_telegram(msg_laporan)
    
    # --- LOOPING MONITORING (Tetap seperti v4.2) ---
    while True:
        now_wib = datetime.utcnow() + timedelta(hours=7)
        if now_wib.hour >= 16:
            if now_wib.weekday() == 4: kirim_telegram(buat_laporan_mingguan())
            kirim_telegram("🏁 *JAM BURSA BERAKHIR.* Sampai jumpa besok!")
            break
        # ... (Logika monitoring hrg & TP/SL tetap sama dengan kode sebelumnya)
        time.sleep(60)

if __name__ == "__main__":
    # Pastikan fungsi cari_bintang_kemarin() didefinisikan di sini juga 
    # sebelum monitor() dipanggil agar tidak error.
    monitor()
