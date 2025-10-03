## Cloud Deployment on AWS

This application is deployed in the AWS Academy Learner Lab environment for COSC349 Assignment 2.  
It uses **two EC2 instances**, **an RDS database**, and **an S3 bucket**.

### Architecture
- **EC2 Instance 1 (Web Server)**: runs Flask app with Gunicorn + Nginx
- **EC2 Instance 2 (Worker)**: runs background report jobs (carbon-worker.service + timer)
- **Amazon RDS (PostgreSQL/MySQL)**: stores activities and emissions data
- **Amazon S3**: stores generated monthly reports (PDF/CSV)

### Setup Steps

1. **Create EC2 instances**
   - Instance 1: Web server (`t2.micro`)
   - Instance 2: Worker (`t2.micro`)
   - Open ports: 22 (SSH), 80/443 (HTTP/HTTPS), 8000 (optional dev only)
   - Both should be in the same VPC/subnet for internal access

2. **Set up RDS**
   - Create an RDS instance (Postgres or MySQL)
   - Record hostname, database name, username, password
   - Ensure inbound rules allow access from your EC2 security group

3. **Create S3 bucket**
   - Unique bucket name (e.g. `carbon-tracker-reports-<studentid>`)
   - Enable bucket for public read (optional), or keep private and serve via signed URLs
   - IAM role or keys with `s3:PutObject` and `s3:GetObject`

4. **Clone and configure the repo on both EC2 instances**
   ```bash
   git clone https://github.com/<your-repo>/carbon-tracker.git /opt/carbon-tracker
   cd /opt/carbon-tracker
   pip install -r requirements.txt

5. **Look at the .env.example and create env files for both ec2 instances**

6. **Initialize the Database Schema**
Run this from one EC2 instance
psql -h <rds-endpoint> -U <dbuser> -d <dbname> -f setup/init_db.sql

7. **Start services**
On Web Server: 
sudo cp setup/carbon-tracker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now carbon-tracker

On Worker:
sudo cp setup/carbon-worker.service /etc/systemd/system/
sudo cp setup/carbon-worker.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now carbon-worker.timer

8. **Access The application**
Navigate to: http://<ec2-public-dns>
