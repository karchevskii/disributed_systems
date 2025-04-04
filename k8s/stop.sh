kubectl delete -n tictactoe all --all
kubectl delete clusters.postgresql.cnpg.io --all -n tictactoe
kubectl delete ingress --all -n tictactoe
kubectl delete secrets --all -n tictactoe
echo "All resources in tictactoe namespace have been deleted."