# ============================================================================
# SMART ROUTE v13 – DETAIL GILA-GILAAN! (FINAL ULTIMATE PRO)
# JUAN + GROK 4 – VERSI YANG BENER-BENER SELESAI!
# ============================================================================
import streamlit as st
#import folium
from streamlit_folium import st_folium
import json
import pandas as pd
import requests
import re
from datetime import datetime, timedelta
from math import radians, sin, cos, asin, sqrt

st.set_page_config(page_tit956239le="Smart Route v13 – DETAIL MAX!", layout="wide")
st.markdown("""
<style>
    .big-font {font-size:50px !important; font-weight:bold; color:#0066FF;}
    .green {color:#00AA00 !important;}
    .red {color:#FF3333 !important;}
    a[target="_blank"] {color:#34A853 !important; font-weight:bold;}
    .stButton>button {background:#34A853; color:white; font-size:18px; padding:15px;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="big-font">Smart Route v13</p>', unsafe_allow_html=True)
st.caption("Pickup Semua Dulu • DETAIL GILA-GILAAN • Copy ke WA • Pro Banget!")

# ============================================================================
# SESSION & STORAGE
# ============================================================================
if "result_data" not in st.session_state:
    st.session_state.result_data = None
if "driver_loc" not in st.session_state:
    st.session_state.driver_loc = None

STORAGE_KEY = "smart_route_v13_pro"
EXPIRY_HOURS = 2

def save_to_storage(data):
    expiry = (datetime.now() + timedelta(hours=EXPIRY_HOURS)).isoformat()
    js = f'''
    <script>
    localStorage.setItem("{STORAGE_KEY}", JSON.stringify({json.dumps({"data": data, "expiry": expiry})}));
    </script>
    '''
    st.components.v1.html(js, height=0)

def load_from_storage():
    js = f'''
    <script>
    const item = localStorage.getItem("{STORAGE_KEY}");
    if (item) {{
        const parsed = JSON.parse(item);
        if (new Date(parsed.expiry) > new Date()) {{
            window.parent.postMessage({{type: "LOADED_V13", data: parsed.data}}, "*");
        }} else {{
            localStorage.removeItem("{STORAGE_KEY}");
        }}
    }}
    </script>
    '''
    return st.components.v1.html(js, height=0)

def clear_storage():
    js = '<script>localStorage.removeItem("smart_route_v13_pro");</script>'
    st.components.v1.html(js, height=0)

load_from_storage()
if st.session_state.get("LOADED_V13"):
    loaded = st.session_state["LOADED_V13"]
    st.session_state.result_data = loaded.get("result_data")
    st.session_state.driver_loc = loaded.get("driver_loc")

# ============================================================================
# UTILITY
# ============================================================================
def extract_lat_lon(url):
    try:
        r = requests.get(url, allow_redirects=True, timeout=5)
        final = r.url
        m = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', final)
        if m: return float(m.group(1)), float(m.group(2))
        m2 = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', final)
        if m2: return float(m2.group(1)), float(m2.group(2))
        return None, None
    except: return None, None

def extract_address(url):
    try:
        r = requests.get(url, allow_redirects=True, timeout=5)
        title = re.search(r'<title>(.*?)</title>', r.text)
        if title:
            addr = title.group(1).replace(" - Google Maps", "").strip()
            return addr if "@" not in addr else "Lokasi dari Link"
        return "Alamat dari Link"
    except: return "Alamat dari Link"

def haversine(p1, p2):
    R = 6371
    lat1, lon1 = map(radians, p1)
    lat2, lon2 = map(radians, p2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 2 * R * asin(sqrt(a))

def gmaps_route(o_lat, o_lon, d_lat, d_lon):
    return f"https://www.google.com/maps/dir/?api=1&origin={o_lat},{o_lon}&destination={d_lat},{d_lon}&travelmode=driving"

# ============================================================================
# SIDEBAR
# ============================================================================
with st.sidebar:
    st.header("Posisi Driver")
    if st.button("Gunakan GPS", type="primary"):
        js = '''
        <script>
        navigator.geolocation.getCurrentPosition(
            pos => {
                const inputs = document.querySelectorAll('input[type="number"]');
                inputs[0].value = pos.coords.latitude;
                inputs[1].value = pos.coords.longitude;
                inputs.forEach(i => i.dispatchEvent(new Event('input', {bubbles: true})));
            },
            err => alert("GPS Gagal")
        );
        </script>
        '''
        st.components.v1.html(js, height=0)

    c1, c2 = st.columns(2)
    with c1: driver_lat = st.number_input("Lat", value=-6.2088, format="%.6f", key="dlat")
    with c2: driver_lon = st.number_input("Lon", value=106.8456, format="%.6f", key="dlon")
    driver_loc = (driver_lat, driver_lon)
    st.session_state.driver_loc = driver_loc
    st.divider()
    num_orders = st.number_input("Jumlah Order", 1, 6, 3, key="norder")

# ============================================================================
# INPUT ORDERS
# ============================================================================
orders = []
for i in range(num_orders):
    with st.expander(f"Order {i+1}", expanded=True):
        col1, col2 = st.columns(2)
        p_lat = p_lon = p_addr = d_lat = d_lon = d_addr = None

        with col1:
            st.subheader("Pickup")
            mode = st.radio("Pickup", ["Manual", "Link"], key=f"p{i}", horizontal=True)
            if mode == "Link":
                link = st.text_input("Link Pickup", key=f"plink{i}")
                if link:
                    lat, lon = extract_lat_lon(link)
                    addr = extract_address(link)
                    if lat:
                        st.success(f"{lat:.6f}, {lon:.6f}")
                        st.info(f"Alamat: {addr}")
                        p_lat, p_lon, p_addr = lat, lon, addr
            if not p_lat:
                p_lat = st.number_input("Lat P", format="%.6f", key=f"plat{i}", value=-6.175)
                p_lon = st.number_input("Lon P", format="%.6f", key=f"plon{i}", value=106.865)
                p_addr = st.text_input("Nama Pickup", key=f"pname{i}", placeholder="Toko Sembako")

        with col2:
            st.subheader("Delivery")
            mode = st.radio("Delivery", ["Manual", "Link"], key=f"d{i}", horizontal=True)
            if mode == "Link":
                link = st.text_input("Link Delivery", key=f"dlink{i}")
                if link:
                    lat, lon = extract_lat_lon(link)
                    addr = extract_address(link)
                    if lat:
                        st.success(f"{lat:.6f}, {lon:.6f}")
                        st.info(f"Alamat: {addr}")
                        d_lat, d_lon, d_addr = lat, lon, addr
            if not d_lat:
                d_lat = st.number_input("Lat D", format="%.6f", key=f"dlat{i}", value=-6.200)
                d_lon = st.number_input("Lon D", format="%.6f", key=f"dlon{i}", value=106.845)
                d_addr = st.text_input("Nama Delivery", key=f"dname{i}", placeholder="Rumah Pak Budi")

        if p_lat and d_lat:
            orders.append({
                "id": i+1,
                "pickup": (p_lat, p_lon),
                "pickup_addr": p_addr or f"Pickup {i+1}",
                "delivery": (d_lat, d_lon),
                "delivery_addr": d_addr or f"Delivery {i+1}"
            })

# ============================================================================
# HITUNG RUTE + DETAIL GILA
# ============================================================================
if st.button("HITUNG RUTE – DETAIL MAX!", type="primary", use_container_width=True):
    if not orders:
        st.error("Isi minimal 1 order!")
        st.stop()

    with st.spinner("Sedang hitung detail gila-gilaan..."):
        current = driver_loc
        pickup_seq = []
        remaining = orders.copy()

        while remaining:
            nearest = min(remaining, key=lambda o: haversine(current, o["pickup"]))
            pickup_seq.append(nearest)
            current = nearest["pickup"]
            remaining.remove(nearest)

        delivery_seq = sorted(orders, key=lambda o: haversine(current, o["delivery"]))

        trips = []
        total_km = total_min = total_fuel = total_cost = 0
        kumulatif_km = 0
        pos = driver_loc

        for o in pickup_seq:
            km = haversine(pos, o["pickup"])
            menit = int((km / 30) * 60)
            liter = round(km / 35, 2)
            biaya = int(liter * 13500)
            kumulatif_km += km
            total_min += menit
            total_fuel += liter
            total_cost += biaya

            url = gmaps_route(pos[0], pos[1], o["pickup"][0], o["pickup"][1])
            trips.append({
                "No": len(trips)+1,
                "Aksi": f"Pickup Order {o['id']}",
                "Alamat": o["pickup_addr"],
                "Jarak": km,
                "Menit": menit,
                "Liter": liter,
                "Biaya": biaya,
                "Kumulatif KM": round(kumulatif_km, 2),
                "URL": url,
                "Coord": o["pickup"],
                "Type": "pickup"
            })
            pos = o["pickup"]

        for o in delivery_seq:
            km = haversine(pos, o["delivery"])
            menit = int((km / 30) * 60)
            liter = round(km / 35, 2)
            biaya = int(liter * 13500)
            kumulatif_km += km
            total_min += menit
            total_fuel += liter
            total_cost += biaya

            url = gmaps_route(pos[0], pos[1], o["delivery"][0], o["delivery"][1])
            trips.append({
                "No": len(trips)+1,
                "Aksi": f"Delivery Order {o['id']}",
                "Alamat": o["delivery_addr"],
                "Jarak": km,
                "Menit": menit,
                "Liter": liter,
                "Biaya": biaya,
                "Kumulatif KM": round(kumulatif_km, 2),
                "URL": url,
                "Coord": o["delivery"],
                "Type": "delivery"
            })
            pos = o["delivery"]

        result = {
            "trips": trips,
            "totals": {
                "km": round(kumulatif_km, 2),
                "min": total_min,
                "fuel": round(total_fuel, 2),
                "cost": total_cost
            },
            "pickup_seq": pickup_seq,
            "delivery_seq": delivery_seq
        }

        st.session_state.result_data = result
        save_to_storage({"result_data": result, "driver_loc": driver_loc})
        st.balloons()
        st.success("SELESAI! DETAIL GILA-GILAAN SIAP!")

# ============================================================================
# TAMPILKAN HASIL – DETAIL MAX + COPY WA
# ============================================================================
if st.session_state.result_data:
    data = st.session_state.result_data
    trips = data["trips"]
    t = data["totals"]

    # METRICS BESAR
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("TOTAL JARAK", f"{t['km']} km", delta=None)
    with col2: st.metric("TOTAL WAKTU", f"{t['min']} menit", delta=None)
    with col3: st.metric("TOTAL BENSIN", f"{t['fuel']} L", delta=None)
    with col4: st.metric("TOTAL BIAYA", f"Rp {t['cost']:,.0f}", delta=None)

    st.markdown("### DETAIL PER TRIP – BISA DI-SORT & DI-SEARCH!")

    df = pd.DataFrame(trips)
    df = df[["No", "Aksi", "Alamat", "Jarak", "Menit", "Liter", "Biaya", "Kumulatif KM"]]
    df["Jarak"] = df["Jarak"].round(2)
    df["Biaya"] = df["Biaya"].astype(int).map("Rp {:,}".format)

    # TAMPILKAN TABEL INTERAKTIF
    st.dataframe(df, use_container_width=True, hide_index=True)

    # COPY KE WHATSAPP
    wa_text = "RUTE HARI INI:\n\n"
    for trip in trips:
        wa_text += f"{trip['No']}. {trip['Aksi']}\n   → {trip['Alamat']}\n   → {trip['Jarak']:.2f} km | {trip['Menit']} menit | Rp {trip['Biaya']:,.0f}\n\n"
    wa_text += f"TOTAL: {t['km']} km | {t['min']} menit | Rp {t['cost']:,.0f}"

    st.markdown("### COPY KE WHATSAPP")
    st.code(wa_text, language=None)
    st.markdown(f"[KIRIM KE WHATSAPP](https://wa.me/?text={requests.utils.quote(wa_text)})")

    # PETA
    m = folium.Map(location=driver_loc, zoom_start=12)
    folium.Marker(driver_loc, popup="DRIVER", icon=folium.Icon(color="blue", icon="motorcycle", prefix='fa')).add_to(m)
    route = [driver_loc]
    for trip in trips:
        folium.Marker(trip["Coord"], 
                     popup=f"<b>{trip['Aksi']}</b><br>{trip['Alamat']}<br><a href='{trip['URL']}' target='_blank'>Buka Maps</a>",
                     icon=folium.Icon(color="green" if trip["Type"]=="pickup" else "red", 
                                    icon="arrow-up" if trip["Type"]=="pickup" else "arrow-down", prefix='fa')).add_to(m)
        route.append(trip["Coord"])
    folium.PolyLine(route, color="#0066FF", weight=7).add_to(m)
    st_folium(m, width=1000, height=600)

    if st.button("CLEAR & MULAI BARU"):
        clear_storage()
        st.session_state.clear()
        st.rerun()

else:
    st.info("Isi data → Klik **HITUNG RUTE** → Dapatkan detail gila-gilaan + copy WA!")
    st.success("v13 SUDAH SEMPURNA – TIDAK ADA LAGI YANG KURANG!")
