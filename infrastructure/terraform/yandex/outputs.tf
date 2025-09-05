output "k3s_master_public_ip" {
  description = "K3s master public IP"
  value       = yandex_compute_instance.k3s_master.network_interface.0.nat_ip_address
}

output "k3s_master_private_ip" {
  description = "K3s master private IP"
  value       = yandex_compute_instance.k3s_master.network_interface.0.ip_address
}

output "k3s_worker_public_ip" {
  description = "K3s worker public IP (app node)"
  value       = yandex_compute_instance.k3s_worker.network_interface.0.nat_ip_address
}

output "k3s_worker_private_ip" {
  description = "K3s worker private IP"
  value       = yandex_compute_instance.k3s_worker.network_interface.0.ip_address
}

output "srv_public_ip" {
  description = "Monitoring server public IP"
  value       = yandex_compute_instance.srv.network_interface.0.nat_ip_address
}

output "srv_private_ip" {
  description = "Monitoring server private IP"
  value       = yandex_compute_instance.srv.network_interface.0.ip_address
}

# output "app_node_static_ip" {
#   description = "Static IP for app node"
#   value       = yandex_vpc_address.app_node.external_ipv4_address[0].address
# }

output "ssh_connection_info" {
  description = "SSH connection information"
  value = {
    user   = var.ssh_user
    master = "ssh ${var.ssh_user}@${yandex_compute_instance.k3s_master.network_interface.0.nat_ip_address}"
    worker = "ssh ${var.ssh_user}@${yandex_compute_instance.k3s_worker.network_interface.0.nat_ip_address}"
    srv    = "ssh ${var.ssh_user}@${yandex_compute_instance.srv.network_interface.0.nat_ip_address}"
  }
}

output "service_urls" {
  description = "Service URLs"
  value = {
    app_collector   = "http://${yandex_compute_instance.k3s_worker.network_interface.0.nat_ip_address}:30081"
    app_processor   = "http://${yandex_compute_instance.k3s_worker.network_interface.0.nat_ip_address}:30080"
    app_generator   = "http://${yandex_compute_instance.k3s_worker.network_interface.0.nat_ip_address}:30082"
    jenkins         = "http://${yandex_compute_instance.srv.network_interface.0.nat_ip_address}:8080"
    grafana         = "http://${yandex_compute_instance.srv.network_interface.0.nat_ip_address}:3000"
    victoriametrics = "http://${yandex_compute_instance.srv.network_interface.0.nat_ip_address}:8428"
  }
}
