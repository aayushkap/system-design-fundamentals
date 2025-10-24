variable "backend_servers" {
  description = "Map of backend server configurations"
  type = map(object({
    external_port = number
    environment   = string
    log_level     = string
  }))
}
