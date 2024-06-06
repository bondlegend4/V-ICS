#!/bin/bash

# Configuration
NAMESPACE=v-ics
BASE_DIR="./scada-lts-data"
DATABASE="$BASE_DIR/database.yaml"
DATABASE_CLAIM="$BASE_DIR/database-pvc.yaml"
DATABASE_CONFIG="$BASE_DIR/database-config.yaml"
DATABASE_SECRET="$BASE_DIR/database-secret.yaml"
SCADALTS="$BASE_DIR/scadalts.yaml"
SCADALTS_CLAIM="$BASE_DIR/scadalts-pvc.yaml"
OPENPLC_IMAGE="openplc:v3"
START_PORT=8081
START_NODE_PORT=30001

# Function to check if SCADA-LTS is already deployed
deploy_scada_lts() {
  if ! kubectl get deployment/scada-lts -n $NAMESPACE &> /dev/null; then
    echo "Deploying SCADA-LTS..."
      kubectl apply -f $DATABASE_CLAIM
      kubectl apply -f $DATABASE_CONFIG
      kubectl apply -f $DATABASE_SECRET
      kubectl apply -f $DATABASE
      kubectl apply -f $SCADALTS_CLAIM
      kubectl apply -f $SCADALTS
  else
    echo "SCADA-LTS is already deployed."
  fi
}

# Function to deploy OpenPLC instances
deploy_openplc_instances() {
  local instances=$1
  local current_port=$START_PORT
  local current_node_port=$START_NODE_PORT

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
  type: NodePort
  selector:
    app: $name
  ports:
    - protocol: TCP
      port: $current_port
      targetPort: 8080
      nodePort: $current_node_port
  type: LoadBalancer
EOF

    ((current_port++))
    ((current_node_port++))
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
