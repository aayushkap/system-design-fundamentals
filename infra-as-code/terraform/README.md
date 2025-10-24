IaC setup where Terraform runs inside a Docker container to provision a FastAPI application, also running in Docker. Terraform is able to persist state across container shutdowns by storing `tf` files locally.

Commands:
1. **docker-compose run --rm terraform init** - This Terraform command that downloads the Docker provider plugin

2. **docker-compose run --rm terraform plan** - Previews what Terraform will do without making changes. Shows `2 resources to add: the Docker image and container`

3. **docker-compose run --rm terraform apply -auto-approve** - Applys the plan & creates real infra.

4. **docker-compose run --rm terraform state list** - Lists all resources Terraform is managing. Stored in the terraform.tfstate file.

5. **docker-compose run --rm terraform destroy** - Removes everything created by Terraform.
