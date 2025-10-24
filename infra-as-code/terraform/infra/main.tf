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


# Build the FastAPI Docker image
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

# Create a custom network for the application
resource "docker_network" "app_network" {
  name   = "fastapi_demo_network"
  driver = "bridge"

  labels {
    label = "environment"
    value = "development"
  }
}

# Create the FastAPI container
resource "docker_container" "fastapi_app" {
  name  = "fastapi-app"
  image = docker_image.fastapi_app.image_id

  ports {
    internal = 8000
    external = 8000
  }

  networks_advanced {
    name = docker_network.app_network.name
  }

  env = [
    "ENVIRONMENT=development",
    "LOG_LEVEL=info",
    "MANAGED_BY=terraform"
  ]

  restart = "unless-stopped"

  labels {
    label = "app"
    value = "fastapi-demo"
  }

  labels {
    label = "provisioned_by"
    value = "terraform"
  }
}

# Outputs to display after applying
output "container_id" {
  value       = docker_container.fastapi_app.id
  description = "The ID of the FastAPI container"
}

output "container_name" {
  value       = docker_container.fastapi_app.name
  description = "The name of the FastAPI container"
}

output "app_url" {
  value       = "http://localhost:${docker_container.fastapi_app.ports[0].external}"
  description = "URL to access the FastAPI application"
}


output "network_name" {
  value       = docker_network.app_network.name
  description = "Docker network name"
}
