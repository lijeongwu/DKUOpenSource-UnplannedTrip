from math import radians, sin, cos, sqrt, atan2
import folium
import requests
import polyline

def run(origin, dest_lat, dest_lon, api_key):
    destination = f"{dest_lat},{dest_lon}"
    print(f"🚌 육지 목적지 처리 중: 출발지={origin}, 목적지={destination}")

    # 좌표 구하기
    start_coords = geocode_via_directions(origin, api_key)
    if not start_coords:
        print(f"❌ 출발지 좌표를 가져올 수 없습니다: {origin}")
        return
    end_coords = (dest_lat, dest_lon)

    m = folium.Map(location=start_coords, zoom_start=7)

    # -------------------- OSRM 경로 레이어 --------------------
    osrm_data = get_osrm_route(start_coords, end_coords)
    if osrm_data:
        points = polyline.decode(osrm_data["routes"][0]["geometry"])
        duration_osrm = osrm_data["routes"][0]["duration"]
        label = f"자차 경로 (OSRM 소요시간: {format_duration(duration_osrm)})"
        layer_osrm = folium.FeatureGroup(name=label)
        folium.PolyLine(points, color="green", weight=4, tooltip=label).add_to(layer_osrm)
        layer_osrm.add_to(m)

    # -------------------- Google Directions 대중교통 경로 --------------------
    google_data = get_google_routes(origin, destination, api_key)

    fastest = None
    fastest_time = None

    for route in google_data["routes"]:
        leg = route["legs"][0]
        duration = leg["duration"]["value"]
        if fastest is None or duration < fastest_time:
            fastest = route
            fastest_time = duration

    if fastest:
        label = format_duration(fastest["legs"][0]["duration"]["value"])
        layer_fast = folium.FeatureGroup(name=f"대중교통 (최소 소요시간: {label})")
        draw_polyline(fastest, layer_fast, "blue", f"최소 소요시간: {label}")
        add_transit_markers(fastest, layer_fast)
        add_walking_markers(fastest, layer_fast)
        layer_fast.add_to(m)

    # -------------------- 비행기 경로 레이어 --------------------
    airport_coords = {
        "인천": (37.4692, 126.451),
        "김포": (37.558056, 126.790556),
        "김해": (35.179444, 128.938056),
        "제주": (33.511111, 126.492778),
        "대구": (35.893889, 128.658889),
        "울산": (35.593333, 129.351667),
        "청주": (36.716389, 127.498889),
        "양양": (38.061111, 128.668889),
        "무안": (34.991406, 126.382814),
        "광주": (35.126389, 126.808889),
        "여수": (34.842222, 127.616667),
        "사천": (35.088611, 128.070278),
        "포항": (35.987858, 129.420486),
        "군산": (35.903756, 126.615906),
        "원주": (37.438056, 127.960278)
    }

    air_routes = {
        ("김포", "김해"): 70,
        ("김포", "여수"): 60,
        ("김포", "울산"): 70,
        ("김포", "광주"): 60,
        ("김포","사천"):65,
        ("김포","포항"):60,
        ("김해", "인천"): 65,
        ("광주", "제주"): 55,
        ("군산", "제주"): 60,
        ("대구", "제주"): 65,
        ("김해", "제주"): 60,
        ("김포", "제주"): 75,
        ("여수", "제주"): 55,
        ("울산", "제주"): 65,
        ("원주", "제주"): 75,
        ("사천", "제주"): 65,
        ("청주", "제주"): 70,
        ("포항", "제주"): 65,
        ## 반대 노선
        ("김해", "김포"): 70,
        ("여수", "김포"): 60,
        ("울산", "김포"): 70,
        ("광주", "김포"): 60,
        ("사천", "김포"):65,
        ("포항", "김포"):60,
        ("인천", "김포"): 65,
        ("인천", "김해"): 65,
        ("제주", "광주"): 55,
        ("제주", "군산"): 60,
        ("제주", "대구"): 65,
        ("제주", "김해"): 60,
        ("제주", "김포"): 75,
        ("제주", "여수"): 55,
        ("제주", "울산"): 65,
        ("제주", "원주"): 75,
        ("제주", "사천"): 65,
        ("제주", "청주"): 70,
        ("제주", "포항"): 65
    }

    start_airport = find_nearest_airport(start_coords[0], start_coords[1], airport_coords)
    end_airport = find_nearest_airport(end_coords[0], end_coords[1], airport_coords)

    air_start_query = f"{start_airport}공항"
    air_end_query = f"{end_airport}공항"

    air_start = get_google_routes(origin, air_start_query, api_key)
    air_end = get_google_routes(air_end_query, destination, api_key)

    if (start_airport, end_airport) not in air_routes:
        print(f"❌ 항공 노선이 없습니다: {start_airport} → {end_airport}")
    else:
        if air_start["routes"] and air_end["routes"]:
            air_time = air_routes[(start_airport, end_airport)] * 60
            air_total_time = (
                air_start["routes"][0]["legs"][0]["duration"]["value"] +
                air_end["routes"][0]["legs"][0]["duration"]["value"] +
                air_time
            )

            air_label = format_duration(air_total_time)
            layer_air = folium.FeatureGroup(name=f"비행기 경로 (총 소요시간: {air_label})")

            draw_polyline(air_start["routes"][0], layer_air, "orange", f"출발지 → {start_airport}공항")
            add_transit_markers(air_start["routes"][0], layer_air)
            add_walking_markers(air_start["routes"][0], layer_air)

            draw_polyline(air_end["routes"][0], layer_air, "orange", f"{end_airport}공항 → 목적지")
            add_transit_markers(air_end["routes"][0], layer_air)
            add_walking_markers(air_end["routes"][0], layer_air)

            folium.PolyLine([
                airport_coords[start_airport],
                airport_coords[end_airport]
            ], color="red", weight=3, dash_array="5,5",
            tooltip=f"비행 경로 (비행 시간: {air_routes[(start_airport, end_airport)]}분)").add_to(layer_air)

            layer_air.add_to(m)

    folium.Marker(start_coords, tooltip="출발지", icon=folium.Icon(color="green")).add_to(m)
    folium.Marker(end_coords, tooltip="목적지", icon=folium.Icon(color="red")).add_to(m)

    folium.LayerControl().add_to(m)
    m.save("random_map.html")
    m.save("random_map_backup.html")
    print("🖼️ 육지 경로 지도 저장 완료: random_map.html")

def geocode(address, API_KEY):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={API_KEY}"
    res = requests.get(url).json()
    loc = res["results"][0]["geometry"]["location"]
    return loc["lat"], loc["lng"]

def geocode_via_directions(address, API_KEY):
    if "제주" in address:
        dummy_dest = "제주 공항"
    else:
        dummy_dest = "서울역"  # 어떤 장소든 무관. 목적은 origin 좌표 추출
    url = (
        f"https://maps.googleapis.com/maps/api/directions/json?"
        f"origin={address}&destination={dummy_dest}&mode=transit&key={API_KEY}"
    )
    res = requests.get(url).json()

    if res.get("status") != "OK" or not res.get("routes"):
        print(f"❌ Directions API로 출발지 좌표 추출 실패: {address}")
        return None

    start_location = res["routes"][0]["legs"][0]["start_location"]
    return start_location["lat"], start_location["lng"]

def get_osrm_route(start_coords, end_coords):
    url = (
        f"http://localhost:5000/route/v1/driving/"
        f"{start_coords[1]},{start_coords[0]};{end_coords[1]},{end_coords[0]}"
        f"?overview=full&geometries=polyline"
    )
    res = requests.get(url)
    return res.json() if res.status_code == 200 else None

def get_google_routes(origin, destination, API_KEY):
    url = (
        f"https://maps.googleapis.com/maps/api/directions/json?"
        f"origin={origin}&destination={destination}&mode=transit&alternatives=true&key={API_KEY}"
    )
    res = requests.get(url).json()
    return res if res["status"] == "OK" else {"routes": []}

def draw_polyline(route, m, color, label):
    points = polyline.decode(route["overview_polyline"]["points"])
    folium.PolyLine(points, color=color, weight=4, tooltip=label).add_to(m)

def add_transit_markers(route, m):
    if not route:
        return
    steps = route["legs"][0]["steps"]
    for step in steps:
        if step["travel_mode"] == "TRANSIT":
            td = step["transit_details"]
            dep = td["departure_stop"]
            arr = td["arrival_stop"]
            vehicle = td["line"]["vehicle"]["type"]
            name = td["line"].get("short_name", td["line"].get("name", "노선"))
            folium.Marker(
                [dep["location"]["lat"], dep["location"]["lng"]],
                tooltip=f"승차: {vehicle} {name} @ {dep['name']}",
                icon=folium.Icon(color="blue", icon="sign-in-alt", prefix="fa")
            ).add_to(m)
            folium.Marker(
                [arr["location"]["lat"], arr["location"]["lng"]],
                tooltip=f"하차: {vehicle} {name} @ {arr['name']}",
                icon=folium.Icon(color="orange", icon="sign-out-alt", prefix="fa")
            ).add_to(m)

def add_walking_markers(route, m):
    steps = route["legs"][0]["steps"]
    for step in steps:
        if step["travel_mode"] == "WALKING":
            start = step["start_location"]
            dist_text = step["distance"]["text"]
            dur_text = step["duration"]["text"]
            folium.Marker(
                [start["lat"], start["lng"]],
                tooltip=f"도보 시작: {dist_text} / {dur_text}",
                icon=folium.Icon(color="lightgray", icon="male", prefix="fa")
            ).add_to(m)

def format_duration(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    return f"{h}시간 {m}분" if h else f"{m}분"

def find_nearest_airport(lat, lon, airport_coords):
    min_dist = float('inf')
    nearest_airport = None
    for airport, (a_lat, a_lon) in airport_coords.items():
        dist = haversine(lat, lon, a_lat, a_lon)
        if dist < min_dist:
            min_dist = dist
            nearest_airport = airport
    return nearest_airport

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c
