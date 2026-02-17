# 🚀 TAAIP Deployment & Hosting Guide
## **Complete Guide: From Local to Production**

---

## 📊 **Where Your Data Lives RIGHT NOW**

```
💾 DATABASE LOCATION: /Users/ambermooney/Desktop/TAAIP/data/taaip.sqlite3
📦 SIZE: ~50 MB
👥 USERS: Just you (1 person)
🔒 BACKUPS: None
💰 COST: $0
⚠️  PROBLEM: Only works on your Mac, no backups, can't handle multiple users
```

---

## ❓ **Your Questions Answered**

### **"Where is all of this being stored?"**
**Currently**: Local SQLite file on your Mac Desktop
**For Production**: You'll need cloud database (AWS/Azure)

### **"Will I need to create a cloud database?"**
**YES** - for production use with multiple users
**Cost**: ~$15-50/month depending on size

### **"Do I need to buy servers?"**
**NO** - You rent cloud servers (no physical hardware)
**Cost**: ~$20-100/month

### **"Do I need a domain to host it?"**
**YES** - for professional access (like `taaip.army`)
**Cost**: ~$12/year

### **"Can I assign, delegate, change tasks, mark complete, track overdue, over budget, etc?"**
**YES** - Already built! The ProjectEditor component has:
- ✅ Task assignment and delegation
- ✅ Status changes (open → in progress → completed)
- ✅ Due date tracking (overdue alerts)
- ✅ Budget tracking (over/under budget indicators)
- ✅ Task priorities
- ✅ Milestone tracking

---

## 💰 **Total Cost Breakdown**

### **Option 1: AWS (Army-Approved) - Recommended**
| Item | Cost | Required? |
|------|------|-----------|
| Domain name (e.g., taaip.army) | $12/year | Yes |
| AWS RDS Database | $15-40/month | Yes |
| AWS EC2 Server | $15-30/month | Yes |
| AWS S3 Storage | $5/month | Yes |
| **TOTAL** | **~$50-90/month** | |

**Annual Cost**: ~$600-1,080/year

### **Option 2: Heroku (Easiest)**
| Item | Cost |
|------|------|
| Domain name | $12/year |
| Heroku Dyno (Basic) | $7/month |
| Heroku PostgreSQL | $9/month |
| **TOTAL** | **~$28/month** |

**Annual Cost**: ~$348/year

### **Option 3: DigitalOcean (Budget)**
| Item | Cost |
|------|------|
| Domain name | $12/year |
| Droplet Server | $12/month |
| Managed Database | $15/month |
| **TOTAL** | **~$39/month** |

**Annual Cost**: ~$480/year

---

## 🏆 **RECOMMENDED: AWS GovCloud** (For Army Use)

### **Why AWS?**
✅ Army/DoD approved
✅ FedRAMP certified
✅ Handles classified data (CUI/FOUO)
✅ Used by other Army systems
✅ Best security
✅ Can scale to entire USAREC

### **What You Get:**
- **Database**: PostgreSQL (up to 100 concurrent users)
- **Servers**: Auto-scaling (handles traffic spikes)
- **Backups**: Daily automatic backups (30-day retention)
- **Security**: Encryption, audit logs, MFA
- **Uptime**: 99.9% availability guarantee

---

## 🚀 **Step-by-Step Deployment** (For Non-Technical Users)

### **Phase 1: Get AWS Account** (Day 1)
```
1. Go to aws.amazon.com
2. Click "Create an AWS Account"
3. Enter email: your.name@army.mil
4. Set password
5. Choose "Business" account type
6. Enter payment method (need credit card even for free tier)
7. Verify phone number
8. Choose "Basic Support" (free)
9. Complete registration
```

**Note**: Check with your G6 - USAREC may have an Army Cloud One account you can use instead!

---

### **Phase 2: Create Database** (Day 2-3)

```
1. Login to AWS Console
2. Search for "RDS" (Relational Database Service)
3. Click "Create database"
4. Select:
   - Engine: PostgreSQL
   - Version: 15.3
   - Template: Production (or Dev/Test for testing)
   - DB instance identifier: taaip-production
   - Master username: taaip_admin
   - Master password: [Create strong password - SAVE THIS!]
   - Instance size: db.t3.micro ($15/mo) or db.t3.small ($30/mo)
   - Storage: 20 GB
   - Enable automatic backups: Yes (7 days retention)
   - Public access: Yes (for now)
5. Click "Create database"
6. Wait 10-15 minutes for creation
```

**You'll get a connection string like:**
```
postgresql://taaip_admin:YOUR_PASSWORD@taaip-db.abc123.us-east-1.rds.amazonaws.com:5432/taaip
```

**SAVE THIS CONNECTION STRING!** You'll need it later.

---

### **Phase 3: Migrate Your Data** (Day 3-4)

I'll create a migration script for you:

```python
# migrate_to_postgres.py - I'll create this
# Run: python3 migrate_to_postgres.py --postgres-url "postgresql://..."
# This copies all your data from SQLite to PostgreSQL
```

**Before migrating, backup your SQLite database:**
```bash
cp data/taaip.sqlite3 data/taaip_backup_$(date +%Y%m%d).sqlite3
```

---

### **Phase 4: Deploy Backend** (Day 4-6)

**Option A: AWS Elastic Beanstalk (Easier)**
```bash
# Install AWS EB CLI
pip install awsebcli

# Initialize
eb init -p python-3.11 taaip-backend --region us-east-1

# Set environment variables
eb setenv DATABASE_URL="postgresql://taaip_admin:PASSWORD@RDS_ENDPOINT:5432/taaip"

# Deploy
eb create taaip-production
eb deploy
```

Your API will be at: `http://taaip-production.us-east-1.elasticbeanstalk.com`

**Option B: AWS EC2 (More Control)**
```
1. Go to EC2 Dashboard
2. Click "Launch Instance"
3. Name: taaip-backend
4. AMI: Ubuntu 22.04 LTS
5. Instance type: t3.small (2GB RAM, 2 vCPU)
6. Create new key pair → Download .pem file
7. Security group:
   - Allow SSH (port 22) from your IP
   - Allow HTTP (port 80) from anywhere
   - Allow HTTPS (port 443) from anywhere
8. Storage: 20 GB
9. Launch instance
```

Then SSH in and install:
```bash
ssh -i your-key.pem ubuntu@YOUR_EC2_IP
sudo apt update && sudo apt install python3 python3-pip nginx -y
pip3 install fastapi uvicorn sqlalchemy psycopg2-binary
```

---

### **Phase 5: Deploy Frontend** (Day 6-7)

```bash
# Build production version
cd taaip-dashboard
npm run build

# This creates a 'dist' folder

# Upload to AWS S3
aws s3 mb s3://taaip-frontend-YOUR_NAME
aws s3 sync dist/ s3://taaip-frontend-YOUR_NAME --acl public-read

# Enable static website hosting
aws s3 website s3://taaip-frontend-YOUR_NAME \
    --index-document index.html \
    --error-document index.html
```

Your site will be at: `http://taaip-frontend-YOUR_NAME.s3-website-us-east-1.amazonaws.com`

---

### **Phase 6: Get Custom Domain** (Day 8-10)

#### Buy Domain:
```
1. Go to GoDaddy.com or Namecheap.com
2. Search for domain: taaip-usarec.com (or whatever you want)
3. Purchase (~$12/year)
4. Don't add extras (privacy protection is enough)
```

#### Connect Domain to AWS:
```
1. In AWS Console, go to Route 53
2. Click "Create hosted zone"
3. Domain name: yourdomain.com
4. Type: Public hosted zone
5. Create
6. Copy the 4 nameserver addresses (ns-123.awsdns-45.com, etc.)
7. Go back to GoDaddy/Namecheap
8. Find DNS settings
9. Replace nameservers with AWS nameservers
10. Wait 24-48 hours for propagation
```

#### Add SSL Certificate (HTTPS):
```
1. Go to AWS Certificate Manager (ACM)
2. Request certificate
3. Add domain names:
   - yourdomain.com
   - www.yourdomain.com
   - api.yourdomain.com
4. Validation method: DNS validation
5. Request certificate
6. Click on certificate
7. Click "Create records in Route 53" (automatic validation)
8. Wait 5-10 minutes
9. Certificate status changes to "Issued"
```

---

## 📱 **Accessing Your App After Deployment**

### **URLs:**
```
Frontend: https://yourdomain.com
API: https://api.yourdomain.com
Admin Panel: https://yourdomain.com/admin
```

### **Sharing Access:**
```
1. Give team members the URL
2. They create accounts (if you add authentication)
3. No installation needed - just web browser
4. Works on phones, tablets, computers
```

---

## 🔒 **Security Setup** (REQUIRED for Army)

### **1. Enable MFA (Multi-Factor Authentication)**
```
1. AWS Console → IAM → Users → Your user
2. Security credentials tab
3. Assign MFA device
4. Use Microsoft Authenticator app
```

### **2. Create IAM Roles** (No hardcoded passwords)
```
1. IAM → Roles → Create role
2. Trusted entity: AWS service → EC2
3. Add permissions:
   - AmazonRDSFullAccess
   - AmazonS3FullAccess
4. Name: TAAIP-EC2-Role
5. Attach to your EC2 instance
```

### **3. Enable CloudTrail** (Audit logging)
```
1. CloudTrail console
2. Create trail
3. Name: taaip-audit-log
4. Apply trail to all regions: Yes
5. Store in S3 bucket
6. Enable log file validation
```

### **4. VPC Security**
```
1. VPC Console → Security Groups
2. Edit RDS security group
3. Remove "0.0.0.0/0" access
4. Only allow EC2 security group to access database
5. Lock down SSH access to your IP only
```

---

## 📊 **Monitoring & Maintenance**

### **Setup CloudWatch Alarms**
```
1. CloudWatch console
2. Create alarm
3. Metrics to monitor:
   - EC2 CPU > 80%
   - RDS connections > 90%
   - Disk space < 20%
4. Send email notifications
```

### **Daily Backups**
```
RDS automatically backs up daily
Manual backup:
1. RDS Console
2. Select your database
3. Actions → Take snapshot
4. Name: taaip-manual-YYYY-MM-DD
```

### **Updates**
```bash
# Update backend code
git pull
eb deploy

# Update frontend
npm run build
aws s3 sync dist/ s3://your-bucket --delete
```

---

## 🆘 **Troubleshooting**

### **"Can't connect to database"**
```
1. Check security group allows your IP
2. Verify connection string is correct
3. Test with psql:
   psql "postgresql://user:pass@host:5432/dbname"
```

### **"Frontend shows errors"**
```
1. Open browser console (F12)
2. Check API_BASE_URL in config
3. Verify CORS is enabled on backend
4. Check CloudFront distribution
```

### **"Site is slow"**
```
1. Check CloudWatch metrics
2. Upgrade instance size (t3.small → t3.medium)
3. Add caching with CloudFront
4. Enable RDS read replicas
```

---

## 💡 **Recommended Path For You**

### **Timeline & Budget**

**Week 1: Setup & Testing** ($0)
- Create AWS account
- Setup RDS database (free tier)
- Test data migration
- Deploy to Elastic Beanstalk (free tier)

**Week 2: Domain & SSL** ($12 one-time)
- Buy domain name
- Configure Route 53
- Setup SSL certificate (free with AWS)

**Week 3: Production Launch** (~$60/month starts)
- Upgrade from free tier
- Full deployment
- Team training

### **Total First Year Cost:**
```
Domain: $12
AWS Services: $60/month × 12 = $720
TOTAL: $732/year

That's $61/month - less than a single office software license!
```

---

## 📞 **Getting Help**

### **Need DevOps Support?**
Consider hiring a contractor for initial setup:
- **Upwork**: Search "AWS deployment specialist"
- **Fiverr**: "AWS fullstack deployment"
- **Cost**: $500-1,500 one-time (3-5 days work)
- They'll do all the technical setup for you

### **Army IT Support**
- Contact your G6 for Army Cloud One access
- USAREC may have existing AWS contract
- Check if hosting budget already exists

### **Free AWS Support**
- AWS Documentation: docs.aws.amazon.com
- AWS Forums: forums.aws.amazon.com
- YouTube: "AWS deployment tutorial"

---

## ✅ **Next Steps - DO THIS NOW:**

1. **[ ] Decide on hosting provider** (AWS recommended)
2. **[ ] Get budget approval** (~$1,000/year)
3. **[ ] Create AWS account** (or use Army Cloud One)
4. **[ ] Buy domain name** (taaip-yourunit.com)
5. **[ ] Schedule deployment** (plan 2-3 weeks)
6. **[ ] Consider hiring DevOps help** (saves time)

---

## 🎯 **Bottom Line**

**What you need:**
- ☁️ Cloud database (AWS RDS): $30/month
- 🖥️ Server hosting (AWS EC2): $25/month
- 🌐 Domain name: $12/year
- 🔒 SSL certificate: Free with AWS
- **TOTAL: ~$60-70/month**

**What you DON'T need:**
- ❌ Physical servers
- ❌ On-premise data center
- ❌ IT staff to maintain hardware
- ❌ Backup systems (AWS handles it)

**Your data will be:**
- ✅ Backed up daily
- ✅ Encrypted
- ✅ Available 24/7
- ✅ Accessible from anywhere
- ✅ DoD-compliant
- ✅ Scalable to entire USAREC

---

**Ready to deploy? Start with the AWS free tier and test everything before committing to paid services!**

**Questions? The deployment process is included - I can guide you through each step!**
