FROM golang:1.24 AS go-builder

WORKDIR /build

COPY go.mod go.sum ./
RUN go mod download

RUN go install github.com/swaggo/swag/cmd/swag@latest

COPY . ./

RUN swag init -g cmd/server/main.go -o docs

RUN CGO_ENABLED=1 GOOS=linux go build -o server ./cmd/server/main.go

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

COPY --from=go-builder /build/server /app/server
COPY --from=go-builder /build/docs /app/docs

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/ /app/scripts/

RUN mkdir -p /app/data/chromadb /app/data/motoko_code_samples /app/data/motoko_official_docs

ENV PORT=8080
ENV GIN_MODE=release
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

VOLUME ["/app/data"]

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

CMD ["/app/server"]