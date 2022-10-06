install-deps:
	 sudo apt-get update
	 xargs -r -a packages.txt sudo apt-get install -y
	 pip install -r requirements.txt
	 cd frontend && npm install && cp .env.development.example .env.development && cp .env.example .env
build-client:
	cd frontend && npm install && PUBLIC_DEV_MODE=PROD npm run build && rm -rf ../static && cp -r build/ ../static/
build-dev:
	cd frontend && npm install && npm run build-dev && rm -rf ../static && cp -r build/ ../static/
run-front-dev:
	cd frontend && npm install && npm run dev
run-prod:
	python app.py
build-all: run-prod