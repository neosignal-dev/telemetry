# Telemetry — спутниковая телеметрия (Prod‑ready)

Проект моделирует сбор и обработку телеметрии от спутников (или IoT‑устройств):
- генерация событий (latency, bandwidth, battery, packet loss и т.д.),
- приём HTTP и постановка в очередь RabbitMQ,
- обработка и запись в Postgres,
- метрики Prometheus и дашборды Grafana,
- IaC (Terraform), автоматизация (Ansible), деплой в Kubernetes (Helm), CI/CD (GitHub Actions).

---

## Структура репозитория
- `services/` — исходники микросервисов (generator, collector, processor)
- `monitoring/` — локальный Prometheus и Grafana (provisioning)
- `srv/` — стек мониторинга/логирования и Alertmanager для отдельного сервера
- `k8s/helm/` — единый Helm‑чарт приложения
- `gitops/apps/` — манифесты FluxCD (GitRepository, HelmRelease, Kustomization)
- `infrastructure/terraform/yandex/` — Terraform (Yandex.Cloud)
- `ansible/` — плейбуки для `srv` (provisioning)
- `.github/workflows/` — CI/CD пайплайны GitHub Actions
- `docker-compose.dev.yml` — локальный запуск
- `tests/` — unit и smoke тесты
- `Makefile` — цели для тестов

---

## Локальный запуск (Docker Compose)
Требования: Docker + Docker Compose, macOS (Intel/ARM) или Linux.

```bash
docker compose -f docker-compose.dev.yml up --build
```

URL и доступы:
- RabbitMQ UI: http://localhost:15672 (user: telemetry, pass: telemetry)
- Postgres: localhost:5432 (db/user: telemetry, pass: example)
- Collector (FastAPI): http://localhost:8080/docs
- Processor (Prometheus): http://localhost:8000/metrics
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

Grafana: папка «Telemetry» → дашборд «Telemetry – Satellites».

Метрики:
- generator: `/metrics` на :9100 (`telemetry_generated_total`, `telemetry_generator_rate_hz`, `telemetry_generator_sat_count`, гистограммы домена)
- collector: `/metrics` (FastAPI Instrumentator) + `telemetry_collected_total{sat_id,region}`
- processor: `/metrics` на :8000 (`telemetry_ingested_total`, `telemetry_ingested_by_sat_total{sat_id,region}`, `telemetry_processing_latency_seconds`, ошибки БД)

Тесты:
```bash
make test           # unit
make test-smoke     # smoke (нужен поднятый compose‑стек)
```

---

## Облачная инфраструктура (Yandex.Cloud, Terraform)
Код Terraform: `infrastructure/terraform/yandex` — создаёт VPC, управляемый Kubernetes‑кластер (1 нода) и ВМ `srv` для мониторинга/CI.

Пример запуска:
```bash
cd infrastructure/terraform/yandex
export TF_VAR_yc_token=... TF_VAR_cloud_id=... TF_VAR_folder_id=... \
       TF_VAR_sa_id=... TF_VAR_srv_image_id=... \
       TF_VAR_ssh_public_key="$(cat ~/.ssh/id_rsa.pub)"
terraform init && terraform apply
```

Аутентификация в Yandex.Cloud:
- Через OAuth токен: экспортируйте `TF_VAR_yc_token`.
- Через ключ сервисного аккаунта: укажите путь к `sa_key_file` в `terraform.tfvars` или переменной окружения.

Kubeconfig кластера:
- После `terraform apply` получите эндпоинт из outputs.
- Настройте `kubectl` через `yc managed-kubernetes cluster get-credentials ...` или вручную сформируйте kubeconfig.

Выходные данные содержат: `srv_public_ip`, параметры кластера Kubernetes.

---

## Автоматизация srv (Ansible)
Плейбук: `ansible/srv/playbook.yml` — устанавливает Docker/Compose, разворачивает Grafana, VictoriaMetrics, vmagent, vmalert, Loki, Promtail, Alertmanager.

```bash
ansible-playbook -i "<srv_ip>," ansible/srv/playbook.yml --user ubuntu --private-key ~/.ssh/id_rsa
```

Дополнительно можно передать TELEGRAM токены для Alertmanager через переменные окружения контейнера (см. `srv/alertmanager/config.yml`).

---

## Деплой в Kubernetes (Helm)
Единый чарт: `k8s/helm` (generator, collector, processor). Ноды экспонируются через NodePort:
- processor: 30080, collector: 30081, generator: 30082

```bash
helm upgrade --install telemetry k8s/helm \
  --set image.repositoryPrefix=ghcr.io/<OWNER>/telemetry- \
  --set image.tag=<COMMIT_SHA> \
  --namespace telemetry --create-namespace
```

Зависимости кластера (K8s):
- RabbitMQ и Postgres НЕ провиженятся GitOps‑манифестами в текущей конфигурации. Для продакшна используйте управляемые сервисы облака, Helm‑чарты инфраструктуры или внешние ресурсы. Локально их роль выполняют контейнеры Docker Compose.

Для GitOps (FluxCD):
- `gitops/apps/repo.yaml` — GitRepository (укажите свой `url`),
- `gitops/apps/telemetry-helmrelease.yaml` — HelmRelease,
- `gitops/apps/telemetry-kustomization.yaml` — применяет каталог `gitops/apps`.
Примечание: можно выбрать один из путей доставки — FluxCD (GitOps) или GitHub Actions (deploy workflow).

---

## CI/CD (GitHub Actions)
Workflows в `.github/workflows/`:
- `ci.yml`: unit‑тесты, сборка и пуш образов в GHCR с тегом `shortSHA`.
- `deploy.yml`: деплой Helm‑чарта. Требуется секрет `KUBECONFIG_CONTENT` (содержимое kubeconfig), а также стандартный `GITHUB_TOKEN` для GHCR.

Теги образов: `ghcr.io/<OWNER>/telemetry-<service>:<shortSHA>`.

---

## Мониторинг и алертинг
- Локально: `monitoring/prometheus/prometheus.yml` (scrape локальных сервисов), Grafana авто‑провиженит datasource и дашборды из `monitoring/grafana/provisioning`.
- На `srv`: стек в `srv/docker-compose.yml` (Grafana, VictoriaMetrics, vmagent, vmalert, Loki, Promtail, Alertmanager).
- Alertmanager → Telegram: задайте `TELEGRAM_BOT_TOKEN` и `TELEGRAM_CHAT_ID` (см. `srv/alertmanager/config.yml`).
- Пример правил: `srv/vmalert/rules.yml` (алерт на падение processor).

Логин в Grafana: по умолчанию `admin/admin` (если не переопределён переменными окружения).

Для K8s‑кластерa на `srv` укажите NodePort‑таргеты в `srv/vmagent/prometheus.yml` (замените `<NODE_IP>` на IP ноды):
- processor: `<NODE_IP>:30080`, collector: `<NODE_IP>:30081`

---

## Пошаговые инструкции
Для разработчика:
1) `docker compose -f docker-compose.dev.yml up --build`
2) Открыть Prometheus/Grafana, проверить метрики и дашборд
3) Запустить `make test`/`make test-smoke`

Для DevOps:
1) `terraform apply` в `infrastructure/terraform/yandex` (получить `srv_public_ip` и доступ к K8s)
2) `ansible-playbook` на `srv` для мониторинга/логирования
3) Настроить FluxCD (см. `gitops/apps/*.yaml`), указать репозиторий и реестр
4) Настроить GitHub Secrets: `KUBECONFIG_CONTENT` (deploy), (опционально) registry‑логин
5) Push в `main` → CI соберёт образы и задеплоит Helm‑чарт

Тесты:
```bash
make test           # unit
make test-smoke     # smoke (нужен поднятый compose‑стек)
```

---

## Замечания по безопасности
- Секреты не коммитятся — используйте GitHub Secrets, Vault или Kubernetes Secrets.
- Переменные окружения для production выносите в Secret/External secrets.
