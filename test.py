import requests
import folium
import webview
import random
from geopy.geocoders import Nominatim

#도커 서버 실행 명령어
#docker run -t -i -p 5000:5000 -v "${PWD}/osrm_data:/data" osrm/osrm-backend osrm-routed --algorithm mld /data/south-korea-latest.osrm

# start와 end만 일정 범위 내의 난수를 생성하도록 만들면 일정 범위 내의 좌표만 만들도록 가능 - 간단하게 가능
# 목적지 매핑은 난수를 생성한 후 난수값을 확인해서 범위 내의 난수는 특정 지역의 좌표 or 역으로 출발지를 지정하도록 수정
# - 여기서는 카카오 로컬 API 사용이 필요할듯?
# 출발지와 목적지 좌표 (예: 제주도 일부)

# 입력받은 주소값을 좌표로 변환해서 start에 할당
address = '죽전캠퍼스 경기도 용인시 수지구 죽전로 152'
geoloc = Nominatim(user_agent = 'Random_Trip', timeout=None)
geo = geoloc.geocode(address)
lat = str(geo.latitude)
log = str(geo.longitude)



# end는 난수 생성기를 통해 일정 범위 내의 목적지만 만들기
## 추후 카카오 로컬 API 를 통해 나온 난수 값의 범위 내의 역으로 목적지를 지정

start = (lat, log)  # 테스트용 위도, 경도
end = (33.3842, 126.3323) # 제주도
# end = (34.1433, 126.8543) # 청산도
# end = (33.0000, 126.5000) # 바다 한가운데


# OSRM API 요청
url = f"http://localhost:5000/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}?overview=full&geometries=geojson&steps=true"
response = requests.get(url)

if response.status_code != 200:
    print("경로 요청 실패:", response.text)
    exit()

data = response.json()
route = data['routes'][0]['geometry']['coordinates']  # [[경도, 위도], ...]

# 좌표 포맷을 folium 용으로 변환 (위도, 경도 순서)
route_course = [(coord[1], coord[0]) for coord in route]

# 지도 생성 (출발지 중심)
m = folium.Map(location=start, zoom_start=13)

# 경로 선 그리기
folium.PolyLine(route_course, color="blue", weight=5).add_to(m)

# 출발지 & 도착지 마커
folium.Marker(start, tooltip="출발지").add_to(m)
folium.Marker(end, tooltip="도착지").add_to(m)

# 결과 저장 및 열기
m.save("route_map.html")
print("지도 생성 완료: route_map.html")

# html 파일을 창에서 열기
window = webview.create_window('just test!', "route_map.html")

webview.start()
