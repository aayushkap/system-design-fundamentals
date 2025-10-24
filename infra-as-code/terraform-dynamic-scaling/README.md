IaC setup where Terraform reads CLI variable to provision backend resource, easily managins scale-up or down.

### To scale:

docker-compose run --rm terraform apply -var="server_count=5" -auto-approve

This will automatically match the number of servers to what is specified.
