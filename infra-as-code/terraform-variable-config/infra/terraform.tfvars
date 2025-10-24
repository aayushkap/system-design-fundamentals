backend_servers = {
  "server-1" = {
    external_port = 8001
    environment   = "development"
    log_level     = "debug"
  }
  "server-2" = {
    external_port = 8002
    environment   = "development"
    log_level     = "info"
  }
  "server-3" = {
    external_port = 8003
    environment   = "production"
    log_level     = "warning"
  }
}
