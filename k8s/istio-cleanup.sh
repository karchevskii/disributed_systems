#!/bin/bash

set -e

echo "🚮 Deleting application resources..."

# Delete app resources (in tictactoe namespace)
kubectl delete namespace tictactoe --ignore-not-found

echo "🧼 Deleting Istio addons..."

# Delete Istio addons
ISTIO_VERSION="1.25.1"
ISTIO_DIR="istio-${ISTIO_VERSION}"
if [ ! -d "$ISTIO_DIR" ]; then
  echo "Downloading Istio $ISTIO_VERSION..."
  curl -L https://istio.io/downloadIstio | ISTIO_VERSION=$ISTIO_VERSION sh -
fi

kubectl delete -f "$ISTIO_DIR/samples/addons" --ignore-not-found

echo "📦 Uninstalling Istio..."

# Uninstall Istio control plane
istioctl uninstall --purge -y || true

# Delete istio-system namespace if still around
kubectl delete namespace istio-system --ignore-not-found

# Optional: delete CloudNativePG CRDs
echo "❌ Deleting CloudNativePG..."
kubectl delete -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.25/releases/cnpg-1.25.1.yaml --ignore-not-found

echo "✅ All resources removed (except cluster). If you want to delete everything, use: minikube delete"
