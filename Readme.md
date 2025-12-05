# Flask MongoDB Kubernetes Assignment

[![Docker Image](https://img.shields.io/badge/Docker%20Hub-Image%20Available-blue)](https://hub.docker.com/r/ayushk1503/flask-mongodb-app)

This project deploys a stateful Python Flask application backed by MongoDB on a Kubernetes cluster. It features authentication, persistence, and horizontal autoscaling.

## 📂 Project Structure

- `app.py`: The Flask application logic (Dual-mode: supports both local and K8s execution).
- `Dockerfile`: Optimized Python image configuration.
- `k8s/`: Contains all Kubernetes manifests.
  - `mongo-secret.yaml`: Stores DB credentials securely.
  - `mongo-pvc.yaml`: Persistent Volume Claim for data durability.
  - `mongo-statefulset.yaml`: Database deployment (StatefulSet).
  - `mongo-service.yaml`: Headless service for internal DNS resolution.
  - `flask-deployment.yaml`: Application deployment.
  - `flask-service.yaml`: LoadBalancer service for external access.
  - `flask-hpa.yaml`: Horizontal Pod Autoscaler configuration.

## 🛠️ Build & Publish Docker Image

**Docker Registry Link:** [ayushk1503/flask-mongodb-app](https://hub.docker.com/r/ayushk1503/flask-mongodb-app)

_Instructions to build and push the image to Docker Hub (Required for Kubernetes to pull the image)._

1.  **Build the Image:**

    ```bash
    docker build -t flask-mongodb-app:v1 .
    ```

2.  **Tag and Push:**
    _(Replace `ayushk1503` with your Docker Hub username)_
    ```bash
    docker tag flask-mongodb-app:v1 ayushk1503/flask-mongodb-app:v1
    docker push ayushk1503/flask-mongodb-app:v1
    ```

## 🚀 How to Deploy (Minikube)

**Prerequisites:** Minikube, Kubectl, Docker.

1.  **Start Minikube & Enable Metrics:**

    ```bash
    minikube start
    minikube addons enable metrics-server
    ```

2.  **Deploy the Database Layer (Dependencies First):**

    ```bash
    kubectl apply -f k8s/mongo-secret.yaml
    kubectl apply -f k8s/mongo-pvc.yaml
    kubectl apply -f k8s/mongo-service.yaml
    kubectl apply -f k8s/mongo-statefulset.yaml
    ```

    _Wait until the `mongodb-0` pod is Running._

3.  **Deploy the Application Layer:**

    ```bash
    kubectl apply -f k8s/flask-deployment.yaml
    kubectl apply -f k8s/flask-service.yaml
    kubectl apply -f k8s/flask-hpa.yaml
    ```

4.  **Access & Verify the Application:**
    Run the tunnel command to get the external URL:

    ```bash
    minikube service flask-service --url
    ```

    _Example URL: `http://127.0.0.1:62402`_

    **Verify Database Interaction:**

    ```bash
    # 1. Check Root Endpoint
    curl [http://127.0.0.1:62402/](http://127.0.0.1:62402/)

    # 2. Insert Data (Write to MongoDB)
    curl -X POST -H "Content-Type: application/json" -d '{"test":"persistence"}' [http://127.0.0.1:62402/data](http://127.0.0.1:62402/data)

    # 3. Retrieve Data (Read from MongoDB)
    curl [http://127.0.0.1:62402/data](http://127.0.0.1:62402/data)
    ```

## 🧠 Design Choices & Concepts

### 1. Why StatefulSet for MongoDB?

I chose a `StatefulSet` over a Deployment because databases require a stable network identity (e.g., `mongodb-0`) and ordered startup/teardown to prevent data corruption. A Deployment treats pods as interchangeable, which is risky for primary/secondary database nodes.

### 2. DNS Resolution in Kubernetes

**How Flask finds Mongo:**
I configured a **Headless Service** (`clusterIP: None`) for MongoDB. This creates a DNS entry `mongodb-service` within the cluster.
When the Flask app tries to connect to `mongodb-service`, Kubernetes DNS resolves this name directly to the IP address of the `mongodb-0` pod. This ensures efficient, direct communication without an unnecessary load balancer in the middle.

### 3. Resource Requests & Limits

I configured the pods with specific constraints to ensure stability:

- **Requests (0.2 CPU, 250Mi):** The minimum resources guaranteed for the pod to be scheduled.
- **Limits (0.5 CPU, 500Mi):** The hard cap. If the app exceeds 500Mi RAM, it will be OOMKilled (Out of Memory) to protect the rest of the node. If it tries to use more than 0.5 CPU, it will be throttled.

### 4. Authentication Strategy

To meet the security requirement, I refactored `app.py` to support a "Dual-Mode" connection. It checks for `MONGO_USERNAME` and `MONGO_PASSWORD` environment variables (injected via Kubernetes Secrets). If present, it uses an authenticated connection string; otherwise, it falls back to a local connection for development.

## 🍪 Cookie Point: Autoscaling Test Results

**Scenario:** Simulated high traffic using 20 concurrent `curl` loops to trigger the CPU threshold.

**Results:**

- **Baseline:** 2 Pods running with < 1% CPU.
- **Load Applied:** CPU utilization spiked to >120% (Target was 70%).
- **HPA Action:** Kubernetes detected the spike and automatically scaled replicas from **2 to 4**.
- **Cooldown:** After stopping the load generator, replicas stabilized and eventually scaled back down to 2.

<img width="659" height="282" alt="Screenshot 2025-12-05 at 21 16 05" src="https://github.com/user-attachments/assets/8efc737f-c296-4cf5-95b0-fc78975cfb16" />
