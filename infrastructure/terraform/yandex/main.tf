terraform {
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = "~> 0.118"
    }
  }
}

provider "yandex" {
  service_account_key_file = var.sa_key_file != "" ? var.sa_key_file : null
  token                    = var.sa_key_file == "" ? var.yc_token : null
  cloud_id                 = var.cloud_id
  folder_id                = var.folder_id
  zone                     = var.zone
}

# Use existing VPC Network
data "yandex_vpc_network" "telemetry" {
  name = "default"
}

# Use existing VPC Subnet
data "yandex_vpc_subnet" "telemetry" {
  name = "default-ru-central1-a"
}

# Use existing Security Group
data "yandex_vpc_security_group" "telemetry" {
  name = "default-sg-enptptv6bk23eamgik91"
}

# Static IP for app node (commented out due to permissions)
# resource "yandex_vpc_address" "app_node" {
#   name = "telemetry-app-node-ip"
#   external_ipv4_address {
#     zone_id = var.zone
#   }
# }

# K3s Master
resource "yandex_compute_instance" "k3s_master" {
  name        = "telemetry-k3s-master"
  platform_id = "standard-v3"
  zone        = var.zone

  resources {
    cores  = 2
    memory = 4
  }

  boot_disk {
    initialize_params {
      image_id = var.debian_image_id
      size     = 40
      type     = "network-ssd"
    }
  }

  network_interface {
    subnet_id          = data.yandex_vpc_subnet.telemetry.id
    nat                = true
    security_group_ids = [data.yandex_vpc_security_group.telemetry.id]
  }

  metadata = {
    ssh-keys = "${var.ssh_user}:${var.ssh_public_key}"
  }
}

# K3s Worker
resource "yandex_compute_instance" "k3s_worker" {
  name        = "telemetry-k3s-worker"
  platform_id = "standard-v3"
  zone        = var.zone

  resources {
    cores  = 2
    memory = 4
  }

  boot_disk {
    initialize_params {
      image_id = var.debian_image_id
      size     = 40
      type     = "network-ssd"
    }
  }

  network_interface {
    subnet_id          = data.yandex_vpc_subnet.telemetry.id
    nat                = true
    security_group_ids = [data.yandex_vpc_security_group.telemetry.id]
  }

  metadata = {
    ssh-keys = "${var.ssh_user}:${var.ssh_public_key}"
  }
}

# Monitoring Server
resource "yandex_compute_instance" "srv" {
  name        = "telemetry-srv"
  platform_id = "standard-v3"
  zone        = var.zone

  resources {
    cores  = 4
    memory = 8
  }

  boot_disk {
    initialize_params {
      image_id = var.debian_image_id
      size     = 120
      type     = "network-ssd"
    }
  }

  network_interface {
    subnet_id          = data.yandex_vpc_subnet.telemetry.id
    nat                = true
    security_group_ids = [data.yandex_vpc_security_group.telemetry.id]
  }

  metadata = {
    ssh-keys = "${var.ssh_user}:${var.ssh_public_key}"
  }
}