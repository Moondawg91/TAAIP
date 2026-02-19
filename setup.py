#!/usr/bin/env python3
"""
TAAIP 2.0 Setup Script
Initializes database and validates configuration
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    print("=" * 60)
    print("TAAIP 2.0 - Initial Setup")
    print("=" * 60)
    
    # Step 1: Check Python version
    print("\n[1/6] Checking Python version...")
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Step 2: Check environment variables
    print("\n[2/6] Checking configuration...")
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("⚠️  DATABASE_URL not set - will use SQLite (dev only)")
        print("   For production, set: export DATABASE_URL='postgresql://user:pass@host:5432/taaip'")
    else:
        print(f"✅ DATABASE_URL configured: {db_url[:30]}...")
    
    # Step 3: Install dependencies
    print("\n[3/6] Installing Python dependencies...")
    try:
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed")
    except Exception as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    
    # Step 4: Initialize database
    print("\n[4/6] Initializing database...")
    try:
        from database.config import init_db, get_db_health
        init_db()
        health = get_db_health()
        if health['status'] == 'healthy':
            print(f"✅ Database initialized ({health['database_type']})")
        else:
            print(f"❌ Database health check failed: {health.get('error')}")
            return False
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 5: Create data directory
    print("\n[5/6] Creating data directories...")
    data_dir = project_root / "data"
    data_dir.mkdir(exist_ok=True)
    print(f"✅ Data directory: {data_dir}")
    
    # Step 6: Summary
    print("\n[6/6] Setup complete!")
    print("\n" + "=" * 60)
    print("Next Steps:")
    print("=" * 60)
    print("1. Start backend server:")
    print("   python3 -m uvicorn taaip_service:app --reload --host 0.0.0.0 --port 8000")
    print("\n2. Start frontend:")
    print("   cd taaip-dashboard && npm run dev")
    print("\n3. Access dashboard:")
    print("   http://localhost:5173")
    print("\n4. For production, configure:")
    print("   - PostgreSQL: export DATABASE_URL='postgresql://...'")
    print("   - API Keys: export EMM_API_KEY='...', SPRINKLR_API_KEY='...'")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
