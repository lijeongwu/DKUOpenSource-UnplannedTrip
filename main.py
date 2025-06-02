import sys
import os
import random
import requests
import folium
import webbrowser
import geopandas as gpd
import pandas as pd
from folium import Popup
import subprocess
from shapely.geometry import Point
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton,
    QHBoxLayout, QSizePolicy, QMenu
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtCore import QUrl, QPoint
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

API_KEY = "AIzaSyCMKJKuiDSJZ_VkCHBsbKO2Zp_TdtsFFvg"
gdf = gpd.read_file("GeoJson/korea_municipalities.geojson")
if gdf.crs is None or gdf.crs.to_string() != "EPSG:4326":
    gdf = gdf.set_crs("EPSG:4326")
center_df = pd.read_csv("행정구역 중심좌표.csv")

class WebEnginePage(QWebEnginePage):
    def createWindow(self, _type):
        page = QWebEnginePage(self)
        page.urlChanged.connect(lambda url: webbrowser.open(url.toString()))
        return page

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("여행 추천 앱")
        self.resize(1000, 800)
        self.api_key = "KakaoAK 8900b330e3332fbd09be87e1827c24fe"
        self.map_file = "random_map.html"
        self.random_lat = None
        self.random_lon = None
        self.selected_category = None
        self.category_data = {}
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.web_view = QWebEngineView()
        self.web_view.setPage(WebEnginePage(self.web_view))
        self.web_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.web_view)

        random_button = QPushButton("랜덤 위치 선정")
        random_button.setStyleSheet("background-color: #666666; color: white; font-size: 16px;")
        random_button.clicked.connect(self.random_location)
        main_layout.addWidget(random_button)

        search_container = QHBoxLayout()
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("출발지 입력 (예: 서울역)")
        self.input_line.returnPressed.connect(self.recommend_route_from_input)
        search_container.addWidget(self.input_line)
        main_layout.addLayout(search_container)

        button_grid_1 = QHBoxLayout()
        btn1 = QPushButton("주변 관광지 추천")
        btn2 = QPushButton("숙소 추천")
        btn3 = QPushButton("맛집 추천")
        btn_back = QPushButton("뒤로가기")

        for btn in (btn1, btn2, btn3, btn_back):
            btn.setStyleSheet("background-color: #666666; color: white; font-size: 16px;")
            button_grid_1.addWidget(btn)
        main_layout.addLayout(button_grid_1)

        btn1.clicked.connect(self.on_button1_clicked)
        btn2.clicked.connect(self.on_button2_clicked)
        btn3.clicked.connect(self.on_button3_clicked)
        # btn_back.clicked.connect(self.show_random_location_map)
        btn_back.clicked.connect(self.show_backup_map)

        category_button = QPushButton("카테고리")
        category_button.setStyleSheet("background-color: #666666; color: white; font-size: 16px;")
        category_button.clicked.connect(self.show_category_menu)
        main_layout.addWidget(category_button)

        reset_category_button = QPushButton("카테고리 초기화")
        reset_category_button.setStyleSheet("background-color: #666666; color: white; font-size: 16px;")
        reset_category_button.clicked.connect(self.reset_category)

        category_layout = QHBoxLayout()
        category_layout.addWidget(category_button)
        category_layout.addWidget(reset_category_button)
        main_layout.addLayout(category_layout)

    def show_backup_map(self):
        backup_path = os.path.abspath("random_map_backup.html")
        if os.path.exists(backup_path):
            print("🔙 백업된 지도 로딩 중...")
            self.web_view.load(QUrl.fromLocalFile(backup_path))
        else:
            print("❌ 백업된 지도가 없습니다.")

    def random_location(self):
        place_name = None
        if self.selected_category:
            file_path = f"{self.selected_category}.csv"
            if os.path.exists(file_path):
                if self.selected_category not in self.category_data:
                    self.category_data[self.selected_category] = pd.read_csv(file_path, usecols=["이름"])
                category_df = self.category_data[self.selected_category]
                selected_row = category_df.sample(n=1).iloc[0]
                place_name = selected_row["이름"]
                lat, lon = self.geocode(f"대한민국 {place_name}")
                if lat is None or lon is None:
                    print(f"❌ 위치를 찾을 수 없습니다: {place_name}")
                    return
                self.random_lat = lat
                self.random_lon = lon
                print(f"📍 무작위 선택된 {self.selected_category}: {place_name} (위도: {lat}, 경도: {lon})")
            else:
                print(f"❌ {self.selected_category}.csv 파일이 존재하지 않습니다.")
                return
        else:
            random_region = center_df.sample(n=1).iloc[0]
            self.random_lat = random_region["위도"]
            self.random_lon = random_region["경도"]
            place_name = random_region["행정구역"]
            print(f"📍 무작위 행정구역 선택: {place_name} (위도: {self.random_lat}, 경도: {self.random_lon})")

        origin = self.input_line.text().strip()
        if not origin:
            origin = "경기도 용인시 수지구 죽전로 152"
        self.run_osrm_route(origin, self.random_lat, self.random_lon)
        self.web_view.load(QUrl.fromLocalFile(os.path.abspath("random_map.html")))

    def show_random_location_map(self):
        if self.random_lat is not None and self.random_lon is not None:
            print("🔙 랜덤 위치 지도 복원 중...")
            self.update_map(self.random_lat, self.random_lon)
        else:
            print("❌ 아직 랜덤 위치가 설정되지 않았습니다.")

    def update_map(self, lat, lon, markers=None):
        m = folium.Map(location=[lat, lon], zoom_start=12)
        folium.Marker([lat, lon], tooltip="기준 위치").add_to(m)
        if markers:
            for marker in markers:
                folium.Marker(
                    [marker['lat'], marker['lon']],
                    tooltip=marker['name'],
                    popup=marker['popup'],
                    icon=marker['icon']
                ).add_to(m)
        m.save(self.map_file)
        self.web_view.load(QUrl.fromLocalFile(os.path.abspath(self.map_file)))

    def recommend_route_from_input(self):
        user_input = self.input_line.text()
        if not user_input:
            print("출발지를 입력해주세요.")
            return
        try:
            geolocator = Nominatim(user_agent="mapApp")
            start_loc = geolocator.geocode(user_input, timeout=10)
            if not start_loc:
                print("위치를 찾을 수 없습니다.")
                return
            start = [start_loc.latitude, start_loc.longitude]
            if self.random_lat is None or self.random_lon is None:
                print("랜덤 위치가 설정되지 않았습니다.")
                return
            end = [self.random_lat, self.random_lon]
            m = folium.Map(location=start, zoom_start=14)
            folium.Marker(start, tooltip=f"출발지: {user_input}").add_to(m)
            folium.Marker(end, tooltip="도착지: 랜덤 위치").add_to(m)
            folium.PolyLine([start, end], color="blue", weight=5, opacity=0.8).add_to(m)
            m.save(self.map_file)
            self.web_view.load(QUrl.fromLocalFile(os.path.abspath(self.map_file)))
        except GeocoderTimedOut:
            print("지오코딩 시간이 초과되었습니다.")

    def on_button1_clicked(self):
        if self.random_lat and self.random_lon:
            self.search_nearby_attractions()
        else:
            print("먼저 랜덤 위치를 선택하세요.")

    def on_button2_clicked(self):
        if self.random_lat and self.random_lon:
            self.search_accommodations()
        else:
            print("먼저 랜덤 위치를 선택하세요.")

    def on_button3_clicked(self):
        if self.random_lat and self.random_lon:
            self.search_restaurants()
        else:
            print("먼저 랜덤 위치를 선택하세요.")

    def show_category_menu(self):
        menu = QMenu(self)
        categories = ["산", "해변"]
        for category in categories:
            action = menu.addAction(category)
            action.triggered.connect(lambda _, c=category: self.category_selected(c))
        menu.exec_(self.mapToGlobal(QPoint(100, 400)))

    def category_selected(self, category):
        self.selected_category = category
        print(f"✅ 선택된 카테고리: {category}")

    def search_nearby_attractions(self):
        headers = {"Authorization": self.api_key}
        url = "https://dapi.kakao.com/v2/local/search/category.json"
        categories = ["CT1", "AT4"]
        try:
            markers = []
            for category_code in categories:
                params = {
                    "category_group_code": category_code,
                    "x": self.random_lon,
                    "y": self.random_lat,
                    "radius": 10000,
                    "size": 10
                }
                response = requests.get(url, headers=headers, params=params)
                data = response.json()
                if "documents" in data:
                    for place in data["documents"]:
                        name = place['place_name'] + (" (문화)" if category_code == "CT1" else " (관광)")
                        lat = float(place["y"])
                        lon = float(place["x"])
                        search_url = f"https://search.naver.com/search.naver?query={place['place_name']}"
                        popup_html = f"<a href='{search_url}' target='_blank'>링크</a>"
                        popup = Popup(popup_html, max_width=200)
                        markers.append({
                            'name': name,
                            'lat': lat,
                            'lon': lon,
                            'popup': popup,
                            'icon': folium.Icon(color="red")
                        })
            self.add_markers_to_existing_map(markers)
        except Exception as e:
            print(f"관광지 검색 실패: {e}")

    def search_accommodations(self):
        headers = {"Authorization": self.api_key}
        url = "https://dapi.kakao.com/v2/local/search/category.json"
        params = {
            "category_group_code": "AD5",
            "x": self.random_lon,
            "y": self.random_lat,
            "radius": 10000,
            "size": 10
        }
        try:
            response = requests.get(url, headers=headers, params=params)
            data = response.json()
            if "documents" in data and data["documents"]:
                markers = []
                for place in data["documents"]:
                    name = f"{place['place_name']} (숙소)"
                    lat = float(place["y"])
                    lon = float(place["x"])
                    search_url = f"https://search.naver.com/search.naver?query={place['place_name']}"
                    popup_html = f"<a href='{search_url}' target='_blank'>링크</a>"
                    popup = Popup(popup_html, max_width=200)
                    markers.append({
                        'name': name,
                        'lat': lat,
                        'lon': lon,
                        'popup': popup,
                        'icon': folium.Icon(color="red")
                    })
                self.update_map(self.random_lat, self.random_lon, markers)
            else:
                print("주변 숙소를 찾을 수 없습니다.")
        except Exception as e:
            print(f"숙소 검색 실패: {e}")

    def search_restaurants(self):
        headers = {"Authorization": self.api_key}
        url = "https://dapi.kakao.com/v2/local/search/category.json"
        params = {
            "category_group_code": "FD6",
            "x": self.random_lon,
            "y": self.random_lat,
            "radius": 10000,
            "size": 10
        }
        try:
            response = requests.get(url, headers=headers, params=params)
            data = response.json()
            if "documents" in data and data["documents"]:
                markers = []
                for place in data["documents"]:
                    name = f"{place['place_name']} (맛집)"
                    lat = float(place["y"])
                    lon = float(place["x"])
                    search_url = f"https://search.naver.com/search.naver?query={place['place_name']}"
                    popup_html = f"<a href='{search_url}' target='_blank'>링크</a>"
                    popup = Popup(popup_html, max_width=200)
                    markers.append({
                        'name': name,
                        'lat': lat,
                        'lon': lon,
                        'popup': popup,
                        'icon': folium.Icon(color="orange", icon="cutlery", prefix='fa')
                    })
                self.update_map(self.random_lat, self.random_lon, markers)
            else:
                print("주변 맛집을 찾을 수 없습니다.")
        except Exception as e:
            print(f"맛집 검색 실패: {e}")

    def run_osrm_route(self, origin, dest_lat, dest_lon):
        subprocess.run([
            "python", "main_OSRM.py",
            "--origin", str(origin),
            "--dest_lat", str(dest_lat),
            "--dest_lon", str(dest_lon),
            "--api_key", API_KEY
        ])

    def add_markers_to_existing_map(self, markers):
        try:
            m = folium.Map(location=[self.random_lat, self.random_lon], zoom_start=12)
            folium.Marker([self.random_lat, self.random_lon], tooltip="기준 위치").add_to(m)
            for marker in markers:
                folium.Marker(
                    [marker['lat'], marker['lon']],
                    tooltip=marker['name'],
                    popup=marker['popup'],
                    icon=marker['icon']
                ).add_to(m)
            m.save(self.map_file)
            self.web_view.load(QUrl.fromLocalFile(os.path.abspath(self.map_file)))
        except Exception as e:
            print(f"마커 추가 중 오류 발생: {e}")

    def geocode(self, address):
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={API_KEY}"
        try:
            res = requests.get(url).json()
            if res["status"] != "OK" or not res["results"]:
                print(f"❌ 주소 '{address}'를 찾을 수 없습니다.")
                return None, None
            loc = res["results"][0]["geometry"]["location"]
            return loc["lat"], loc["lng"]
        except Exception as e:
            print(f"❌ 지오코딩 중 오류 발생: {e}")
            return None, None
        
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
    
    def reset_category(self):
        self.selected_category = None
        print("🔁 카테고리 초기화 완료 (선택 해제됨)")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
