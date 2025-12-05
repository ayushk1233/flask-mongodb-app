# Flask MongoDB Kubernetes Assignment

This project deploys a stateful Python Flask application backed by MongoDB on a Kubernetes cluster. It features authentication, persistence, and horizontal autoscaling.

## 📂 Project Structure
* `app.py`: The Flask application logic (Dual-mode: supports both local and K8s execution).
* `Dockerfile`: optimized Python image configuration.
* `k8s/`: Contains all Kubernetes manifests.
    * `mongo-secret.yaml`: Stores DB credentials securely.
    * `mongo-pvc.yaml`: Persistent Volume Claim for data durability.
    * `mongo-statefulset.yaml`: Database deployment (StatefulSet).
    * `mongo-service.yaml`: Headless service for internal DNS resolution.
    * `flask-deployment.yaml`: Application deployment.
    * `flask-service.yaml`: LoadBalancer service for external access.
    * `flask-hpa.yaml`: Horizontal Pod Autoscaler configuration.

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
    *Wait until the `mongodb-0` pod is Running.*

3.  **Deploy the Application Layer:**
    ```bash
    kubectl apply -f k8s/flask-deployment.yaml
    kubectl apply -f k8s/flask-service.yaml
    kubectl apply -f k8s/flask-hpa.yaml
    ```

4.  **Access the Application:**
    Run the tunnel command to get the external URL:
    ```bash
    minikube service flask-service --url
    ```

## 🧠 Design Choices & Concepts

### 1. Why StatefulSet for MongoDB?
I chose a `StatefulSet` over a Deployment because databases require a stable network identity (e.g., `mongodb-0`) and ordered startup/teardown to prevent data corruption. [cite_start]A Deployment treats pods as interchangeable, which is risky for primary/secondary database nodes[cite: 129, 130].

### 2. DNS Resolution in Kubernetes
**How Flask finds Mongo:**
I configured a **Headless Service** (`clusterIP: None`) for MongoDB. This creates a DNS entry `mongodb-service` within the cluster.
When the Flask app tries to connect to `mongodb-service`, Kubernetes DNS resolves this name directly to the IP address of the `mongodb-0` pod. [cite_start]This ensures efficient, direct communication without an unnecessary load balancer in the middle[cite: 147, 148].

### 3. Resource Requests & Limits
[cite_start]I configured the pods with specific constraints to ensure stability[cite: 153, 154]:
* **Requests (0.2 CPU, 250Mi):** The minimum resources guaranteed for the pod to be scheduled.
* **Limits (0.5 CPU, 500Mi):** The hard cap. If the app exceeds 500Mi RAM, it will be OOMKilled (Out of Memory) to protect the rest of the node. If it tries to use more than 0.5 CPU, it will be throttled.

### 4. Authentication Strategy
To meet the security requirement, I refactored `app.py` to support a "Dual-Mode" connection. It checks for `MONGO_USERNAME` and `MONGO_PASSWORD` environment variables (injected via Kubernetes Secrets). If present, it uses an authenticated connection string; otherwise, it falls back to a local connection for development.

## 🍪 Cookie Point: Autoscaling Test Results
**Scenario:** Simulated high traffic using an infinite `curl` loop.
**Result:**
* Baseline: 2 Pods (CPU < 1%).
* Load Applied: CPU utilization spiked to >120% (Target: 70%).
* HPA Action: Scaled replicas from **2 to 5** automatically.
* Cooldown: After stopping load, replicas scaled back down to 2.