## Minikube Setup

Follow these steps to set up the project on Minikube:

### Prerequisites

- Install [Minikube](https://minikube.sigs.k8s.io/docs/start/).
- Install [Helm](https://helm.sh/docs/intro/install/).
- Ensure Docker is installed and running.

### Steps

1. **Start Minikube:**

   - For Linux:
     ```bash
     minikube start
     ```

   - For Windows (using Hyper-V driver):
     ```bash
     minikube start --driver=hyperv
     ```

2. **Enable Ingress Controller:**
   ```bash
   minikube addons enable ingress
   ```

3. **Deploy the Helm Chart:**
   ```bash
   helm install proiect ./ds-proiect
   ```

4. **Verify the Deployment:**
   ```bash
   kubectl get all
   ```

5. **Access the Application:**
   - Use `minikube ip` to get the Minikube IP.
   - Access the services via the configured ingress routes or NodePorts:
     - Frontend: `http://<minikube-ip>:30000`
     - Swagger: `http://<minikube-ip>:30001`
