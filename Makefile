.PHONY: help test test-unit test-smoke build build-local deploy-local deploy-k8s setup-monitoring clean

help: ## Показать справку по командам
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

test: test-unit test-smoke ## Запустить все тесты

test-unit: ## Запустить unit тесты
	@echo "🧪 Запуск unit тестов..."
	python -m pytest tests/unit/ -v

test-smoke: ## Запустить smoke тесты
	@echo "🚀 Запуск smoke тестов..."
	python -m pytest tests/smoke/ -v

build: ## Сборка Docker образов для всех сервисов
	@echo "🔨 Сборка Docker образов..."
	docker build -t telemetry-generator:latest services/telemetry-generator/
	docker build -t telemetry-collector:latest services/telemetry-collector/
	docker build -t telemetry-processor:latest services/telemetry-processor/

build-local: ## Локальная сборка и запуск
	@echo "🏠 Локальная сборка и запуск..."
	docker-compose -f docker-compose.dev.yml up --build -d

deploy-local: ## Деплой в локальный Docker Compose
	@echo "🚀 Деплой в локальный Docker Compose..."
	docker-compose -f docker-compose.dev.yml up -d

deploy-k8s: ## Деплой в Kubernetes через Helm
	@echo "☸️ Деплой в Kubernetes..."
	helm upgrade --install telemetry ./k8s/helm --namespace telemetry --create-namespace

setup-monitoring: ## Настройка мониторинга на SRV сервере
	@echo "📊 Настройка мониторинга на SRV..."
	@echo "1. Подключитесь к SRV серверу: ssh debian@<SRV_IP>"
	@echo "2. Перейдите в директорию: cd ~/monitoring"
	@echo "3. Запустите стек: docker-compose up -d"
	@echo "4. Откройте Grafana: http://<SRV_IP>:3000"

clean: ## Очистка Docker ресурсов
	@echo "🧹 Очистка Docker ресурсов..."
	docker-compose -f docker-compose.dev.yml down -v
	docker system prune -f

status: ## Показать статус сервисов
	@echo "📊 Статус сервисов:"
	@echo "Локальные (Docker Compose):"
	docker-compose -f docker-compose.dev.yml ps 2>/dev/null || echo "Docker Compose не запущен"
	@echo ""
	@echo "Kubernetes:"
	kubectl get pods -n telemetry 2>/dev/null || echo "Kubernetes недоступен"
	@echo ""
	@echo "SRV мониторинг:"
	@echo "Grafana: http://51.250.107.234:3000"
	@echo "VictoriaMetrics: http://51.250.107.234:8428"
	@echo "vmagent: http://51.250.107.234:8429"

logs: ## Показать логи локальных сервисов
	@echo "📝 Логи локальных сервисов:"
	docker-compose -f docker-compose.dev.yml logs -f

k8s-logs: ## Показать логи Kubernetes подов
	@echo "📝 Логи Kubernetes подов:"
	kubectl logs -f -n telemetry -l app.kubernetes.io/name=telemetry

monitoring-logs: ## Показать логи мониторинга на SRV
	@echo "📝 Логи мониторинга на SRV:"
	ssh ubuntu@51.250.107.234 "cd ~/monitoring && docker-compose logs -f"

