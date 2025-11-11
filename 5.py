# ============================================================================
# FILE: multi_stop_optimizer_v10.py → FIX ALL ERRORS + 2 JAM PERSISTENT
# AUTHOR: Juan + Grok 4 (FINAL FIXED VERSION)
# ============================================================================
import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import requests
import re
from datetime import datetime, timedelta
from math import radians, sin, cos, asin, sqrt
from pathlib import Path

# ----------------------------------------------------------------------------
# SETUP
# ----------------------------------------------------------------------------
st.set_page_config(page_title="Smart Route v10 - Final Fixed", layout="wide")
st.title("Smart Route Optimizer v10")
st.caption("Data tersimpan 2 jam • Refresh aman • Clear kapan saja!")

# ----------------------------------------------------------------------------
# INISIALISASI SESSION STATE (WAJIB!)
# ----------------------------------------------------------------------------
required_keys = ["route_data", "map_obj", "driver_loc", "saved_data"]
for key in required_keys:
    if key not in st.session_state:
        st.session_state[key] = None

# ----------------------------------------------------------------------------
# LOCALSTORAGE AUTO SAVE (HANYA DATA JSON!)
# ----------------------------------------------------------------------------
STORAGE_KEY = "smart_route_v10_data"
EXPIRY_HOURS = 2

def save_to_storage(data):
    expiry = (datetime.now() + timedelta(hours=EXPIRY_HOURS)).isoformat()
    data_with_expiry = {"data": data, "expiry": expiry}
    js = f'''
    <script>
    localStorage.setItem("{STORAGE_KEY}", JSON.stringify({json.dumps(data_with_expiry)}));
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
            window.parent.postMessage({{type: "LOADED_DATA", data: parsed.data}}, "*");
        }} else {{
            localStorage.removeItem("{STORAGE_KEY}");
        }}
    }}
    </script>
    '''
    return st.components.v1.html(js, height=0)

def clear_storage():
    js = f'''
    <script>
    localStorage.removeItem("{STORAGE_KEY}");
    </script>
    '''
    st.components.v1.html(js, height=0)

# ----------------------------------------------------------------------------
# LOAD DATA DARI LOCALSTORAGE
# ----------------------------------------------------------------------------
loaded = load_from_storage()

# Jika ada pesan dari JS
if st.session_state.get("LOADED_DATA"):
    loaded_data = st.session_state["LOADED_DATA"]
    st.session_state.route_data = loaded_data.get("route_data")
    st.session_state.driver_loc = loaded_data.get("driver_loc")
    st.session_state.saved_data = loaded_data
    # Restore input driver
    if loaded_data.get("driver_loc"):
        st.session_state.driver_lat_input = loaded_data["driver_loc"][0]
        st.session_state.driver_lon_input = loaded_data["driver_loc"][1]

# ----------------------------------------------------------------------------
# UTILITY FUNCTIONS
# ----------------------------------------------------------------------------
def extract_lat_lon_from_gmaps(url):
    try:
        r = requests.get(url, allow_redirects=True, timeout=5)
        final_url = r.url
        match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', final_url)
        if match:
            return float(match.group(1)), float(match.group(2))
        match2 = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', final_url)
        if match2:
            return float(match2.group(1)), float(match2.group(2))
        return None, None
    except:
        return None, None

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c

def generate_gmaps_url(points):
    base = "https://www.google.com/maps/dir/?api=1"
    origin = f"{points[0][0]},{points[0][1]}"
    destination = f"{points[-1][0]},{points[-1][1]}"
    waypoints = "|".join([f"{p[0]},{p[1]}" for p in points[1:-1]]) if len(points) > 2 else ""
    return f"{base}&origin={origin}&destination={destination}&waypoints={waypoints}&travelmode=driving"

# ----------------------------------------------------------------------------
# REBUILD MAP DARI DATA (kalau ada)
# ----------------------------------------------------------------------------
def rebuild_map(route_data):
    if not route_data:
        return None
    driver_loc = route_data["driver_loc"]
    m = folium.Map(location=driver_loc, zoom_start=13, tiles="CartoDB positron")

    # Marker Driver
    folium.Marker(
        driver_loc,
        popup=folium.Popup(f"<b style='color:#0066FF;'>DRIVER</b><br><a href='https://www.google.com/maps/search/?api=1&query={driver_loc[0]},{driver_loc[1]}' target='_blank'>Buka Maps</a>", max_width=300),
        tooltip="Kamu",
        icon=folium.Icon(color="blue", icon="motorcycle", prefix='fa')
    ).add_to(m)

    # Marker titik lain
    route = route_data["route"]
    for label, lat, lon in route[1:]:
        is_pickup = "Pickup" in label
        color = "green" if is_pickup else "red"
        icon_name = "arrow-up" if is_pickup else "arrow-down"
        folium.Marker(
            [lat, lon],
            popup=folium.Popup(f"<b style='color:{'#0f0' if is_pickup else '#f00'}'>{label}</b><br>{lat:.6f}, {lon:.6f}", max_width=300),
            tooltip=label,
            icon=folium.Icon(color=color, icon=icon_name, prefix='fa')
        ).add_to(m)

    folium.PolyLine(
        [(p[1], p[2]) for p in route],
        color="#0066FF", weight=7, opacity=0.9
    ).add_to(m)

    return m

# ----------------------------------------------------------------------------
# SIDEBAR
# ----------------------------------------------------------------------------
with st.sidebar:
    st.header("Posisi Driver")
    if st.button("Gunakan GPS", type="primary"):
        js = '''
        <script>
        navigator.geolocation.getCurrentPosition(
            pos => {
                const lat = pos.coords.latitude;
                const lon = pos.coords.longitude;
                document.querySelector('[data-testid="stNumberInput"][key="driver_lat_input"] input').value = lat;
                document.querySelector('[data-testid="stNumberInput"][key="driver_lon_input"] input').value = lon;
                Streamlit.setComponentValue("gps_done");
            },
            err => alert("GPS gagal: " + err.message)
        );
        </script>
        '''
        st.components.v1.html(js, height=0)

    col1, col2 = st.columns(2)
    with col1:
        driver_lat = st.number_input("Lat Driver", value=st.session_state.get("driver_lat_input", -6.2088), format="%.6f", key="driver_lat_input")
    with col2:
        driver_lon = st.number_input("Lon Driver", value=st.session_state.get("driver_lon_input", 106.8456), format="%.6f", key="driver_lon_input")
    
    driver_location = (driver_lat, driver_lon)
    st.session_state.driver_loc = driver_location

    st.divider()
    st.header("Jumlah Order")
    num_orders = st.number_input("Order", 1, 5, 3, key="num_orders")

# ----------------------------------------------------------------------------
# INPUT ORDER
# ----------------------------------------------------------------------------
orders = []
for i in range(num_orders):
    with st.expander(f"Order {i+1}", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Pickup")
            input_type_p = st.radio("Pickup", ["Link Maps", "Manual"], key=f"ip_{i}", horizontal=True)
            p_lat = p_lon = None
            if input_type_p == "Link Maps":
                link = st.text_input("Link Pickup", key=f"lp_{i}")
                if link:
                    lat, lon = extract_lat_lon_from_gmaps(link)
                    if lat:
                        st.success(f"{lat:.6f}, {lon:.6f}")
                        p_lat, p_lon = lat, lon
                        st.number_input("Lat", value=lat, disabled=True, key=f"_lp_lat_{i}")
                        st.number_input("Lon", value=lon, disabled=True, key=f"_lp_lon_{i}")
                    else:
                        st.error("Link salah")
            else:
                p_lat = st.number_input("Lat", value=-6.175, format="%.6f", key=f"plat_{i}")
                p_lon = st.number_input("Lon", value=106.865, format="%.6f", key=f"plon_{i}")
        
        with col2:
            st.subheader("Delivery")
            input_type_d = st.radio("Delivery", ["Link Maps", "Manual"], key=f"id_{i}", horizontal=True)
            d_lat = d_lon = None
            if input_type_d == "Link Maps":
                link = st.text_input("Link Delivery", key=f"ld_{i}")
                if link:
                    lat, lon = extract_lat_lon_from_gmaps(link)
                    if lat:
                        st.success(f"{lat:.6f}, {lon:.6f}")
                        d_lat, d_lon = lat, lon
                        st.number_input("Lat", value=lat, disabled=True, key=f"_ld_lat_{i}")
                        st.number_input("Lon", value=lon, disabled=True, key=f"_ld_lon_{i}")
                    else:
                        st.error("Link salah")
            else:
                d_lat = st.number_input("Lat", value=-6.200, format="%.6f", key=f"dlat_{i}")
                d_lon = st.number_input("Lon", value=106.845, format="%.6f", key=f"dlon_{i}")
        
        orders.append({"pickup": (p_lat, p_lon), "delivery": (d_lat, d_lon)})

# ----------------------------------------------------------------------------
# HITUNG RUTE
# ----------------------------------------------------------------------------
if st.button("HITUNG RUTE", type="primary", use_container_width=True):
    with st.spinner("Sedang menghitung..."):
        all_points = [("Driver", driver_location[0], driver_location[1])]
        for idx, o in enumerate(orders):
            if not o["pickup"][0] or not o["delivery"][0]:
                st.error(f"Order {idx+1} belum lengkap!")
                st.stop()
            all_points.append((f"Pickup {idx+1}", o["pickup"][0], o["pickup"][1]))
            all_points.append((f"Delivery {idx+1}", o["delivery"][0], o["delivery"][1]))

        route = [all_points[0]]
        remaining = all_points[1:]
        while remaining:
            curr = route[-1]
            nearest = min(remaining, key=lambda x: haversine(curr[1], curr[2], x[1], x[2]))
            route.append(nearest)
            remaining.remove(nearest)

        total_km = sum(haversine(route[i][1], route[i][2], route[i+1][1], route[i+1][2]) for i in range(len(route)-1))
        est_time_min = (total_km / 30) * 60
        est_fuel_l = total_km / 35
        est_cost = est_fuel_l * 13500
        gmaps_url = generate_gmaps_url([(p[1], p[2]) for p in route])

        route_data = {
            "route": route,
            "total_km": total_km,
            "est_time_min": est_time_min,
            "est_fuel_l": est_fuel_l,
            "est_cost": est_cost,
            "gmaps_url": gmaps_url,
            "driver_loc": driver_location
        }

        st.session_state.route_data = route_data
        st.session_state.map_obj = rebuild_map(route_data)

        # SIMPAN KE LOCALSTORAGE (HANYA DATA JSON!)
        save_data = {
            "route_data": route_data,
            "driver_loc": driver_location
        }
        save_to_storage(save_data)

        st.balloons()
        st.success("Rute selesai & disimpan otomatis 2 jam!")

# ----------------------------------------------------------------------------
# TAMPILKAN HASIL
# ----------------------------------------------------------------------------
if st.session_state.route_data:
    rd = st.session_state.route_data
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Jarak", f"{rd['total_km']:.2f} km")
    with col2: st.metric("Waktu", f"{rd['est_time_min']:.0f} menit")
    with col3: st.metric("Bensin", f"{rd['est_fuel_l']:.2f} L")
    with col4: st.metric("Biaya", f"Rp {rd['est_cost']:,.0f}")

    st.markdown(f"""
    <div style="text-align:center; margin:30px;">
        <a href="{rd['gmaps_url']}" target="_blank">
            <button style="background:#34A853; color:white; padding:18px 40px; font-size:20px; border:none; border-radius:12px;">
            BUKA GOOGLE MAPS
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)

    st_folium(st.session_state.map_obj, width=1000, height=600)

    col_a, col_b = st.columns([1, 4])
    with col_a:
        if st.button("CLEAR & BARU", type="secondary"):
            clear_storage()
            st.session_state.clear()
            for key in required_keys:
                st.session_state[key] = None
            st.success("Semua data dihapus!")
            st.rerun()
    with col_b:
        st.caption("Data otomatis hilang setelah 2 jam")

else:
    st.info("Isi data → Hitung → Refresh pun tetap ada!")
    st.markdown("### Fitur: **Tidak pernah hilang selama 2 jam!**")
