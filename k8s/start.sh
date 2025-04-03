minikube addons enable ingress
sleep 5

kubectl apply --server-side -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.25/releases/cnpg-1.25.1.yaml
sleep 5

# Redis
kubectl apply -f redis.yaml
sleep 5
# Secrets
kubectl apply -f postgres-users-secret.yaml
kubectl apply -f postgres-game-history-secret.yaml
kubectl apply -f users-secret.yaml
sleep 5
# Postgres
kubectl apply -f postgres-users.yaml
kubectl apply -f postgres-game-history.yaml
sleep 5
# Services
kubectl apply -f users.yaml


#Ingress
kubectl apply -f ingress.yaml

sleep 30

# Run port-forwards in parallel
kubectl port-forward -n tictactoe svc/users-db-cluster-rw 5432:5432 &
kubectl port-forward -n tictactoe svc/game-history-db-cluster-rw 5433:5432 &
kubectl port-forward -n tictactoe svc/redis-primary 6379:6379 &
minikube tunnel &

# Save all background process IDs
pids=($!)

# Add trap to kill background processes on script exit
trap "kill ${pids[*]} 2>/dev/null" EXIT

# Wait for Ctrl+C to terminate
echo "Port forwarding in progress. Press Ctrl+C to stop."
wait