# Device Management with Kubernetes (K8s)

## Overview
This is a distributed system project that leverages microservices architecture. It includes multiple backend services, an API gateway, a frontend, and a Swagger documentation service. The project is containerized using Docker and orchestrated with Kubernetes. Helm is used to manage the deployment of the services.

## Repository Structure

- **api-gateway/**: Contains the API gateway service.
- **backend-auth/**: Backend service for authentication.
- **backend-devices/**: Backend service for managing devices.
- **backend-user/**: Backend service for user management.
- **ds-proiect/**: Helm chart for deploying the entire project.
- **frontend/**: Frontend application built with modern web technologies.
- **swagger/**: Swagger documentation service.

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
   - Access the services via the configured ingress routes.

## Helm Chart Details

The Helm chart is located in the `ds-proiect/` directory. It includes the following services:

- **authService**: Authentication backend.
- **userService**: User management backend.
- **deviceService**: Device management backend.
- **apiService**: API gateway.
- **frontendService**: Frontend application.
- **swaggerService**: Swagger documentation.

### Values.yaml
The `values.yaml` file defines the configuration for each service, including replica counts, Docker images, and inter-service DNS.

## Docker Images

The Docker images for the services are pulled from my personal Docker repository. You can find the image references in the `values.yaml` file of the Helm chart. Ensure that the images are accessible and properly tagged in the Docker repository.

## Contributing

Feel free to fork the repository and submit pull requests. Ensure your code adheres to the project's coding standards.

## License

This project is licensed under the MIT License.