# Configuration
NAMESPACE = v-ics
SCADALTS_DIR = ./scada-lts
OPENPLC_DIR = ./openplc

# Kubernetes manifests
DATABASE = $(SCADALTS_DIR)/database.yaml
DATABASE_CLAIM = $(SCADALTS_DIR)/database-pvc.yaml
DATABASE_CONFIG = $(SCADALTS_DIR)/database-config.yaml
DATABASE_SECRET = $(SCADALTS_DIR)/database-secret.yaml
SCADALTS = $(SCADALTS_DIR)/scadalts.yaml
SCADALTS_CLAIM = $(SCADALTS_DIR)/scadalts-pvc.yaml
OPENPLC_YAML = $(OPENPLC_DIR)/openplc.yaml  # New file for OpenPLC template

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
