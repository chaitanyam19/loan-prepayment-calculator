# Loan Prepayment Calculator

This is a simple Python loan EMI and prepayment calculator.

## Docker image

Build the image:

```bash
docker build -t loan-prepayment-calculator .
```

Run the FastAPI container on port 8080:

```bash
docker run -it --rm -p 8080:8080 loan-prepayment-calculator
```

Open the API docs in your browser:

```bash
http://localhost:8080/docs
```

Fetch a calculation with curl:

```bash
curl "http://localhost:8080/calculate?principal=100000&annual_rate=10&tenure_years=5&prepayment_month=12&prepayment_amount=20000&method=reduce+tenure"
```

Publish the image to a registry:

```bash
docker tag loan-prepayment-calculator your-registry/loan-prepayment-calculator:latest
docker push your-registry/loan-prepayment-calculator:latest
```

Then run it from any host with Docker:

```bash
docker run -it --rm -p 8080:8080 your-registry/loan-prepayment-calculator:latest
```

Tag the image for your registry:

```bash
docker tag loan-prepayment-calculator your-registry/loan-prepayment-calculator:latest
```

Push it:

```bash
docker push your-registry/loan-prepayment-calculator:latest
```

Then run it on any host with Docker:

```bash
docker run -it --rm your-registry/loan-prepayment-calculator:latest
```

## Deployment options

- Docker Hub or GitHub Container Registry for public images
- AWS ECS / Fargate
- Azure Container Instances
- Google Cloud Run
- Any Kubernetes cluster
