This demo demonstrates Round Robin scheduling with integrated health checks.

The `docker-compose` file launches five backend servers. Each server can independently report an unhealthy status.

Unhealthy servers are excluded from load balancing, ensuring traffic is only routed to healthy servers.

You can go to `Services` in the Traefik Ui to see those services which are healthy and which are not.
