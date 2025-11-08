# ============================================================================
# FILE: multi_stop_optimizer_v11_1_FULL_KLIKABLE.py
# FITUR: SEMUA LINK & MARKER BISA DIKLIK! + TAMPILAN PRO
# ============================================================================
import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import json
import requests
import re
from datetime import datetime, timedelta
from math import radians, sin, cos, asin, sqrt

st.set_page_config(page_title="Smart Route v11.1 - SEMUA KLIKABLE", layout="wide")
st.title("Smart Route Optimizer v11.1")
st.caption("PER TRIP • SEMUA BISA DIKLIK • Data 2 Jam • Pro Banget!")

# ============================================================================
# SESSION STATE & LOCALSTORAGE 2 JAM
# ============================================================================
required_keys = ["trips_data", "driver_loc", "map_obj"]
for key in required_keys:
    if key not in st.session_state:
        st.session_state[key] = None

STORAGE_KEY = "smart_route_v111_klikable"
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
            window.parent.postMessage({{type: "LOADED_V111", data: parsed.data}}, "*");
        }} else {{
            localStorage.removeItem("{STORAGE_KEY}");
        }}
    }}
    </script>
    '''
    return st.components.v1.html(js, height=0)

def clear_storage():
    js = '<script>localStorage.removeItem("smart_route_v111_klikable");</script>'
    st.components.v1.html(js, height=0)

load_from_storage()
if st.session_state.get("LOADED_V111"):
    loaded = st.session_state["LOADED_V111"]
    st.session_state.trips_data = loaded.get("trips_data")
    st.session_state.driver_loc = loaded.get("driver_loc")

# ============================================================================
# UTILITY
# ============================================================================
def extract_lat_lon_from_gmaps(url):
    try:
        r = requests.get(url, allow_redirects=True, timeout=5)
        final_url = r.url
        match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', final_url)
        if match: return float(match.group(1)), float(match.group(2))
        match2 = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', final_url)
        if match2: return float(match2.group(1)), float(match2.group(2))
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

def gmaps_link(lat, lon, label=""):
    return f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"

def gmaps_trip(origin_lat, origin_lon, pickup_lat, pickup_lon, delivery_lat, delivery_lon):
    return f"https://www.google.com/maps/dir/?api=1&origin={origin_lat},{origin_lon}&destination={delivery_lat},{delivery_lon}&waypoints={pickup_lat},{pickup_lon}&travelmode=driving"

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
                inputs[0].dispatchEvent(new Event('input', { bubbles: true }));
                inputs[1].dispatchEvent(new Event('input', { bubbles: true }));
            },
            err => alert("GPS Error: " + err.message)
        );
        </script>
        '''
        st.components.v1.html(js, height=0)

    c1, c2 = st.columns(2)
    with c1:
        driver_lat = st.number_input("Lat", value=st.session_state.get("driver_lat_input", -6.2088), format="%.6f", key="driver_lat")
    with c2:
        driver_lon = st.number_input("Lon", value=st.session_state.get("driver_lon_input", 106.8456), format="%.6f", key="driver_lon")
    driver_loc = (driver_lat, driver_lon)
    st.session_state.driver_loc = driver_loc

    st.divider()
    num_orders = st.number_input("Jumlah Order", 1, 6, 3, key="num_orders")

# ============================================================================
# INPUT ORDERS
# ============================================================================
orders = []
for i in range(num_orders):
    with st.expander(f"Order {i+1}", expanded=True):
        col1, col2 = st.columns(2)
        p_lat = p_lon = d_lat = d_lon = None

        with col1:
            st.subheader("Pickup")
            if st.radio("Pickup", ["Manual", "Link"], key=f"p_{i}", horizontal=True) == "Link":
                link = st.text_input("Link Maps Pickup", key=f"pl_{i}")
                if link:
                    lat, lon = extract_lat_lon_from_gmaps(link)
                    if lat:
                        st.success(f"{lat:.6f}, {lon:.6f}")
                        p_lat, p_lon = lat, lon
            if not p_lat:
                p_lat = st.number_input("Lat Pickup", format="%.6f", key=f"plat_{i}", value=-6.175)
                p_lon = st.number_input("Lon Pickup", format="%.6f", key=f"plon_{i}", value=106.865)

        with col2:
            st.subheader("Delivery")
            if st.radio("Delivery", ["Manual", "Link"], key=f"d_{i}", horizontal=True) == "Link":
                link = st.text_input("Link Maps Delivery", key=f"dl_{i}")
                if link:
                    lat, lon = extract_lat_lon_from_gmaps(link)
                    if lat:
                        st.success(f"{lat:.6f}, {lon:.6f}")
                        d_lat, d_lon = lat, lon
            if not d_lat:
                d_lat = st.number_input("Lat Delivery", format="%.6f", key=f"dlat_{i}", value=-6.200)
                d_lon = st.number_input("Lon Delivery", format="%.6f", key=f"dlon_{i}", value=106.845)

        if p_lat and d_lat:
            orders.append({
                "pickup": (p_lat, p_lon),
                "delivery": (d_lat, d_lon),
                "label": f"Order {i+1}"
            })

# ============================================================================
# HITUNG RUTE PER TRIP
# ============================================================================
if st.button("HITUNG RUTE PER TRIP", type="primary", use_container_width=True):
    if not orders:
        st.error("Isi minimal 1 order!")
        st.stop()

    with st.spinner("Mengoptimalkan urutan per trip..."):
        current_pos = driver_loc
        trips = []
        total_km = total_min = total_fuel = total_cost = 0

        remaining = orders.copy()
        while remaining:
            nearest = min(remaining, key=lambda o: haversine(current_pos[0], current_pos[1], o["pickup"][0], o["pickup"][1]))
            remaining.remove(nearest)

            leg1 = haversine(current_pos[0], current_pos[1], nearest["pickup"][0], nearest["pickup"][1])
            leg2 = haversine(nearest["pickup"][0], nearest["pickup"][1], nearest["delivery"][0], nearest["delivery"][1])
            trip_km = leg1 + leg2
            trip_min = (trip_km / 30) * 60
            trip_fuel = trip_km / 35
            trip_cost = trip_fuel * 13500

            trip_url = gmaps_trip(
                current_pos[0], current_pos[1],
                nearest["pickup"][0], nearest["pickup"][1],
                nearest["delivery"][0], nearest["delivery"][1]
            )

            trips.append({
                "order": nearest["label"],
                "from": current_pos,
                "pickup": nearest["pickup"],
                "delivery": nearest["delivery"],
                "km": trip_km,
                "min": trip_min,
                "fuel": trip_fuel,
                "cost": trip_cost,
                "url": trip_url
            })

            current_pos = nearest["delivery"]
            total_km += trip_km
            total_min += trip_min
            total_fuel += trip_fuel
            total_cost += trip_cost

        result = {
            "trips": trips,
            "totals": {"km": total_km, "min": total_min, "fuel": total_fuel, "cost": total_cost},
            "driver_start": driver_loc,
            "driver_end": current_pos
        }

        st.session_state.trips_data = result
        save_to_storage({"trips_data": result, "driver_loc": driver_loc})
        st.balloons()
        st.success("Rute selesai! Semua link & marker bisa diklik!")

# ============================================================================
# TAMPILKAN HASIL – SEMUA KLIKABLE!
# ============================================================================
if st.session_state.trips_data:
    data = st.session_state.trips_data
    trips = data["trips"]
    totals = data["totals"]

    # METRICS
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Total Jarak", f"{totals['km']:.2f} km")
    with c2: st.metric("Total Waktu", f"{totals['min']:.0f} menit")
    with c3: st.metric("Bensin", f"{totals['fuel']:.2f} L")
    with c4: st.metric("Biaya", f"Rp {totals['cost']:,.0f}")

    # TABEL PER TRIP – LINK KLIKABLE
    st.markdown("### Detail Per Trip")
    table = []
    for i, t in enumerate(trips):
        table.append({
            "Trip": i+1,
            "Order": t["order"],
            "Jarak": f"{t['km']:.2f} km",
            "Waktu": f"{t['min']:.0f} mnt",
            "Bensin": f"{t['fuel']:.2f} L",
            "Biaya": f"Rp {t['cost']:,.0f}",
            "BUKA TRIP": f"[BUKA DI GOOGLE MAPS]({t['url']})"
        })
    st.markdown(pd.DataFrame(table).to_html(escape=False, index=False), unsafe_allow_html=True)

    # PETA – MARKER BISA DIKLIK!
    m = folium.Map(location=driver_loc, zoom_start=12, tiles="CartoDB positron")

    # Driver Start
    folium.Marker(
        driver_loc,
        popup=folium.Popup(f"""
            <b style="color:#0066FF;">DRIVER MULAI</b><br>
            <a href="{gmaps_link(*driver_loc)}" target="_blank">Buka di Maps</a>
        """, max_width=300),
        tooltip="Driver Start",
        icon=folium.Icon(color="blue", icon="motorcycle", prefix='fa')
    ).add_to(m)

    # Semua trip
    route_coords = [driver_loc]
    for i, t in enumerate(trips):
        # Pickup
        folium.Marker(
            t["pickup"],
            popup=folium.Popup(f"""
                <b style="color:green;">Pickup {t['order']}</b><br>
                <a href="{gmaps_link(*t['pickup'])}" target="_blank">Buka Lokasi Pickup</a>
            """, max_width=300),
            tooltip=f"Pickup {t['order']}",
            icon=folium.Icon(color="green", icon="arrow-up", prefix='fa')
        ).add_to(m)

        # Delivery
        folium.Marker(
            t["delivery"],
            popup=folium.Popup(f"""
                <b style="color:red;">Delivery {t['order']}</b><br>
                <a href="{gmaps_link(*t['delivery'])}" target="_blank">Buka Lokasi Delivery</a><br>
                <hr>
                <a href="{t['url']}" target="_blank" style="color:#34A853;font-weight:bold;">BUKA RUTE TRIP {i+1} DI GOOGLE MAPS</a>
            """, max_width=300),
            tooltip=f"Delivery {t['order']}",
            icon=folium.Icon(color="red", icon="arrow-down", prefix='fa')
        ).add_to(m)

        route_coords.extend([t["pickup"], t["delivery"]])

    # Garis rute
    folium.PolyLine(route_coords, color="#0066FF", weight=7, opacity=0.9).add_to(m)

    # Finish flag
    folium.Marker(
        data["driver_end"],
        popup=folium.Popup(f"<b style='color:black;'>SELESAI DI SINI</b>", max_width=300),
        icon=folium.Icon(color="black", icon="flag-checkered", prefix='fa')
    ).add_to(m)

    st.session_state.map_obj = m
    st_folium(m, width=1000, height=600, key="map")

    # CLEAR BUTTON
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("CLEAR SEMUA", type="secondary"):
            clear_storage()
            st.session_state.clear()
            st.rerun()
    with col2:
        st.caption("Data otomatis hilang setelah 2 jam tidak aktif")

else:
    st.info("Isi data → Klik **HITUNG RUTE PER TRIP** → Semua bisa diklik!")
    st.markdown("""
    ### Fitur Keren v11.1:
    - Link di tabel **bisa diklik**
    - Marker di peta **bisa diklik → langsung buka Maps**
    - Rute per trip realistis
    - Data aman 2 jam
    """)

