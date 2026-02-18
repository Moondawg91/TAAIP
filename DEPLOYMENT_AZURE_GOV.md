# TAAIP Deployment Guide - Azure Government

## Production Army Deployment (RMF/ATO Compliant)

This guide covers deploying TAAIP to Azure Government Cloud for official DoD/Army use with full compliance.

---

## Overview

### Timeline: 3-6 months
- Week 1-2: Azure Gov account approval
- Week 3-4: Environment setup
- Month 2-3: Security configuration & CAC integration
- Month 3-6: RMF/ATO documentation & approval

### Cost: $200-500/month
- App Service (Frontend): $50-100/month
- App Service (Backend): $50-100/month
- PostgreSQL Database: $50-150/month
- Redis Cache: $20-50/month
- Other services: $30-100/month

---

## Phase 1: Azure Government Access

### Step 1: Request Azure Gov Account

Contact your **G6/IM office** with:

```
Subject: Azure Government Cloud Account Request - TAAIP Platform

Unit: [Your Unit]
POC: [Your Name, Rank]
Email: [Your .mil email]
Phone: [DSN/Commercial]

Request: Azure Government subscription for Talent Acquisition Analytics 
and Intelligence Platform (TAAIP)

Justification:
- Mission: Automated recruiting intelligence for [Brigade/Battalion]
- Users: 420T Technicians, Recruiting Leadership
- Compliance: RMF/ATO required, FedRAMP High
- Classification: Unclassified (FOUO)
- Timeline: 3-6 month deployment

Attachments:
- TAAIP WHITEPAPER.md
- System Architecture diagram
- Cost estimate
```

### Step 2: Security Approval

Required documentation (use templates from your G6):

1. **System Security Plan (SSP)**
   - Use NIST 800-53 controls
   - Reference TAAIP WHITEPAPER.md for system description
   
2. **Risk Assessment**
   - Low impact system (recruiting data, no PII)
   - FOUO handling procedures
   
3. **Authority to Operate (ATO) Package**
   - 90-day provisional ATO possible
   - Full ATO within 6 months

---

## Phase 2: Infrastructure Setup

### Prerequisites
- Azure Gov subscription approved
- Azure CLI installed: `brew install azure-cli`
- CAC reader and middleware configured

### Step 1: Login to Azure Gov

```bash
# Login to Azure Government
az cloud set --name AzureUSGovernment
az login

# Verify you're in Gov cloud
az cloud show --output table
```

### Step 2: Create Resource Group

```bash
# Set variables
RESOURCE_GROUP="rg-taaip-prod"
LOCATION="usgovvirginia"  # or usgovtexas, usgovarizona
ENVIRONMENT="production"

# Create resource group
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION \
  --tags Environment=$ENVIRONMENT Mission=Recruiting
```

### Step 3: Create Virtual Network

```bash
# Create VNet with secure subnets
az network vnet create \
  --resource-group $RESOURCE_GROUP \
  --name vnet-taaip \
  --address-prefix 10.0.0.0/16 \
  --subnet-name subnet-frontend \
  --subnet-prefix 10.0.1.0/24

az network vnet subnet create \
  --resource-group $RESOURCE_GROUP \
  --vnet-name vnet-taaip \
  --name subnet-backend \
  --address-prefix 10.0.2.0/24

az network vnet subnet create \
  --resource-group $RESOURCE_GROUP \
  --vnet-name vnet-taaip \
  --name subnet-database \
  --address-prefix 10.0.3.0/24
```

### Step 4: Create PostgreSQL Database

```bash
# Create PostgreSQL server
az postgres flexible-server create \
  --resource-group $RESOURCE_GROUP \
  --name taaip-postgres-prod \
  --location $LOCATION \
  --admin-user taaip_admin \
  --admin-password 'CHANGE_THIS_SECURE_PASSWORD' \
  --sku-name Standard_D2s_v3 \
  --tier GeneralPurpose \
  --storage-size 128 \
  --version 14 \
  --public-access None \
  --vnet vnet-taaip \
  --subnet subnet-database

# Create database
az postgres flexible-server db create \
  --resource-group $RESOURCE_GROUP \
  --server-name taaip-postgres-prod \
  --database-name taaip_recruiting
```

### Step 5: Create Redis Cache

```bash
az redis create \
  --resource-group $RESOURCE_GROUP \
  --name taaip-redis-prod \
  --location $LOCATION \
  --sku Basic \
  --vm-size c0 \
  --enable-non-ssl-port false
```

### Step 6: Create Container Registry

```bash
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name taaipacrprod \
  --sku Standard \
  --admin-enabled true
```

---

## Phase 3: Application Deployment

### Step 1: Build and Push Docker Images

```bash
# Login to registry
az acr login --name taaipacrprod

# Get registry URL
REGISTRY_URL=$(az acr show --name taaipacrprod --query loginServer --output tsv)

# Build and push backend
cd /Users/ambermooney/Desktop/TAAIP
docker build -f Dockerfile.backend -t $REGISTRY_URL/taaip-backend:latest .
docker push $REGISTRY_URL/taaip-backend:latest

# Build and push frontend
cd taaip-dashboard
docker build -t $REGISTRY_URL/taaip-frontend:latest \
  --build-arg VITE_API_URL=https://taaip-api.azuregovapps.us .
docker push $REGISTRY_URL/taaip-frontend:latest
```

### Step 2: Create App Service Plan

```bash
az appservice plan create \
  --resource-group $RESOURCE_GROUP \
  --name plan-taaip-prod \
  --location $LOCATION \
  --is-linux \
  --sku P1V2
```

### Step 3: Deploy Backend API

```bash
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan plan-taaip-prod \
  --name taaip-api-prod \
  --deployment-container-image-name $REGISTRY_URL/taaip-backend:latest

# Configure backend
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name taaip-api-prod \
  --settings \
    DATABASE_URL="postgresql://taaip_admin:PASSWORD@taaip-postgres-prod.postgres.database.usgovcloudapi.net:5432/taaip_recruiting" \
    REDIS_URL="redis://taaip-redis-prod.redis.cache.usgovcloudapi.net:6380" \
    JWT_SECRET="GENERATE_SECURE_RANDOM_STRING" \
    ENVIRONMENT="production"

# Enable managed identity for CAC
az webapp identity assign \
  --resource-group $RESOURCE_GROUP \
  --name taaip-api-prod
```

### Step 4: Deploy Frontend

```bash
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan plan-taaip-prod \
  --name taaip-frontend-prod \
  --deployment-container-image-name $REGISTRY_URL/taaip-frontend:latest

# Configure frontend
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name taaip-frontend-prod \
  --settings \
    API_URL="https://taaip-api-prod.azuregovapps.us"
```

---

## Phase 4: Security Configuration

### Step 1: Enable HTTPS Only

```bash
az webapp update \
  --resource-group $RESOURCE_GROUP \
  --name taaip-api-prod \
  --https-only true

az webapp update \
  --resource-group $RESOURCE_GROUP \
  --name taaip-frontend-prod \
  --https-only true
```

### Step 2: Configure WAF (Web Application Firewall)

```bash
# Create Application Gateway with WAF
az network application-gateway waf-config set \
  --resource-group $RESOURCE_GROUP \
  --gateway-name taaip-appgw \
  --enabled true \
  --firewall-mode Prevention \
  --rule-set-type OWASP \
  --rule-set-version 3.0
```

### Step 3: Enable CAC Authentication

```bash
# Configure Azure AD for CAC/PIV
az webapp auth update \
  --resource-group $RESOURCE_GROUP \
  --name taaip-frontend-prod \
  --enabled true \
  --action LoginWithAzureActiveDirectory \
  --aad-allowed-token-audiences "https://taaip-frontend-prod.azuregovapps.us"

# Your G6 will provide:
# - Azure AD Tenant ID
# - Client ID for CAC integration
# - Certificate mapping for DoD PKI
```

### Step 4: Enable Diagnostic Logging

```bash
# Create Log Analytics workspace
az monitor log-analytics workspace create \
  --resource-group $RESOURCE_GROUP \
  --workspace-name taaip-logs

# Enable diagnostics
az monitor diagnostic-settings create \
  --name taaip-diagnostics \
  --resource-group $RESOURCE_GROUP \
  --workspace taaip-logs \
  --logs '[{"category": "AppServiceConsoleLogs", "enabled": true}]'
```

---

## Phase 5: Database Migration

### Step 1: Export Local Database

```bash
# On your Mac
cd /Users/ambermooney/Desktop/TAAIP
sqlite3 recruiting.db .dump > taaip_dump.sql
```

### Step 2: Convert to PostgreSQL

```bash
# Install pgloader
brew install pgloader

# Convert SQLite to PostgreSQL
pgloader recruiting.db postgresql://taaip_admin:PASSWORD@taaip-postgres-prod.postgres.database.usgovcloudapi.net:5432/taaip_recruiting
```

### Step 3: Verify Migration

```bash
# Connect to PostgreSQL
psql postgresql://taaip_admin:PASSWORD@taaip-postgres-prod.postgres.database.usgovcloudapi.net:5432/taaip_recruiting

# Check tables
\dt

# Verify data
SELECT COUNT(*) FROM contracts;
SELECT COUNT(*) FROM cbsa_data;
```

---

## Phase 6: Monitoring & Compliance

### Step 1: Enable Azure Monitor

```bash
# Create alerts for critical metrics
az monitor metrics alert create \
  --resource-group $RESOURCE_GROUP \
  --name taaip-high-response-time \
  --description "Alert when API response time > 2 seconds" \
  --condition "avg Percentage CPU > 80" \
  --window-size 5m \
  --evaluation-frequency 1m
```

### Step 2: Configure Backups

```bash
# Enable automatic database backups
az postgres flexible-server backup create \
  --resource-group $RESOURCE_GROUP \
  --name taaip-postgres-prod \
  --backup-name daily-backup

# Configure retention
az postgres flexible-server parameter set \
  --resource-group $RESOURCE_GROUP \
  --server-name taaip-postgres-prod \
  --name backup_retention_days \
  --value 30
```

### Step 3: Implement Audit Logging

```bash
# Enable audit logs for compliance
az postgres flexible-server parameter set \
  --resource-group $RESOURCE_GROUP \
  --server-name taaip-postgres-prod \
  --name pgaudit.log \
  --value "all"
```

---

## Phase 7: Custom Domain & SSL

### Step 1: Add Custom Domain

```bash
# Add .mil domain (requires DNS validation)
az webapp config hostname add \
  --resource-group $RESOURCE_GROUP \
  --webapp-name taaip-frontend-prod \
  --hostname taaip.usarec.army.mil

# Bind SSL certificate (DoD wildcard cert)
az webapp config ssl upload \
  --resource-group $RESOURCE_GROUP \
  --name taaip-frontend-prod \
  --certificate-file /path/to/dod-cert.pfx \
  --certificate-password 'CERT_PASSWORD'

az webapp config ssl bind \
  --resource-group $RESOURCE_GROUP \
  --name taaip-frontend-prod \
  --certificate-thumbprint <thumbprint> \
  --ssl-type SNI
```

---

## RMF/ATO Documentation

### Required Documents (Templates from DISA)

1. **System Security Plan (SSP)**
   ```
   - System categorization: LOW impact
   - Security controls: NIST 800-53 (Moderate baseline)
   - Boundary definition: Azure Gov VNet
   ```

2. **Security Assessment Report (SAR)**
   ```
   - Penetration testing results
   - Vulnerability scan reports
   - Compliance matrix
   ```

3. **Plan of Action & Milestones (POA&M)**
   ```
   - Known vulnerabilities
   - Remediation timeline
   - Risk acceptance
   ```

4. **Continuous Monitoring Plan**
   ```
   - Azure Monitor integration
   - SIEM configuration (Splunk/Azure Sentinel)
   - Incident response procedures
   ```

### Compliance Checklist

- [ ] Azure Gov subscription in correct region
- [ ] VNet with proper segmentation
- [ ] Database encryption at rest (enabled by default)
- [ ] TLS 1.2+ for all connections
- [ ] CAC/PIV authentication configured
- [ ] Web Application Firewall enabled
- [ ] DDoS protection enabled
- [ ] Audit logging to SIEM
- [ ] Automated backups (30 day retention)
- [ ] Disaster recovery plan documented
- [ ] Incident response plan documented
- [ ] Security training for admins completed
- [ ] Provisional ATO signed
- [ ] Continuous monitoring active

---

## Cost Optimization

### Production Environment (~$300/month)

| Service | SKU | Cost/Month |
|---------|-----|------------|
| App Service Plan | P1V2 | $146 |
| PostgreSQL | Standard_D2s_v3 | $120 |
| Redis Cache | Basic C0 | $16 |
| Application Gateway + WAF | WAF_v2 | $125 |
| Log Analytics | 5GB/day | $15 |
| **Total** | | **~$422** |

### Cost Savings

```bash
# Use reserved instances (save 30-40%)
az reservations reservation-order purchase \
  --reservation-order-id <order-id> \
  --term P1Y

# Auto-scaling for non-peak hours
az monitor autoscale create \
  --resource-group $RESOURCE_GROUP \
  --name taaip-autoscale \
  --min-count 1 \
  --max-count 3 \
  --count 1
```

---

## Maintenance

### Update Application

```bash
# Build new version
docker build -t $REGISTRY_URL/taaip-backend:v2.0.1 .
docker push $REGISTRY_URL/taaip-backend:v2.0.1

# Update app service
az webapp config container set \
  --resource-group $RESOURCE_GROUP \
  --name taaip-api-prod \
  --docker-custom-image-name $REGISTRY_URL/taaip-backend:v2.0.1

# Restart
az webapp restart --resource-group $RESOURCE_GROUP --name taaip-api-prod
```

### Database Maintenance

```bash
# Manual backup
az postgres flexible-server backup create \
  --resource-group $RESOURCE_GROUP \
  --name taaip-postgres-prod \
  --backup-name manual-backup-$(date +%Y%m%d)

# Restore from backup
az postgres flexible-server restore \
  --resource-group $RESOURCE_GROUP \
  --name taaip-postgres-restored \
  --source-server taaip-postgres-prod \
  --restore-time "2025-11-19T12:00:00Z"
```

---

## Troubleshooting

### View Application Logs

```bash
az webapp log tail \
  --resource-group $RESOURCE_GROUP \
  --name taaip-api-prod
```

### Connect to Database

```bash
az postgres flexible-server connect \
  --resource-group $RESOURCE_GROUP \
  --name taaip-postgres-prod \
  --database-name taaip_recruiting \
  --admin-user taaip_admin
```

### Check Service Health

```bash
# Backend health
curl https://taaip-api-prod.azuregovapps.us/health

# Check all resources
az resource list \
  --resource-group $RESOURCE_GROUP \
  --output table
```

---

## Support & Resources

- **Azure Gov Portal**: https://portal.azure.us
- **Azure Gov Docs**: https://docs.microsoft.com/en-us/azure/azure-government/
- **DISA Cloud SRG**: https://public.cyber.mil/dccs/
- **RMF Knowledge Service**: https://rmf.org
- **Your G6/IM Office**: Contact for ATO support

---

## Timeline Checklist

### Week 1-2: Account Setup
- [ ] Submit Azure Gov account request
- [ ] Complete security training
- [ ] Obtain CAC credentials for Azure

### Week 3-4: Infrastructure
- [ ] Create resource groups and VNets
- [ ] Deploy database and cache
- [ ] Deploy application services

### Month 2: Security
- [ ] Configure CAC authentication
- [ ] Enable WAF and monitoring
- [ ] Complete security scans

### Month 3-4: Documentation
- [ ] Complete SSP
- [ ] Generate SAR
- [ ] Submit ATO package

### Month 5-6: Testing & Approval
- [ ] Security assessment by IA team
- [ ] Remediate findings
- [ ] Obtain provisional ATO
- [ ] Launch to users

---

**Next Steps:**
1. Contact your G6 with account request
2. Meanwhile, test on DigitalOcean pilot
3. Prepare RMF documentation using templates
4. Schedule security assessment
