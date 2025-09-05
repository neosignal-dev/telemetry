variable "yc_token" {
  type        = string
  default     = ""
  description = "Yandex Cloud OAuth token"
}

variable "sa_key_file" {
  type        = string
  default     = ""
  description = "Path to service account key file"
}

variable "cloud_id" {
  type        = string
  description = "Yandex Cloud ID"
}

variable "folder_id" {
  type        = string
  description = "Yandex Cloud folder ID"
}

variable "zone" {
  type        = string
  default     = "ru-central1-a"
  description = "Yandex Cloud zone"
}

variable "debian_image_id" {
  type        = string
  description = "Debian 12 image ID"
  default     = "fd8kdq6d0p8sij7h5qe3"
}

variable "ssh_user" {
  type        = string
  default     = "debian"
  description = "SSH user for VMs"
}

variable "ssh_public_key" {
  type        = string
  description = "SSH public key for VMs"
}
