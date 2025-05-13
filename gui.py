import sys
import folium
import os
import random
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit, QLabel, QPushButton, QHBoxLayout, QSizePolicy
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("25-05-10")
        self.setGeometry(100, 100, 600, 800)
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()

        # title_container = QHBoxLayout()
        # title_label = QLabel("랜덤 위치 선정")
        # title_label.setFixedHeight(50)
        # title_label.setFixedWidth(500)
        # title_label.setStyleSheet("""
        #     background-color: #444444;
        #     color: white;
        #     font-size: 18px;
        #     font-weight: bold;
        #     border-radius: 5px;
        # """)
        # title_container.addStretch()
        # title_container.addWidget(title_label)
        # title_container.addStretch()
        # main_layout.addLayout(title_container)

        map_container = QHBoxLayout()
        self.map_file = "map.html"
        self.web_view = QWebEngineView()
        self.web_view.setFixedHeight(250)
        self.web_view.setFixedWidth(500)

        map_container.addWidget(self.web_view)
        main_layout.addLayout(map_container)

        # "랜덤 위치 선정" 버튼
        random_button = QPushButton("랜덤 위치 선정")
        random_button.setStyleSheet("background-color: #666666; color: white; font-size: 16px;")
        random_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        random_button.clicked.connect(self.random_location)

        main_layout.addWidget(random_button)

        # 경로 추천 입력란
        search_container = QHBoxLayout()
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("출발지 입력 (예: 서울역)")
        self.input_line.setFixedWidth(500)
        search_container.addWidget(self.input_line)
        self.input_line.returnPressed.connect(self.recommend_route_from_input)
        main_layout.addLayout(search_container)

        # 주변 관광지 추천 및 숙소 추천 버튼들
        button_grid_1 = QHBoxLayout()
        button_grid_1.setSpacing(10)
        btn1 = QPushButton("주변 관광지 추천")
        btn2 = QPushButton("숙소 추천")
        for btn in (btn1, btn2):
            btn.setStyleSheet("background-color: #666666; color: white; font-size: 16px;")
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        button_grid_1.addWidget(btn1)
        button_grid_1.addWidget(btn2)
        main_layout.addLayout(button_grid_1)

        self.setLayout(main_layout)

        # 기존 버튼 이벤트
        btn1.clicked.connect(self.on_button1_clicked)
        btn2.clicked.connect(self.on_button2_clicked)

        # 랜덤 위치 저장용
        self.random_lat = None
        self.random_lon = None

    def random_location(self):
        # 한국 내에서 랜덤으로 위치를 선택하는 방법 (위도, 경도 범위)
        lat_min, lat_max = 33.0, 38.5  # 한국의 위도 범위
        lon_min, lon_max = 126.0, 130.0  # 한국의 경도 범위

        self.random_lat = random.uniform(lat_min, lat_max)
        self.random_lon = random.uniform(lon_min, lon_max)

        print(f"랜덤 위치: 위도 {self.random_lat}, 경도 {self.random_lon}")

        # 지도 업데이트
        self.update_map(self.random_lat, self.random_lon)

    def update_map(self, lat, lon):
        # Folium으로 지도 생성
        m = folium.Map(location=[lat, lon], zoom_start=12)
        folium.Marker([lat, lon], tooltip="랜덤 위치").add_to(m)

        # 저장하고 웹뷰에서 불러오기
        m.save(self.map_file)
        self.web_view.load(QUrl.fromLocalFile(os.path.abspath(self.map_file)))

    def recommend_route_from_input(self):
        # 경로 추천 입력란에서 출발지 입력받기
        user_input = self.input_line.text()
        if not user_input:
            print("출발지를 입력해주세요.")
            return

        # 출발지의 지오코딩
        try:
            geolocator = Nominatim(user_agent="mapApp")
            start_loc = geolocator.geocode(user_input, timeout=10)

            if not start_loc:
                print("위치를 찾을 수 없습니다.")
                return

            start = [start_loc.latitude, start_loc.longitude]

            # 랜덤 위치가 설정되지 않았다면 경로를 표시하지 않음
            if self.random_lat is None or self.random_lon is None:
                print("랜덤 위치가 설정되지 않았습니다.")
                return

            end = [self.random_lat, self.random_lon]

            # 경로를 지도에 표시
            m = folium.Map(location=start, zoom_start=14)
            folium.Marker(start, tooltip=f"출발지: {user_input}").add_to(m)
            folium.Marker(end, tooltip="도착지: 랜덤 위치").add_to(m)
            folium.PolyLine([start, end], color="blue", weight=5, opacity=0.8).add_to(m)

            map_file = "map.html"
            m.save(map_file)
            self.web_view.load(QUrl.fromLocalFile(os.path.abspath(map_file)))

        except GeocoderTimedOut:
            print("지오코딩 시간이 초과되었습니다.")

    def on_button1_clicked(self):
        print("주변 관광지 추천 클릭됨")

    def on_button2_clicked(self):
        print("숙소 추천 클릭됨")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
