# Руководство по развертыванию

## Предварительные требования

1. **Yandex Cloud аккаунт** с настроенным OAuth токеном
2. **SSH ключ** для доступа к серверам
3. **GitHub репозиторий** с настроенными секретами

## Пошаговое развертывание

### Шаг 1: Подготовка окружения

```bash
# Клонирование репозитория
git clone <repository-url>
cd telemetry

# Настройка переменных окружения
cp env.example .env
# Отредактируйте .env файл с вашими данными

# Создание inventory файла
cp ansible/inventory.example.yml ansible/inventory.yml
# Отредактируйте inventory.yml с IP адресами ваших серверов

# Создание файла секретов
cp ansible/secrets.example.yml ansible/secrets.yml
# Отредактируйте secrets.yml с вашими секретами
```

### Шаг 2: Настройка Yandex Cloud

```bash
# Установка Yandex Cloud CLI
curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash

# Инициализация
yc init

# Настройка переменных
export YC_TOKEN="your_oauth_token"
export YC_CLOUD_ID="your_cloud_id" 
export YC_FOLDER_ID="your_folder_id"
```

### Шаг 3: Развертывание инфраструктуры

```bash
cd infrastructure/terraform/yandex

# Инициализация Terraform
terraform init

# Планирование изменений
terraform plan

# Применение конфигурации
terraform apply
```

### Шаг 4: Настройка серверов

```bash
cd ../../ansible

# Обновление inventory с полученными IP адресами
vim ansible/inventory.yml

# Развертывание конфигурации
ansible-playbook -i inventory.yml playbook.yml
```

### Шаг 5: Деплой приложения

```bash
# Создание тега для автоматического деплоя
git tag v1.0.0
git push origin v1.0.0
```

## Проверка развертывания

### Проверка инфраструктуры
```bash
# Статус серверов
ssh telemetry@<SRV_IP> "kubectl get nodes"

# Статус подов
ssh telemetry@<SRV_IP> "kubectl get pods -n telemetry"
```

### Проверка приложения
```bash
# Доступность приложения
curl http://<WORKER_IP>:30081/health

# Метрики
curl http://<WORKER_IP>:30081/metrics
```

### Проверка мониторинга
```bash
# Grafana
open http://<SRV_IP>:3000

# VictoriaMetrics
curl http://<SRV_IP>:8428/api/v1/query?query=up

# Loki
curl http://<SRV_IP>:3100/loki/api/v1/label
```

## Устранение неполадок

### Проблемы с Terraform
```bash
# Очистка состояния
terraform destroy
rm -rf .terraform/
terraform init
```

### Проблемы с Ansible
```bash
# Проверка подключения
ansible all -i inventory.yml -m ping

# Запуск с отладкой
ansible-playbook -i inventory.yml playbook.yml -vvv
```

### Проблемы с Kubernetes
```bash
# Проверка логов
kubectl logs -n telemetry <pod-name>

# Описание пода
kubectl describe pod -n telemetry <pod-name>
```

## Масштабирование

### Увеличение количества реплик
```bash
kubectl scale deployment collector -n telemetry --replicas=3
```

### Добавление нод в кластер
```bash
# На новом сервере
curl -sfL https://get.k3s.io | K3S_URL=https://<MASTER_IP>:6443 K3S_TOKEN=<TOKEN> sh -
```

## Резервное копирование

### База данных
```bash
kubectl exec -n telemetry postgresql-0 -- pg_dump -U postgres telemetry > backup.sql
```

### Конфигурации
```bash
# Экспорт всех ресурсов
kubectl get all -n telemetry -o yaml > telemetry-backup.yaml
```