# DKUOpenSource-UnplannedTrip
즉흥 여행 프로그램


### 1. geofabric에서 한국 지도 데이터 다운로드받기
https://download.geofabrik.de/asia/south-korea.html에 접속한 후 south-korea-latest.orm.pbf 파일을 다운로드 받은 뒤 osrm_data 폴더를 새로 만들어 폴더 안에 집어넣기

### 2. 로컬 OSRM 서버를 만들기 위해 docker 다운로드 및 실행
https://docs.docker.com/desktop/setup/install/windows-install/에 접속한 후 운영체제에 알맞는 도커 허브를 다운로드 후 설치하기 및 docker 프로그램 실행

### 3. docker 서버의 OSRM 데이터 전처리하기
south-korea-latest.osm.pbf라는 지도 데이터를 읽어서 OSRM 서버를 위한 기본 데이터로 변하는 코드. car을 통해 차량 주행 기준으로 설정

docker run -t -v "${PWD}/osrm_data:/data" osrm/osrm-backend osrm-extract -p /opt/car.lua /data/south-korea-latest.osm.pbf

경로 분할 작업

docker run -t -v "${PWD}/osrm_data:/data" osrm/osrm-backend osrm-partition /data/south-korea-latest.osrm

도로별 가중치 적용

docker run -t -v "${PWD}/osrm_data:/data" osrm/osrm-backend osrm-customize /data/south-korea-latest.osrm

### 4. docker 서버 활용으로 로컬 OSRM 서버 생성
docker server를 현재의 south-korea-latest.osrm 파일을 데이터로 구동

docker run -t -i -p 5000:5000 -v "${PWD}/osrm_data:/data" osrm/osrm-backend osrm-routed --algorithm mld /data/south-korea-latest.osrm

위의 설정이 끝나면 test.py 실행을 통해 로컬 OSRM 서버에 요청을 하고, 응답을 통해 지도 데이터에 표시 및 파일 생성이 가능하다.
