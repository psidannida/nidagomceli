import streamlit as st
import pandas as pd
import json
import os
import urllib.parse
from datetime import datetime
import plotly.express as px

# --- 1. VERİ YÖNETİMİ (Tek Dosya Çözümü) ---
VERI_DOSYASI = "nida_akademi_data.json"

def veri_yukle():
    if os.path.exists(VERI_DOSYASI):
        try:
            with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {"ogrenciler": {}}
    return {"ogrenciler": {}}

def veri_kaydet(veri):
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)

if 'db' not in st.session_state:
    st.session_state.db = veri_yukle()

# --- 2. TAM MÜFREDAT LİSTESİ ---
mufredat_yks = {
    "TYT Matematik": ["Temel Kavramlar", "Sayılar", "Bölünebilme", "Problemler", "Mantık", "Fonksiyonlar", "Veri"],
    "AYT Matematik": ["Trigonometri", "Logaritma", "Diziler", "Limit", "Türev", "İntegral", "Polinomlar"],
    "YKS Fen": ["Fizik", "Kimya", "Biyoloji"],
    "YKS Edebiyat-Sosyal": ["Edebiyat", "Tarih", "Coğrafya", "Felsefe", "Din Kültürü"]
}

mufredat_lgs = {
    "LGS Matematik": ["Çarpanlar ve Katlar", "Üslü İfadeler", "Kareköklü İfadeler", "Veri Analizi", "Olasılık", "Cebirsel İfadeler"],
    "LGS Fen": ["Mevsimler", "DNA", "Basınç", "Madde", "Basit Makineler", "Enerji"],
    "LGS Türkçe": ["Fiilimsiler", "Sözcük-Cümle-Paragraf", "Cümlenin Ögeleri", "Yazım-Noktalama"]
}

# --- 3. TASARIM ---
st.set_page_config(page_title="Nida GÖMCELİ Akademi", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #05070a; color: white; }
    .header { text-align: center; padding: 20px; border: 2px solid #00d4ff; border-radius: 15px; background: #11141b; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="header"><h1>🛡️ Nida GÖMCELİ Akademi</h1><p>Hepsi Bir Arada Koçluk Sistemi</p></div>', unsafe_allow_html=True)

# --- 4. GİRİŞ KONTROLÜ ---
if "logged_in" not in st.session_state:
    tab_login, tab_setup = st.tabs(["🔐 Giriş Yap", "🆕 İlk Kez Şifre Oluştur"])
    
    with tab_login:
        user = st.text_input("Ad Soyad (Sistemdeki)")
        pw = st.text_input("Şifre", type="password")
        if st.button("Giriş"):
            if user == "admin" and pw == "nida2024":
                st.session_state.update({"logged_in": True, "role": "admin"})
                st.rerun()
            elif user in st.session_state.db["ogrenciler"]:
                if st.session_state.db["ogrenciler"][user].get("sifre") == pw:
                    st.session_state.update({"logged_in": True, "role": "ogrenci", "user": user})
                    st.rerun()
                else: st.error("Hatalı şifre!")
            else: st.error("Kullanıcı bulunamadı!")

    with tab_setup:
        st.info("Hocanız isminizi eklediyse buradan şifrenizi belirleyebilirsiniz.")
        s_user = st.text_input("Kayıtlı Ad Soyadınız")
        s_pw = st.text_input("Yeni Şifre", type="password")
        if st.button("Şifremi Belirle"):
            if s_user in st.session_state.db["ogrenciler"]:
                st.session_state.db["ogrenciler"][s_user]["sifre"] = s_pw
                veri_kaydet(st.session_state.db)
                st.success("Şifre kaydedildi! Giriş yapabilirsiniz.")
            else: st.error("İsminiz sistemde yok, önce hocanız eklemeli.")

else:
    # --- 5. ADMIN PANELİ ---
    if st.session_state["role"] == "admin":
        st.sidebar.title("Yönetici Paneli")
        if st.sidebar.button("Güvenli Çıkış"): del st.session_state["logged_in"]; st.rerun()

        menu = st.sidebar.radio("İşlem Seçin", ["Öğrenci Kaydı", "Gelişim Takibi", "Veri Yedekleme"])

        if menu == "Öğrenci Kaydı":
            st.subheader("👤 Yeni Öğrenci Ekle")
            n = st.text_input("Öğrenci Ad Soyad")
            g = st.selectbox("Sınav Grubu", ["LGS", "YKS"])
            t = st.text_input("Veli Telefon (905...)")
            h = st.number_input("Haftalık Soru Hedefi", 100, 5000, 500)
            if st.button("Kaydet"):
                st.session_state.db["ogrenciler"][n] = {"soru_takip": [], "denemeler": [], "tel": t, "sinav": g, "hedef": h, "sifre": None}
                veri_kaydet(st.session_state.db)
                st.success(f"{n} başarıyla eklendi!")

        elif menu == "Gelişim Takibi":
            if st.session_state.db["ogrenciler"]:
                secilen = st.selectbox("Öğrenci Seç", list(st.session_state.db["ogrenciler"].keys()))
                o = st.session_state.db["ogrenciler"][secilen]
                st.write(f"### {secilen} - ({o['sinav']})")
                
                # Soru Analizi
                if o["soru_takip"]:
                    df_s = pd.DataFrame(o["soru_takip"])
                    st.write("*Son Soru Girişleri*")
                    st.table(df_s.tail(5))
                
                # Deneme Analizi
                if o["denemeler"]:
                    df_d = pd.DataFrame(o["denemeler"])
                    st.write("*Deneme Netleri*")
                    st.table(df_d)
            else: st.warning("Henüz öğrenci eklenmemiş.")

        elif menu == "Veri Yedekleme":
            st.subheader("💾 Verileri Bilgisayara İndir")
            st.write("Streamlit geçici olduğu için haftalık olarak verileri indirip saklamanız önerilir.")
            if st.button("Tüm Veriyi Hazırla"):
                data_str = json.dumps(st.session_state.db, ensure_ascii=False, indent=4)
                st.download_button("Dosyayı İndir (.json)", data_str, "nida_akademi_yedek.json")

    # --- 6. ÖĞRENCİ PANELİ ---
    else:
        u = st.session_state["user"]
        o = st.session_state.db["ogrenciler"][u]
        m = mufredat_lgs if o["sinav"] == "LGS" else mufredat_yks
        
        st.sidebar.title(f"Hoş Geldin {u}")
        if st.sidebar.button("Çıkış"): del st.session_state["logged_in"]; st.rerun()

        tab1, tab2, tab3 = st.tabs(["📝 Soru Girişi", "📈 Deneme Analizi", "🎯 Hedef Çubuğu"])

        with tab1:
            st.subheader("Günlük Soru Takibi")
            ders = st.selectbox("Ders Seç", list(m.keys()))
            konu = st.selectbox("Konu Seç", m[ders])
            kaynak = st.text_input("Çözülen Kaynak")
            d, y = st.columns(2)
            dogru = d.number_input("Doğru Sayısı", 0)
            yanlis = y.number_input("Yanlış Sayısı", 0)
            if st.button("Kaydet"):
                o["soru_takip"].append({"Tarih": datetime.now().strftime("%d/%m/%Y"), "Ders": ders, "Konu": konu, "Kaynak": kaynak, "Doğru": dogru, "Yanlış": yanlis, "Toplam": dogru+yanlis})
                veri_kaydet(st.session_state.db); st.success("Veriler kaydedildi!")

        with tab2:
            st.subheader("Deneme Net Girişi")
            d_adi = st.text_input("Deneme Yayını")
            c1, c2, c3, c4 = st.columns(4)
            n_t = c1.number_input("Türkçe Net", 0.0)
            n_m = c2.number_input("Matematik Net", 0.0)
            n_s = c3.number_input("Sosyal Net", 0.0)
            n_f = c4.number_input("Fen Net", 0.0)
            h_konu = st.multiselect("Yanlış Yaptığın Konular", m[ders])
            if st.button("Deneme Kaydet"):
                o["denemeler"].append({"Tarih": datetime.now().strftime("%d/%m/%Y"), "Deneme": d_adi, "Toplam": n_t+n_m+n_s+n_f, "Hatalar": h_konu})
                veri_kaydet(st.session_state.db); st.balloons()

        with tab3:
            st.subheader("🎯 Haftalık Hedef Durumu")
            toplam = sum(item["Toplam"] for item in o["soru_takip"])
            yuzde = min(toplam / o["hedef"], 1.0)
            st.progress(yuzde)
            st.write(f"Hedef: {o['hedef']} | Çözülen: {toplam} | Kalan: {max(0, o['hedef']-toplam)}")