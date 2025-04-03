kubectl apply --server-side -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.25/releases/cnpg-1.25.1.yaml
sleep 30
kubectl apply -f redis.yaml
kubectl apply -f postgres-user-secret.yaml
kubectl apply -f postgres-game-history-secret.yaml
kubectl apply -f postgres-users.yaml
kubectl apply -f postgres-game-history.yaml