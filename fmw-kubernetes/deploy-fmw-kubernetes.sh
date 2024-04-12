#!/bin/bash

# Configuration
NAMESPACE=fmw-scada
SCADA_LTS_DEPLOYMENT="scada-lts-deployment.yaml"
OPENPLC_IMAGE="openplc:v3"
START_PORT=8081

# Function to check if SCADA-LTS is already deployed
deploy_scada_lts() {
  if ! kubectl get deployment/scada-lts -n $NAMESPACE &> /dev/null; then
    echo "Deploying SCADA-LTS..."
    kubectl apply -f $SCADA_LTS_DEPLOYMENT
  else
    echo "SCADA-LTS is already deployed."
  fi
}

# Function to deploy OpenPLC instances
deploy_openplc_instances() {
  local instances=$1
  local current_port=$START_PORT

  for i in $(seq 1 $instances); do
    local name="openplc-instance$i"
    echo "Deploying $name..."

    # Generate Deployment YAML
    cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $name
  namespace: $NAMESPACE
spec:
  replicas: 1
  selector:
    matchLabels:
      app: $name
  template:
    metadata:
      labels:
        app: $name
    spec:
      containers:
      - name: openplc
        image: $OPENPLC_IMAGE
        ports:
        - containerPort: 8080

---
apiVersion: v1
kind: Service
metadata:
  name: $name
  namespace: $NAMESPACE
spec:
  selector:
    app: $name
  ports:
    - protocol: TCP
      port: $current_port
      targetPort: 8080
  type: LoadBalancer
EOF

    ((current_port++))
  done
}

# Main script logic
main() {
  local number_of_instances

  # Check if number of OpenPLC instances is provided
  if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <number_of_openplc_instances>"
    exit 1
  fi

  number_of_instances=$1

  # Create Kubernetes namespace if it doesn't exist
  kubectl get namespace $NAMESPACE &> /dev/null || kubectl create namespace $NAMESPACE

  deploy_scada_lts
  deploy_openplc_instances $number_of_instances
}

main "$@"
