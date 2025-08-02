In distributed tracing, a span is the primary building block of a trace. A trace is the end-to-end journey of a single request through your system, and spans are the individual steps along that journey.

Context propagation is the mechanism by which trace context (like trace IDs and span IDs) is passed along with requests as they travel through different services. This allows for the correlation of spans across services, enabling a complete view of the request's journey.

### About this project

[Client Root Span]
    │
[Gateway Span]
    │
[Processor Span]
    │
[Database Span]

There is a gateway service that receives requests and forwards them to any of the two processor services. 

Each processor service processes the request and interacts with a database service. Each processor may randomly throw an error to simulate failure scenarios.

You can view the traces at http://localhost:9411/

You can submit a request to the gateway service at http://localhost:8000/docs#/default/proxy_proxy_get
