import sys
import os
import random
import requests
import folium
import webbrowser
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton,
    QHBoxLayout, QSizePolicy, QMenu
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtCore import QUrl, QPoint
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

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
        self.map_file = "map.html"
        self.random_lat = None
        self.random_lon = None
        self.selected_category = None
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
        for btn in (btn1, btn2):
            btn.setStyleSheet("background-color: #666666; color: white; font-size: 16px;")
        button_grid_1.addWidget(btn1)
        button_grid_1.addWidget(btn2)
        main_layout.addLayout(button_grid_1)

        category_button = QPushButton("카테고리")
        category_button.setStyleSheet("background-color: #666666; color: white; font-size: 16px;")
        category_button.clicked.connect(self.show_category_menu)
        main_layout.addWidget(category_button)

        btn1.clicked.connect(self.on_button1_clicked)
        btn2.clicked.connect(self.on_button2_clicked)

    def random_location(self):
        lat_min, lat_max = 33.0, 38.5
        lon_min, lon_max = 126.0, 130.0
        self.random_lat = random.uniform(lat_min, lat_max)
        self.random_lon = random.uniform(lon_min, lon_max)
        self.selected_category = None
        self.update_map(self.random_lat, self.random_lon)

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
            return
        try:
            geolocator = Nominatim(user_agent="mapApp")
            start_loc = geolocator.geocode(user_input, timeout=10)
            if not start_loc:
                return
            start = [start_loc.latitude, start_loc.longitude]
            if self.random_lat is None or self.random_lon is None:
                return
            end = [self.random_lat, self.random_lon]
            m = folium.Map(location=start, zoom_start=14)
            folium.Marker(start, tooltip=f"출발지: {user_input}").add_to(m)
            folium.Marker(end, tooltip="도착지: 랜덤 위치").add_to(m)
            folium.PolyLine([start, end], color="blue", weight=5, opacity=0.8).add_to(m)
            m.save(self.map_file)
            self.web_view.load(QUrl.fromLocalFile(os.path.abspath(self.map_file)))
        except GeocoderTimedOut:
            print("지오코딩 시간 초과")

    def on_button1_clicked(self):
        if self.random_lat and self.random_lon:
            self.search_nearby_attractions()

    def on_button2_clicked(self):
        if self.random_lat and self.random_lon:
            self.search_accommodations()

    def show_category_menu(self):
        menu = QMenu(self)
        categories = ["산", "바다"]  # "꽃구경" 제거됨
        for category in categories:
            action = menu.addAction(category)
            action.triggered.connect(lambda _, c=category: self.category_selected(c))
        menu.exec_(self.mapToGlobal(QPoint(100, 400)))

    def category_selected(self, category):
        self.selected_category = category
        if self.random_lat is None or self.random_lon is None:
            return
        if category == "산":
            self.search_nearby_mountains()
        else:
            pass  # 바다 선택 시 마커 표시 생략 (필요시 구현)

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
                        popup_html = f"<a href='https://search.naver.com/search.naver?query={place['place_name']}' target='_blank'>{place['place_name']} (네이버 검색)</a>"
                        markers.append({
                            'name': name,
                            'lat': lat,
                            'lon': lon,
                            'popup': popup_html,
                            'icon': folium.Icon(color="blue")
                        })
            self.update_map(self.random_lat, self.random_lon, markers)
        except Exception as e:
            print("관광지 검색 실패:", e)

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
            if "documents" in data:
                markers = []
                for place in data["documents"]:
                    name = place["place_name"]
                    lat = float(place["y"])
                    lon = float(place["x"])
                    popup_html = f"<a href='https://search.naver.com/search.naver?query={name}' target='_blank'>{name} (네이버 검색)</a>"
                    markers.append({
                        'name': name,
                        'lat': lat,
                        'lon': lon,
                        'popup': popup_html,
                        'icon': folium.Icon(color="purple")
                    })
                self.update_map(self.random_lat, self.random_lon, markers)
        except Exception as e:
            print("숙소 검색 실패:", e)

    def search_nearby_mountains(self):
        try:
            import json
            with open("mountains.json", "r", encoding="utf-8") as f:
                mountain_data = json.load(f)
            markers = []
            for mountain in mountain_data:
                lat = float(mountain["위도"])
                lon = float(mountain["경도"])
                dist = ((lat - self.random_lat) ** 2 + (lon - self.random_lon) ** 2) ** 0.5
                if dist < 0.3:  # 약 30km
                    name = mountain["산이름"]
                    popup_html = f"<a href='https://search.naver.com/search.naver?query={name}' target='_blank'>{name} (네이버 검색)</a>"
                    markers.append({
                        'name': name,
                        'lat': lat,
                        'lon': lon,
                        'popup': popup_html,
                        'icon': folium.Icon(color="red")
                    })
            self.update_map(self.random_lat, self.random_lon, markers)
        except Exception as e:
            print("산 정보 검색 실패:", e)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
