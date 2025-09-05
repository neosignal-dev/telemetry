# Satellite Telemetry System

Полнофункциональная система телеметрии спутников с полным циклом CI/CD, мониторингом и логированием.

## Архитектура

- **Kubernetes**: K3s кластер (1 master + 1 worker)
- **Приложение**: 3 микросервиса (generator, collector, processor) + PostgreSQL + RabbitMQ
- **Мониторинг**: VictoriaMetrics + Grafana + Loki + Alertmanager
- **CI/CD**: GitHub Actions с автоматическим деплоем по Git тегам
- **Инфраструктура**: Yandex Cloud (Terraform + Ansible)

## Быстрый старт

### 1. Развертывание инфраструктуры

```bash
# Настройка Yandex Cloud
export YC_TOKEN="your_oauth_token"
export YC_CLOUD_ID="your_cloud_id"
export YC_FOLDER_ID="your_folder_id"

# Развертывание инфраструктуры
cd infrastructure/terraform/yandex
terraform init
terraform plan
terraform apply
```

### 2. Настройка серверов

```bash
# Создание inventory файла
cp ansible/inventory.example.yml ansible/inventory.yml
# Отредактируйте inventory.yml с IP адресами ваших серверов

# Создание файла секретов
cp ansible/secrets.example.yml ansible/secrets.yml
# Отредактируйте secrets.yml с вашими секретами

# Развертывание конфигурации
cd ansible
ansible-playbook -i inventory.yml playbook.yml
```

### 3. Деплой приложения

```bash
# Создание Git тега для автоматического деплоя
git tag v1.0.0
git push origin v1.0.0
```

## Доступ к сервисам

- **Приложение**: http://WORKER_IP:30081
- **Grafana**: http://SRV_IP:3000
- **VictoriaMetrics**: http://SRV_IP:8428
- **Loki**: http://SRV_IP:3100
- **Alertmanager**: http://SRV_IP:9093

## Структура проекта

```
├── infrastructure/terraform/yandex/  # Terraform конфигурации
├── ansible/                          # Ansible плейбуки и роли
├── k8s/helm/                         # Helm чарт приложения
├── services/                         # Исходный код микросервисов
├── monitoring/                       # Конфигурации мониторинга
├── .github/workflows/                # CI/CD пайплайны
└── tests/                           # Тесты
```

## Мониторинг

### Метрики
- Время отклика приложения
- Количество запросов (RPS)
- Ошибки базы данных
- Глубина очереди RabbitMQ
- Статус подов и нод

### Логирование
- Автоматический сбор логов всех подов
- Централизованное хранение в Loki
- Поиск и анализ через Grafana

### Алертинг
- Уведомления в Telegram
- Алерты на недоступность сервисов
- Мониторинг ресурсов сервера

## CI/CD

Автоматический пайплайн при создании Git тега:

1. **Build**: Сборка Docker образов
2. **Push**: Отправка в GitHub Container Registry
3. **Deploy**: Развертывание в Kubernetes через Helm
4. **Test**: Smoke тесты


## Требования

- Terraform >= 1.0
- Ansible >= 2.9
- kubectl >= 1.20
- Helm >= 3.0
- Yandex Cloud CLI

## Лицензия

MIT