# AWS EC2 + k3s Free-Tier-Style Deployment

This profile is for a low-cost demo on one EC2 instance running k3s.

It exposes:

- API docs: `http://EC2_PUBLIC_IP:30080/docs`
- Frontend: `http://EC2_PUBLIC_IP:30085`

Use security group inbound rules:

- SSH `22` from your IP only
- TCP `30080` from anywhere for the API
- TCP `30085` from anywhere for the frontend

Do not use Amazon EKS for a zero-cost demo. EKS has Kubernetes control plane charges. A single EC2 instance with k3s avoids that managed control-plane cost, but EC2/EBS/free-tier limits still apply to your AWS account.

## EC2 Setup

```bash
curl -sfL https://get.k3s.io | sh -
sudo kubectl get nodes
sudo cat /etc/rancher/k3s/k3s.yaml
```

Copy the kubeconfig output, replace `127.0.0.1` with your EC2 public IP, then base64 encode it for GitHub:

```powershell
[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes((Get-Content .\k3s.yaml -Raw)))
```

## GitHub Variables

Set repository variables:

- `ENABLE_K8S_DEPLOY=true`
- `K8S_PROFILE=aws-free`
- `EC2_PUBLIC_IP=your.ec2.public.ip`

## GitHub Secrets

Set repository secrets:

- `KUBECONFIG`
- `SECRET_KEY`
- `GROQ_API_KEY`
- `PINECONE_API_KEY`
- `MYSQL_PASSWORD`
- `MYSQL_ROOT_PASSWORD`
- `DATABASE_URL`

Use this value for `DATABASE_URL` if you use the included MySQL pod:

```text
mysql+pymysql://support_user:YOUR_MYSQL_PASSWORD@mysql-svc.ai-support.svc.cluster.local:3306/support_db
```
