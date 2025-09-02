terraform {
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = "~> 0.118"
    }
  }
}

provider "yandex" {
  token     = var.yc_token
  cloud_id  = var.cloud_id
  folder_id = var.folder_id
  zone      = var.zone
}

resource "yandex_vpc_network" "this" {
  name = "telemetry-net"
}

resource "yandex_vpc_subnet" "this" {
  name           = "telemetry-subnet"
  zone           = var.zone
  network_id     = yandex_vpc_network.this.id
  v4_cidr_blocks = ["10.10.0.0/24"]
}

resource "yandex_kubernetes_cluster" "this" {
  name        = "telemetry-k8s"
  network_id  = yandex_vpc_network.this.id
  master {
    version   = var.k8s_version
    zonal {
      zone      = var.zone
      subnet_id = yandex_vpc_subnet.this.id
    }
    public_ip = true
  }
  service_account_id      = var.sa_id
  node_service_account_id = var.sa_id
  release_channel         = "RAPID"
}

resource "yandex_kubernetes_node_group" "apps" {
  cluster_id = yandex_kubernetes_cluster.this.id
  name       = "apps"
  version    = var.k8s_version
  instance_template {
    platform_id = "standard-v3"
    resources {
      cores  = 2
      memory = 4
    }
    boot_disk {
      type = "network-ssd"
      size = 30
    }
    network_interface {
      subnet_ids = [yandex_vpc_subnet.this.id]
      nat        = true
    }
  }
  scale_policy {
    fixed_scale {
      size = 1
    }
  }
}

resource "yandex_compute_instance" "srv" {
  name        = "telemetry-srv"
  platform_id = "standard-v3"
  resources {
    cores  = 2
    memory = 4
  }
  boot_disk {
    initialize_params {
      image_id = var.srv_image_id
      size     = 20
    }
  }
  network_interface {
    subnet_id = yandex_vpc_subnet.this.id
    nat       = true
  }
  metadata = {
    ssh-keys = "${var.ssh_user}:${var.ssh_public_key}"
  }
}
