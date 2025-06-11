# DKUOpenSource-UnplannedTrip
즉흥 여행 프로그램

목적지를 정하는 것의 번거로움은 줄이고, 어디로 튈지 모르는 여행을 통해 새로운 경험과 예측할 수 없는 미래에 대한 설레임을 즐기도록 도와줄 수 있는 프로그램
랜덤으로 선정한 목적지에 대한 자차 경로 및 대중교통 경로를 시각화해서 보여주고, 목적지 주변의 관광 명소, 맛집, 숙소 등의 위치정보와 네이버 검색엔진 연동을 통한 상세 정보까지 확인 가능


사전 작업

### 1. geofabric에서 한국 지도 데이터 다운로드받기
https://download.geofabrik.de/asia/south-korea.html 에 접속한 후 south-korea-latest.orm.pbf 파일을 다운로드 받은 뒤 osrm_data 폴더를 새로 만들어 폴더 안에 집어넣기

### 2. 로컬 OSRM 서버를 만들기 위해 docker 다운로드 및 실행
https://docs.docker.com/desktop/setup/install/windows-install/ 에 접속한 후 운영체제에 알맞는 도커 허브를 다운로드 후 설치하기 및 docker 프로그램 실행

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

위의 설정이 끝나면 main.py 실행을 통해 즉흥 여행 프로그램 실행이 가능하다.

* google directions API는 key 값이 있어야 실행 가능한데, 현재 github상에 올라와 있는 코드는 보안 상의 문제로 마스킹 처리가 되어 있음.
* google directions API 키를 직접 발급 받아 main의 API_KEY에 넣고 실행하는 것을 권장하며, 혹시 필요하다면 메일로 보내드리겠습니다.

google directions API는 실시간 대중교통 정보를 포함하기 때문에, 교통수단이 없는 시간대라면 비정상적으로 보이는 시간이 표시될 가능성이 있으나 이는 정상적인 현상이다.
