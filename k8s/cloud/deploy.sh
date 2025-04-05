# Namespace
kubectl apply -f namespace.yaml

kubectl create secret tls cloudflare-origin-cert --key=./origin-private-key.pem --cert=./origin-cert.pem -n tictactoe

kubectl apply --server-side -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.25/releases/cnpg-1.25.1.yaml
sleep 25


# Secrets
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

#Ingress
kubectl apply -f ingress-deploy.yaml