output "k8s_cluster_id" { value = yandex_kubernetes_cluster.this.id }
output "k8s_master_endpoint" { value = yandex_kubernetes_cluster.this.master.0.external_v4_endpoint }
output "srv_public_ip" { value = yandex_compute_instance.srv.network_interface.0.nat_ip_address }
