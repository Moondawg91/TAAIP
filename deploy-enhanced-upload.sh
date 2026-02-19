#!/bin/bash

# Enhanced Upload System Deployment Script
# Run this on your DigitalOcean droplet

echo "=========================================="
echo "Enhanced Upload System Deployment"
echo "=========================================="
echo ""

cd /opt/TAAIP || exit 1

echo "📥 Step 1: Pulling latest code..."
git pull origin feat/optimize-app

echo ""
echo "🗄️  Step 2: Running database migration..."
python3 migrate_pipeline_tables.py

echo ""
echo "🛑 Step 3: Stopping containers..."
/usr/bin/docker-compose down

echo ""
echo "🔨 Step 4: Rebuilding containers..."
echo "   (This will take 2-3 minutes)"
/usr/bin/docker-compose up -d --build

echo ""
echo "⏳ Step 5: Waiting for services to start..."
sleep 15

echo ""
echo "✅ Step 6: Verifying deployment..."
/usr/bin/docker-compose ps

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "🎉 Enhanced Upload System Features:"
echo ""
echo "Data Types Now Supported:"
echo "  1. Leads - Initial contacts and inquiries"
echo "  2. Prospects - Qualified and contacted leads"
echo "  3. Applicants - Active applicants in process"
echo "  4. Future Soldiers - Contracted soldiers awaiting ship"
echo "  5. Events - Recruiting events and activities"
echo "  6. Projects - Project management and tracking"
echo "  7. Marketing Activities - Marketing campaigns"
echo "  8. Budgets - Budget allocation and tracking"
echo ""
echo "New Lead Fields:"
echo "  Required: first_name, last_name, date_of_birth, education_code,"
echo "            phone_number, lead_source, prid"
echo "  Optional: cbsa_code, middle_name, address, asvab_score"
echo ""
echo "Access at: http://129.212.185.3"
echo "  → Operations → 'Upload Data'"
echo ""
echo "📖 Check UPLOAD_DATA_GUIDE.md for complete documentation"
echo ""
