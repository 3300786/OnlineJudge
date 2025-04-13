# Dockerfile
FROM ubuntu:20.04

RUN apt update && apt install -y \
    g++ python3 python3-pip time && \
    apt clean

WORKDIR /workspace

CMD ["bash"]
