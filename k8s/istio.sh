#!/bin/bash

# Download istioctl if not already installed
if ! command -v istioctl &> /dev/null; then
  echo "Downloading istioctl..."
  curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.25.1 sh -
  export PATH="$PWD/istio-1.25.1/bin:$PATH"
else
  echo "istioctl already installed"
fi

ISTIO_DIR="$PWD/istio-1.25.1"

# Create namespace
echo "Creating namespace..."
kubectl apply -f namespace.yaml

# Install Istio with demo profile (includes ingress gateway)
echo "Installing Istio..."
istioctl install --set profile=demo -y

# Label namespace for sidecar injection
kubectl label namespace tictactoe istio-injection=enabled --overwrite

# Apply CloudNativePG
kubectl apply --server-side -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.25/releases/cnpg-1.25.1.yaml
sleep 5

# Secrets
echo "Creating secrets..."
kubectl apply -f redis-secret.yaml
kubectl apply -f postgres-users-secret.yaml
kubectl apply -f postgres-game-history-secret.yaml
kubectl apply -f users-secret.yaml
sleep 5

# Redis
kubectl apply -f redis.yaml
sleep 5

# Postgres
kubectl apply -f postgres-users.yaml
kubectl apply -f postgres-game-history.yaml
sleep 5

# Services
kubectl apply -f users.yaml
kubectl apply -f game-history.yaml
kubectl apply -f game.yaml
kubectl apply -f frontend.yaml

# Deploy Istio addons (Kiali, Prometheus, Jaeger, Grafana)
echo "Deploying Istio addons..."
kubectl apply -f "$ISTIO_DIR/samples/addons"

# Wait until Kiali is ready
echo "Waiting for Kiali to be ready..."
kubectl wait --for=condition=available --timeout=120s deployment/kiali -n istio-system

# Ingress (app + addons routes via tictactoe.local)
kubectl apply -f istio-ingress.yaml

sleep 10

# Run port-forwards in parallel (DB + Redis)
# kubectl port-forward -n tictactoe svc/users-db-cluster-rw 5432:5432 &
# kubectl port-forward -n tictactoe svc/game-history-db-cluster-rw 5433:5432 &
# kubectl port-forward -n tictactoe svc/redis 6379:6379 &
minikube tunnel &

# Save all background process IDs
pids=($!)
trap "kill ${pids[*]} 2>/dev/null" EXIT

echo "Port forwarding in progress. Press Ctrl+C to stop."
wait
