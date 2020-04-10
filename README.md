# Bugs API

The repository contains the code and instructions for building an deploying the Bugs API.

You will build a Kubernetes cluster (for dev and/or prod environments) hosting:
- the Bugs API server, implemented with [FastAPI](https://github.com/tiangolo/fastapi)
- the database to store bugs, implemented with [Redis](https://redis.io/)

## Prerequisites

The Bugs API will run on AWS EKS, so you need an AWS account and the following installed and correctly configured in your
local machine if working locally (without a full CI/CD pipeline):
1. [aws-cli with iam authenticator](https://docs.aws.amazon.com/eks/latest/userguide/install-aws-iam-authenticator.html), configured with a IAM user with full privileges
2. [docker](https://www.docker.com/)
3. [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/)
4. [terraform](https://www.terraform.io/) (version 0.11)

## Overview of the repository structure

| Folder | Content |
| -------|---------| 
| [terraform](terraform) | Scripts to generate dev and prod clusters | 
| [api-server](api-server) | Code and Dockerfile to build the Bugs API server |  
| [kubernetes](kubernetes) | Kubernetes deployments |
| [ci-cd](ci-cd) | Proposals of Jenkins pipelines for a better CI/CD implementation |

## 1. Create AWS resources

You will create:
1. A docker registry (ECR) to host the custom docker image for the API server
2. A Kubernetes cluster (EKS) to host the deployment. Development and production environments require two different clusters.

### 1.1 ECR creation

Move to the right folder: `cd terraform/ecr`

Execute the script (inspired by [this](https://www.terraform.io/docs/providers/aws/r/ecr_repository.html):
`terraform init` then `terraform apply`

At this point you'll have a new ECR called `bugs`. The URN for this repository will be saved as the terraform output variable `ecr_arn`.
To retrieve it: `terraform output ecr_arn`

You need `docker` to login into it by following [this guide](https://docs.aws.amazon.com/AmazonECR/latest/userguide/Registries.html) 

### 1.2 EKS cluster creation

Move to the right folder: `cd terraform/eks-cluster-<env>` where `env` identifies the `dev` or `prod` stage.

Execute the script (inspired by [this](https://learn.hashicorp.com/terraform/aws/eks-intro):
`terraform init` then `terraform apply`

Generate kubeconfig and configmap for adding worker nodes from terraform outputs:
```
terraform output kubeconfig > ./kubeconfig
terraform output config_map_aws_auth > ./config_map_aws_auth.yaml
```

Update your `kubectl` configuration and apply the configmap to make worker nodes join the cluster:
```
export KUBECONFIG=./kubeconfig
kubectl apply -f ./config_map_aws_auth.yaml
```

After a while you should see all the nodes correctly registered to the cluster and ready by checking with this command:
`kubectl get nodes`

## 2. Build the BUGS API server

Move to the right folder: `cd api-server/eks-cluster`

Build the custom docker image: `docker build -t <image_name> .`

Tag and push the image to your ECR:
```
docker tag <image_id> <ECR_URN>/<image_name>
docker push <ECR_URN>/<image_name>
```

## 3. Deploy everything

Move to the right folder: `cd kubernetes`

Create a class storage for AWS EBS: `kubernetes apply -f gp2-storage-class.yaml`

Create a namespace: `kubernetes apply -f namespace.yaml`

Deploy Redis: `kubernetes apply -f redis.yaml`

Deploy the API server: `kubernetes apply -f api-server.yaml`. Before applying the manifest, you need to configure the API server
repository name and deployment environment name.

*Alternative option:* a basic Helm chart is in the `helm` folder. 

## 4. Access the API server

The external IP address of the api-server service (autogenerated by the AWS LoadBalancer) can be retrieved with this command:
`kubectl -n bugs get svc`

The JSON API is at `/api/bugs`

A simple web page to get all bugs and create a new one is at `/web/bugs`

An automatic Swagger UI will be at `/docs`