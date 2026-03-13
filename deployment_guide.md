# Deployment Guide: Hosting on AWS EC2 (Free Tier)

This guide walks you through the steps to host your **Multi-Cloud Dashboard** on an Amazon EC2 `t2.micro` instance.

---

## Step 1: Launch an AWS EC2 Instance
1.  Log in to the **AWS Management Console**.
2.  Navigate to **EC2** and click **Launch Instance**.
3.  **Name:** `Multi-Cloud-Dashboard-Server`.
4.  **AMI:** Select **Ubuntu Server 24.04 LTS** (Free tier eligible).
5.  **Instance Type:** `t2.micro` (Free tier eligible).
6.  **Key Pair:** Create a new key pair or select an existing one to SSH into the server.
7.  **Network Settings:** 
    *   Allow SSH traffic from **My IP**.
    *   **CRITICAL:** Once the instance is launched, go to the **Security Group** and add an **Inbound Rule**:
        *   **Type:** Custom TCP
        *   **Port:** `8501`
        *   **Source:** `0.0.0.0/0` (Allows everyone to see your dashboard).

---

## Step 2: Install Docker on the Server
Once you have SSH'd into your server, run the following commands:

```bash
# Update packages
sudo apt-get update

# Install Docker
sudo apt-get install -y docker.io

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker
# Add your user to the docker group (to run without sudo)
sudo usermod -aG docker $USER
# (Note: Logout and log back in for this to take effect)
```

---

## Step 3: Deploy the Application
1.  **Clone your repository:**
    ```bash
    git clone [YOUR_GITHUB_REPO_URL]
    cd [YOUR_REPO_NAME]
    ```

2.  **Setup Environment Variables:**
    Create a `.env` file on the server and add your cloud credentials (or use AWS Secret Manager for extra credit!).
    ```bash
    nano .env
    # Paste your credentials here, Ctrl+O, Enter, Ctrl+X to save
    ```

3.  **Build and Run with Docker:**
    ```bash
    # Build the image
    docker build -t cloud-analyzer .

    # Run the container in the background
    docker run -d -p 8501:8501 --env-file .env --name analyzer-app cloud-analyzer
    ```

---

## Step 4: Access the Dashboard
1.  Go to the **EC2 Dashboard** in your browser.
2.  Find your **Public IPv4 Address**.
3.  Open a new tab and go to: `http://[YOUR_PUBLIC_IP]:8501`

---

## Why this approach is "Professor-Ready":
*   **Scalability:** Using Docker means the app can be moved to any cloud provider easily (No Lock-In!).
*   **Professionalism:** Shows you've handled infrastructure-as-code and networking (Security Groups/Ports).
*   **Reliability:** The app won't crash due to "it works on my machine" issues.
