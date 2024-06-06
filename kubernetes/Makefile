# Configuration
NAMESPACE = v-ics
BASE_DIR = ./scada-lts

# Kubernetes manifests
DATABASE = $(BASE_DIR)/database.yaml
DATABASE_CLAIM = $(BASE_DIR)/database-pvc.yaml
DATABASE_CONFIG = $(BASE_DIR)/database-config.yaml
DATABASE_SECRET = $(BASE_DIR)/database-secret.yaml
SCADALTS = $(BASE_DIR)/scadalts.yaml
SCADALTS_CLAIM = $(BASE_DIR)/scadalts-pvc.yaml
OPENPLC_YAML = $(BASE_DIR)/openplc.yaml  # New file for OpenPLC template

.PHONY: all deploy-scada-lts deploy-openplc clean

all: deploy-scada-lts deploy-openplc

deploy-scada-lts:
	@kubectl get namespace $(NAMESPACE) &> /dev/null || kubectl create namespace $(NAMESPACE)
	@if ! kubectl get deployment/scada-lts -n $(NAMESPACE) &> /dev/null; then \
		echo "Deploying SCADA-LTS..."; \
		kubectl apply -f $(DATABASE_CLAIM); \
		kubectl apply -f $(DATABASE_CONFIG); \
		kubectl apply -f $(DATABASE_SECRET); \
		kubectl apply -f $(DATABASE); \
		kubectl apply -f $(SCADALTS_CLAIM); \
		kubectl apply -f $(SCADALTS); \
	else \
		echo "SCADA-LTS is already deployed."; \
	fi

deploy-openplc: $(OPENPLC_YAML)
	@echo "Deploying OpenPLC instances..."
	bash ./deploy_openplc.sh $(NUM_INSTANCES)  # Use separate Bash script

$(OPENPLC_YAML):
	@echo "Generating OpenPLC YAML template..."
	@echo 'OPENPLC_IMAGE="openplc:v3"' > $@
	@echo 'START_PORT=8081' >> $@
	@echo 'START_NODE_PORT=30001' >> $@

clean:
	@kubectl delete namespace $(NAMESPACE)  # Optional: Delete namespace on clean
