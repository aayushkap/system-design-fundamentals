terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0.2"
    }
  }
}

provider "docker" {
  host = "unix:///var/run/docker.sock"
}

# Build the FastAPI Docker image (single image for all containers)
resource "docker_image" "fastapi_app" {
  name = "fastapi-terraform-app:latest"
  build {
    context    = "../app"
    dockerfile = "Dockerfile"
    tag        = ["fastapi-terraform-app:latest"]
    label = {
      author      = "terraform"
      environment = "development"
    }
  }
  keep_locally = true
}

# Create a custom network for all services
resource "docker_network" "app_network" {
  name   = "fastapi_demo_network"
  driver = "bridge"

  labels {
    label = "environment"
    value = "development"
  }
}

# Create multiple FastAPI containers using for_each
resource "docker_container" "fastapi_backends" {
  for_each = var.backend_servers

  name  = "fastapi-${each.key}"
  image = docker_image.fastapi_app.name  # do not use .image_id here.

  ports {
    internal = 8000
    external = each.value.external_port
  }

  networks_advanced {
    name = docker_network.app_network.name
  }

  env = [
    "SERVER_ID=${each.key}",
    "SERVER_PORT=${each.value.external_port}",
    "ENVIRONMENT=${each.value.environment}",
    "LOG_LEVEL=${each.value.log_level}",
    "MANAGED_BY=terraform"
  ]

  restart = "unless-stopped"

  labels {
    label = "app"
    value = "fastapi-demo"
  }

  labels {
    label = "server_id"
    value = each.key
  }

  labels {
    label = "provisioned_by"
    value = "terraform"
  }

  lifecycle { # To prevent previous container shutdown on scaling up
    ignore_changes = [
      image,
      network_mode,
      working_dir,
      command,
      entrypoint,
    ]
  }
}

# Outputs
output "backend_servers" {
  value = {
    for key, container in docker_container.fastapi_backends : key => {
      id   = container.id
      name = container.name
      port = container.ports[0].external
      url  = "http://localhost:${container.ports[0].external}"
    }
  }
  description = "Information about all backend servers"
}


output "network_name" {
  value       = docker_network.app_network.name
  description = "Docker network name"
}
