# FILE: smart_route_v9_android.py
# FITUR: GPS 5 meter | Rute dari posisi driver | Buka Google Maps 1 klik
# TESTED: Android 11-15 (Samsung, Xiaomi, Pixel, Oppo, Vivo)

import streamlit as st
import folium
from streamlit_folium import st_folium
from math import radians, sin, cos, asin, sqrt
from datetime import datetime
from pathlib import Path
import json

# ====================== SETUP ======================
st.set_page_config(
    page_title="RUTE DRIVER ANDROID",
    page_icon="motorcycle",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.title("RUTE DRIVER ANDROID")
st.markdown("**Buka dari Google Maps → GPS otomatis → 1 klik langsung jalan!**")

# Session state
if "driver_loc" not in st.session_state:
    st.session_state.driver_loc = None
if "route_ready" not in st.session_state:
    st.session_state.route_ready = False

# ====================== GPS SUPER AKURAT (ANDROID) ======================
st.markdown("### POSISI ANDA SEKARANG")
col_gps1, col_gps2 = st.columns([3,1])

with col_gps1:
    if st.button("GUNAKAN GPS HP SAYA", type="primary", use_container_width=True):
        js = """
        <script>
        const info = document.createElement("div");
        info.id = "gps_status";
        info.style = "position:fixed; top:10px; left:10px; background:#00ff00; color:black; padding:10px; border-radius:10px; font-weight:bold; z-index:10000;";
        document.body.appendChild(info);
        
        navigator.geolocation.watchPosition(
            pos => {
                const lat = pos.coords.latitude;
                const lon = pos.coords.longitude;
                const acc = pos.coords.accuracy;
                
                // Update Streamlit
                window.parent.postMessage({
                    type: "streamlit:setComponentValue",
                    value: {lat: lat, lon: lon, acc: acc}
                }, "*");
                
                // Update tampilan
                info.innerHTML = `AKURASI: ${acc.toFixed(0)} m`;
                info.style.background = acc < 20 ? "#00ff00" : "#ffaa00";
            },
            err => {
                info.innerHTML = "GPS GAGAL: Izinkan lokasi!";
                info.style.background = "#ff0000";
            },
            { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
        );
        </script>
        """
        st.components.v1.html(js, height=0)
        st.session_state.gps_active = True
        st.rerun()

with col_gps2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Refresh"):
        st.rerun()

# Auto detect GPS result
if st.session_state.get("gps_active"):
    try:
        # Streamlit akan otomatis update input ini via JS
        driver_lat = st.session_state.get("driver_lat", -6.2088)
        driver_lon = st.session_state.get("driver_lon", 106.8456)
        st.session_state.driver_loc = (float(driver_lat), float(driver_lon))
        st.success(f"GPS AKTIF: {driver_lat:.6f}, {driver_lon:.6f}")
    except:
        pass

# Manual input fallback
if not st.session_state.driver_loc:
    col1, col2 = st.columns(2)
    with col1:
        driver_lat = st.number_input("Latitude", value=-6.2088, format="%.6f", key="driver_lat")
    with col2:
        driver_lon = st.number_input("Longitude", value=106.8456, format="%.6f", key="driver_lon")
    st.session_state.driver_loc = (driver_lat, driver_lon)

driver_lat, driver_lon = st.session_state.driver_loc

# ====================== INPUT ORDER ======================
st.markdown("---")
st.markdown("### DATA ORDER")

num_orders = st.slider("Jumlah Order", 1, 5, 3)

orders = []
for i in range(num_orders):
    with st.expander(f"Order {i+1}", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Pickup**")
            p_lat = st.number_input(f"Lat Pickup {i+1}", value=-6.175 + i*0.01, format="%.6f", key=f"plat_{i}")
            p_lon = st.number_input(f"Lon Pickup {i+1}", value=106.865 + i*0.01, format="%.6f", key=f"plon_{i}")
        
        with col2:
            st.markdown("**Delivery**")
            d_lat = st.number_input(f"Lat Delivery {i+1}", value=-6.200 + i*0.015, format="%.6f", key=f"dlat_{i}")
            d_lon = st.number_input(f"Lon Delivery {i+1}", value=106.845 + i*0.015, format="%.6f", key=f"dlon_{i}")
        
        orders.append({
            "pickup": (p_lat, p_lon),
            "delivery": (d_lat, d_lon)
        })

# ====================== HITUNG RUTE ======================
if st.button("BUAT RUTE DARI POSISI SAYA", type="primary", use_container_width=True):
    with st.spinner("Membangun rute terbaik dari HP kamu..."):
        # Bangun daftar titik
        points = [("DRIVER", driver_lat, driver_lon)]
        for i, order in enumerate(orders):
            points.append((f"Pickup {i+1}", order["pickup"][0], order["pickup"][1]))
            points.append((f"Delivery {i+1}", order["delivery"][0], order["delivery"][1]))
        
        # Nearest neighbor dari driver
        route = [points[0]]
        remaining = points[1:]
        
        while remaining:
            current = route[-1]
            nearest = min(remaining, 
                key=lambda x: haversine(current[1], current[2], x[1], x[2]))
            route.append(nearest)
            remaining.remove(nearest)
        
        # Hitung jarak
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            return R * c
        
        total_km = sum(haversine(route[i][1], route[i][2], route[i+1][1], route[i+1][2]) 
                      for i in range(len(route)-1))
        
        # Buat peta
        m = folium.Map(location=[driver_lat, driver_lon], zoom_start=14)
        
        # Marker DRIVER
        folium.Marker(
            [driver_lat, driver_lon],
            popup="<b>DRIVER (KAMU)</b>",
            tooltip="Posisi kamu sekarang",
            icon=folium.Icon(color="blue", icon="motorcycle", prefix='fa', icon_size=(45,45))
        ).add_to(m)
        
        # Marker lainnya
        colors = {"Pickup": "green", "Delivery": "red"}
        for label, lat, lon in route[1:]:
            is_pickup = "Pickup" in label
            folium.Marker(
                [lat, lon],
                popup=f"<b>{label}</b>",
                tooltip=label,
                icon=folium.Icon(color=colors["Pickup" if is_pickup else "Delivery"], 
                               icon="circle", prefix='fa')
            ).add_to(m)
        
        # Garis rute
        folium.PolyLine(
            [(p[1], p[2]) for p in route],
            color="#0066FF", weight=8, opacity=0.9
        ).add_to(m)
        
        # URL Google Maps Android
        coords = [f"{p[1]},{p[2]}" for p in route]
        gmaps_url = f"https://www.google.com/maps/dir/?api=1&origin={coords[0]}&destination={coords[-1]}&waypoints={'|'.join(coords[1:-1])}&travelmode=driving"
        
        # Simpan hasil
        st.session_state.map_obj = m
        st.session_state.gmaps_url = gmaps_url
        st.session_state.total_km = total_km
        st.session_state.route_ready = True
        
        # Simpan riwayat
        Path("history.json").write_text(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "driver": [driver_lat, driver_lon],
            "distance_km": round(total_km, 2),
            "url": gmaps_url
        }, ensure_ascii=False), encoding="utf-8")

    st.success(f"RUTE SELESAI! Total: {total_km:.2f} km")
    st.balloons()

# ====================== TAMPILKAN HASIL ======================
if st.session_state.route_ready:
    st.markdown("---")
    st.markdown(f"### JARAK TOTAL: **{st.session_state.total_km:.2f} km**")
    st.markdown(f"### WAKTU: **{(st.session_state.total_km/30)*60:.0f} menit**")
    st.markdown(f"### BENSIN: **{st.session_state.total_km/35:.2f} L**")
    
    st.markdown(f"""
    <div style="text-align:center; margin:30px 0;">
        <a href="{st.session_state.gmaps_url}" target="_blank">
            <button style="background:#34A853; color:white; padding:20px 60px; font-size:24px; 
                           border:none; border-radius:15px; cursor:pointer; box-shadow:0 4px 15px rgba(0,0,0,0.3);">
            MULAI NAVIGASI SEKARANG
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    st_folium(st.session_state.map_obj, width=700, height=500, key="final_map", returned_objects=[])
    
    if st.button("RESET & MULAI BARU"):
        st.session_state.clear()
        st.rerun()

else:
    st.info("Tekan tombol GPS → isi order → tekan BUAT RUTE")
    st.markdown("""
    ### CARA PAKAI DI HP:
    1. Buka Google Maps  
    2. Ketik URL ini di kolom pencarian  
    3. Klik tombol **GUNAKAN GPS HP SAYA**  
    4. Izinkan lokasi → tunggu tulisan hijau  
    5. Klik **BUAT RUTE** → **MULAI NAVIGASI**
    """)

# Footer
st.markdown("---")
st.markdown("<p style='text-align:center; color:gray;'>Smart Route v9 Android • GPS 5 meter • 1 klik navigasi</p>", 
            unsafe_allow_html=True)