import yfinance as yf
import pandas as pd
import requests
import os
import time
from datetime import datetime, timedelta

# Konfigurasi Bot
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

watchlist_lq45 = [
    'ADRO.JK', 'AMMN.JK', 'AMRT.JK', 'ASII.JK', 'BBCA.JK', 'BBNI.JK', 'BBRI.JK', 'BBTN.JK',
    'BMRI.JK', 'BRIS.JK', 'BRPT.JK', 'CPIN.JK', 'GOTO.JK', 'HRUM.JK', 'ICBP.JK',
    'INCO.JK', 'INDF.JK', 'INKP.JK', 'ITMG.JK', 'KLBF.JK', 'MDKA.JK', 'MEDC.JK', 
    'MBMA.JK', 'PGAS.JK', 'PTBA.JK', 'SMGR.JK', 'TLKM.JK', 'TPIA.JK', 'UNTR.JK', 'UNVR.JK'
]

def kirim_telegram(pesan):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': pesan, 'parse_mode': 'Markdown', 'disable_web_page_preview': True}
    try: requests.post(url, data=payload)
    except: print("Gagal kirim Telegram")

def get_kondisi_ihsg():
    try:
        ihsg = yf.Ticker("^JKSE")
        h = ihsg.history(period="2d")
        perubahan = ((h['Close'].iloc[-1] - h['Close'].iloc[-2]) / h['Close'].iloc[-2]) * 100
        status = "🟢 BULLISH" if perubahan > 0 else "🔴 BEARISH"
        return f"{status} ({perubahan:.2f}%)", ihsg.news[:5]
    except: return "⚪ TIDAK TERDETEKSI", []

def analisa_sentimen(berita_list):
    if not berita_list: return "⚪ NETRAL"
    pos = ['laba', 'naik', 'untung', 'dividen', 'ekspansi', 'akuisisi', 'positif', 'rekor', 'profit']
    neg = ['rugi', 'turun', 'anjlok', 'sengketa', 'denda', 'kasus', 'negatif', 'suspensi']
    skor = 0
    for n in berita_list:
        txt = n.get('title', '').lower()
        skor += sum(1 for p in pos if p in txt)
        skor -= sum(1 for n_ in neg if n_ in txt)
    return f"🟢 BULLISH (Score: {skor})" if skor > 0 else (f"🔴 BEARISH (Score: {skor})" if skor < 0 else "⚪ NETRAL")

def cari_bintang_kemarin():
    bintang = []
    for kode in watchlist_lq45:
        try:
            h = yf.Ticker(kode).history(period="5d")
            if len(h) < 3: continue
            chg = ((h['Close'].iloc[-2] - h['Close'].iloc[-3]) / h['Close'].iloc[-3]) * 100
            if chg > 1.5 and h['Volume'].iloc[-2] > h['Volume'].mean():
                bintang.append(kode)
        except: continue
    return bintang

def buat_rekap_mingguan():
    try:
        df = pd.read_csv('history.csv')
        tgl_batas = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        df_week = df[df['tgl_sinyal'] >= tgl_batas]
        p = len(df_week[df_week['status'] == 'PROFIT'])
        l = len(df_week[df_week['status'] == 'LOSS'])
        wr = (p / (p + l) * 100) if (p + l) > 0 else 0
        return f"📊 *REKAP MINGGUAN*\n✅ Profit: {p} | ❌ Loss: {l}\n📈 *Win Rate: {wr:.1f}%*"
    except: return "Belum ada data rekap."

def monitor():
    wib_now = datetime.utcnow() + timedelta(hours=7)
    ihsg_info, berita_ihsg = get_kondisi_ihsg()
    saham_pantauan = cari_bintang_kemarin()
    
    # --- LAPORAN PEMBUKAAN ---
    msg = f"☀️ *MARKET PREPARATION REPORT*\n📅 {wib_now.strftime('%d %b %Y')}\n"
    msg += f"──────────────────\n📈 IHSG: *{ihsg_info}*\n\n"
    
    if berita_ihsg:
        msg += "📰 *BERITA TERKINI:*\n"
        for i, b in enumerate(berita_ihsg):
            judul = b.get('title', 'Berita Saham').replace('[','').replace(']','').replace('*','')
            link = b.get('link') or (b.get('content', {}).get('clickThroughUrl', {}).get('url'))
            if link:
                # Format Baru: Judul di atas, link di bawah
                msg += f"{i+1}. *{judul}*\n🔗 [Klik Berita]({link})\n\n"
        msg += "──────────────────\n"

    if not saham_pantauan:
        msg += "🔍 *ANALISA:* Tidak ada saham bintang. Pantau Big Caps utama."
        saham_pantauan = ['BBCA.JK', 'BBRI.JK', 'BMRI.JK', 'TLKM.JK']
    else:
        msg += f"🎯 *TARGET:* `{', '.join(saham_pantauan)}`"
    
    kirim_telegram(msg)

    while True:
        now_wib = datetime.utcnow() + timedelta(hours=7)
        if now_wib.hour >= 16:
            if now_wib.weekday() == 4: kirim_telegram(buat_rekap_mingguan())
            kirim_telegram("🏁 *JAM BURSA BERAKHIR.*")
            break

        try:
            if os.path.exists('history.csv'): df = pd.read_csv('history.csv')
            else: df = pd.DataFrame(columns=['kode', 'tgl_sinyal', 'harga_beli', 'tp', 'sl', 'status'])

            for kode in saham_pantauan:
                s = yf.Ticker(kode)
                h = s.history(period="1d", interval="1m")
                if h.empty: continue
                hrg, op = h['Close'].iloc[-1], h['Open'].iloc[0]
                tgl = now_wib.strftime('%Y-%m-%d')

                # Cek TP/SL
                active_trades = df[(df['kode'] == kode) & (df['status'] == 'OPEN')]
                for idx, row in active_trades.iterrows():
                    if hrg >= row['tp']:
                        df.at[idx, 'status'] = 'PROFIT'
                        kirim_telegram(f"✅ *TP HIT:* {kode} @ {hrg:,.0f}")
                        df.to_csv('history.csv', index=False)
                    elif hrg <= row['sl']:
                        df.at[idx, 'status'] = 'LOSS'
                        kirim_telegram(f"❌ *SL HIT:* {kode} @ {hrg:,.0f}")
                        df.to_csv('history.csv', index=False)

                # Cek Beli
                if df[(df['kode'] == kode) & (df['tgl_sinyal'] == tgl)].empty:
                    if ((hrg - op) / op) * 100 > 0.5:
                        sent = analisa_sentimen(s.news)
                        tp, sl = hrg * 1.075, hrg * 0.975
                        new_row = pd.DataFrame([{'kode': kode, 'tgl_sinyal': tgl, 'harga_beli': hrg, 'tp': tp, 'sl': sl, 'status': 'OPEN'}])
                        df = pd.concat([df, new_row], ignore_index=True)
                        df.to_csv('history.csv', index=False)
                        kirim_telegram(f"🚀 *BUY:* {kode} @ {hrg:,.0f}\n🧠 {sent}\n🎯 TP: {tp:,.0f} | SL: {sl:,.0f}")
            time.sleep(60)
        except: time.sleep(30)

if __name__ == "__main__":
    monitor()
