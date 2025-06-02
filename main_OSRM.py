import argparse
import importlib
import json
import requests
from shapely.geometry import Point
import geopandas as gpd
import sys
import os

def is_point_in_land_excluding_islands(lat, lon, gdf):
    # 섬 지역 이름 포함한 행정구역 제외
    island_keywords = [
    "제주시", "서귀포시",             # 제주도
    "울릉군", "독도",                 # 울릉도 및 독도
    "흑산면", "하의면", "신의면", "도초면", "비금면",  # 신안군 주요 섬들
    "백령면", "대청면", "덕적면", "자월면",             # 인천 옹진군 섬들
    "연평면", "영흥면", "북도면", "덕적도", "소청도",
    "거문면", "금산면",              # 여수시 섬
    "매물도", "비진도",              # 통영 일대 섬 (비공식이지만 인식 보완용)
    "조도면",                         # 진도군 조도
    "가거도", "소흑산도", "마라도", "우도", "추자면"  # 개별 섬 또는 섬 전체면
]
    
    # 'ADM_NM' 또는 'name' 컬럼 사용 여부 확인 필요
    col_name = "ADM_NM" if "ADM_NM" in gdf.columns else "name"
    
    gdf_filtered = gdf[~gdf[col_name].str.contains("|".join(island_keywords), na=False)]
    
    point = Point(lon, lat)
    return gdf_filtered.contains(point).any()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--origin", type=str, required=True, help="출발지 (예: 서울시 용산구)")
    parser.add_argument("--dest_lat", type=float, required=True, help="도착지 위도")
    parser.add_argument("--dest_lon", type=float, required=True, help="도착지 경도")
    parser.add_argument("--api_key", type=str, required=True, help="Google API Key")
    args = parser.parse_args()

    origin = args.origin
    dest_lat = args.dest_lat
    dest_lon = args.dest_lon
    api_key = args.api_key

    # Step 1: Google Directions API 호출 (대중교통)
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={dest_lat},{dest_lon}&mode=transit&key={api_key}"
    response = requests.get(url)
    directions_result = response.json()

    status = directions_result.get("status", "")

    # Step 2: GeoJSON 기반 섬 판단
    gdf = gpd.read_file("GeoJson/korea_municipalities.geojson")
    if gdf.crs is None or gdf.crs.to_string() != "EPSG:4326":
        gdf = gdf.set_crs("EPSG:4326")

    point = Point(dest_lon, dest_lat)

    # Step 3: 조건 판단
    if "제주" in origin:
        is_island = True
        print("섬 출발지 로직 실행 중 (true.py)")
    elif status == "ZERO_RESULTS":
        if is_point_in_land_excluding_islands(dest_lat, dest_lon, gdf):
            is_island = False
            print("📍 목적지는 육지에 존재하지만 대중교통 경로가 없습니다.")
        else:
            is_island = True
            print("🏝️ 섬 목적지 로직 실행 중 (true.py)")
    else:
        is_island = False
        print("🛣️ 일반 육지 목적지 로직 실행 중 (false.py)")
        print("🚀 현재 Python 경로:", sys.executable)

    # Step 4: 모듈 실행
    if is_island:
        true_module = importlib.import_module("true")
        true_module.run(origin, dest_lat, dest_lon, api_key)
    else:
        false_module = importlib.import_module("false")
        false_module.run(origin, dest_lat, dest_lon, api_key)

    if os.path.exists("random_map.html"):
        import shutil
        shutil.copyfile("random_map.html", "random_map_backup.html")

if __name__ == "__main__":
    main()