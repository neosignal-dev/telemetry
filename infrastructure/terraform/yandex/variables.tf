variable "yc_token" { type = string }
variable "sa_key_file" { type = string default = "" }
variable "cloud_id" { type = string }
variable "folder_id" { type = string }
variable "zone" { type = string  default = "ru-central1-a" }
variable "sa_id" { type = string }
variable "k8s_version" { type = string default = "1.29" }
variable "srv_image_id" { type = string description = "Yandex.Cloud image id (e.g., ubuntu-22-04-lts)" }
variable "ssh_user" { type = string default = "ubuntu" }
variable "ssh_public_key" { type = string }
