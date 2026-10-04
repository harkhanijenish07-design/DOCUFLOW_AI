import os
import sys
from pathlib import Path

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import SessionLocal, init_db
from app.models.user import User
from app.models.workflow import Workflow
from app.utils.auth import hash_password

def seed_database():
    init_db()
    db = SessionLocal()
    
    # 1. Create a demo user
    demo_email = "demo@docuflow.ai"
    user = db.query(User).filter(User.email == demo_email).first()
    if not user:
        print(f"Creating demo user: {demo_email}")
        user = User(
            name="Demo User",
            email=demo_email,
            password_hash=hash_password("password123")
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        print(f"Demo user {demo_email} already exists.")
        
    # 2. Create some default workflows
    workflows = [
        {
            "name": "Invoice High Value Notification",
            "document_type": "invoice",
            "conditions": [{"field": "total_amount", "operator": ">", "value": 50000}],
            "actions": [{"type": "slack", "config": {"channel": "#finance-alerts"}}],
            "enabled": True,
            "require_approval": True
        },
        {
            "name": "Extract Candidate Info",
            "document_type": "resume",
            "conditions": [], # Always run for resumes
            "actions": [{"type": "database", "config": {"table": "candidates"}}, {"type": "google_sheets", "config": {"sheet": "HR_Pipeline"}}],
            "enabled": True,
            "require_approval": False
        },
         {
            "name": "Flag High Risk KYC",
            "document_type": "kyc",
            "conditions": [], 
            "actions": [{"type": "email", "config": {"to": "compliance@docuflow.ai", "subject": "New KYC Document Submitted"}}],
            "enabled": True,
            "require_approval": True
        }
    ]
    
    for wf_data in workflows:
        wf = db.query(Workflow).filter(Workflow.name == wf_data["name"]).first()
        if not wf:
            print(f"Creating workflow: {wf_data['name']}")
            workflow = Workflow(**wf_data)
            db.add(workflow)
    
    db.commit()
    db.close()
    print("Database seeding completed.")

if __name__ == "__main__":
    seed_database()
