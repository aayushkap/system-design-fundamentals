IaC setup where Terraform reads configuration variables to provision backend resource, without shutting down existing servers on scale-up.

### Scale up (add server-4):

Edit tf.vars by adding the below:

```json
	"server-4" = {
		external_port = 8004
		environment   = "staging"
		log_level     = "info"
	}
```

then run:

1. **docker-compose run --rm terraform plan** (will show a plan to add 1 and remove 0)
2. **docker-compose run --rm terraform apply**
