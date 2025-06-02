import geopandas as gpd
from shapely.geometry import Point
import random
import pandas as pd

# ✅ 무작위 좌표 생성 함수
def generate_random_point_within(gdf):
    country_shape = gdf.union_all()
    minx, miny, maxx, maxy = country_shape.bounds

    while True:
        lon = random.uniform(minx, maxx)
        lat = random.uniform(miny, maxy)
        point = Point(lon, lat)
        if country_shape.contains(point):
            return point, lat, lon

# ✅ GeoJSON 로드 및 좌표계 설정
gdf = gpd.read_file("GeoJson/korea_municipalities.geojson")
if gdf.crs is None or gdf.crs.to_string() != "EPSG:4326":
    gdf = gdf.set_crs("EPSG:4326")

# ✅ 중심좌표 CSV 로드
center_df = pd.read_csv("행정구역 중심좌표.csv")

# ✅ 무작위 점 생성
point, lat, lon = generate_random_point_within(gdf)

# ✅ 해당 점이 속한 행정구역 찾기
matched = gdf[gdf.contains(point)]
if matched.empty:
    print("⚠️ 좌표가 행정구역 경계에 포함되지 않음.")
else:
    region_name = matched.iloc[0]['name']
    print(f"📍 선택된 무작위 행정구역: {region_name}")

    # ✅ 중심좌표 매칭
    match = center_df[center_df['행정구역'] == region_name]
    if not match.empty:
        lat_center = round(match.iloc[0]['위도'], 4)
        lon_center = round(match.iloc[0]['경도'], 4)

        result_df = pd.DataFrame([{
            "행정구역": region_name,
            "위도": lat_center,
            "경도": lon_center
        }])

        result_df.to_csv("무작위_행정구역_중심좌표.csv", index=False, encoding="utf-8-sig")
        print("✅ 무작위 행정구역 중심좌표 CSV 저장 완료.")
    else:
        print("❌ 중심좌표 CSV에서 해당 행정구역을 찾을 수 없습니다.")
