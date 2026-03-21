# EVOLV Kubernetes Deployment

## Prerequisites
- kubectl configured against your cluster
- AWS Load Balancer Controller installed (for ALB/NLB support)
- Container images pushed to your registry

## Deploy

```bash
# 1. Apply the service and deployment
kubectl apply -f deployment.yaml

# 2. Apply the ingress
kubectl apply -f ingress.yaml

# 3. Verify pods are running
kubectl get pods -l app=csv-tool

# 4. Get the load balancer URL
kubectl get svc csv-tool-service
```

## Notes
- `deployment.yaml` configures a LoadBalancer service (AWS NLB, internet-facing) targeting port 8501 (Streamlit).
- `ingress.yaml` uses an ALB ingress (internal scheme) routing all paths to the service on port 80.
- Replace `<your-image-id>` in `deployment.yaml` with your actual container image URI before applying.
- Secrets (API keys) should be stored in a Kubernetes Secret and referenced via `envFrom` rather than hardcoded.
