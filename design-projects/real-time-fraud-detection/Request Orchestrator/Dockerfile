# Use small base with g++
FROM debian:bookworm-slim AS build

# Install build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
	g++ make curl ca-certificates && \
	rm -rf /var/lib/apt/lists/*

# Copy source
WORKDIR /app
COPY server.cpp httplib.h json.hpp ./

# Build
RUN g++ -std=c++17 -O2 server.cpp -o server -pthread

# Final lightweight image
FROM debian:bookworm-slim
WORKDIR /app
COPY --from=build /app/server .
EXPOSE 8080
CMD ["./server"]
