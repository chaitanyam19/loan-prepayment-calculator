# Loan Prepayment Calculator

This is a simple Python loan EMI and prepayment calculator.

## Docker image

Build the image:

```bash
docker build -t loan-prepayment-calculator .
```

Run the container interactively:

```bash
docker run -it --rm loan-prepayment-calculator
```

## Publish to a registry

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
