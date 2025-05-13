import geopandas as gpd
from shapely.geometry import Point
import random

def generate_random_point_within(gdf):
    # 모든 시군구 경계를 합쳐 하나의 Polygon으로 (멀티폴리곤 포함)
    country_shape = gdf.union_all()

    # GeoJSON은 EPSG:4326 기준이어야 함 (WGS84)
    minx, miny, maxx, maxy = country_shape.bounds

    while True:
        # 경계 바깥 포함 안 되게 랜덤 좌표 반복 생성
        lon = random.uniform(minx, maxx)
        lat = random.uniform(miny, maxy)
        point = Point(lon, lat)

        if country_shape.contains(point):
            return point, lat, lon

# GeoJSON 파일 불러오기
gdf = gpd.read_file("GeoJson/korea_municipalities.geojson")

# CRS 설정 확인 및 설정
if gdf.crs is None or gdf.crs.to_string() != "EPSG:4326":
    gdf = gdf.set_crs("EPSG:4326")

# 무작위 좌표 생성 (국토 내만)
point, lat, lon = generate_random_point_within(gdf)

print(f"대한민국 경계 내 무작위 좌표: 위도 {lat:.6f}, 경도 {lon:.6f}")

# 해당 행정구역 찾기
matched = gdf[gdf.contains(point)]

if not matched.empty:
    name = matched.iloc[0].get("name", "알 수 없음")  # 'name' 필드명에 맞게 수정
    print(f"이 좌표는 '{name}'(으)로 식별됩니다.")
else:
    print("⚠️ 좌표가 행정구역 경계에 포함되지 않음 (예외적 상황)")
