import uuid
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Role


def seed_roles():
    db: Session = SessionLocal()
    base_roles = [
        {
            "name": "admin",
            "permissions": {
                "assets": 3,
                "sites": 3,
                "areas": 3,
                "locations": 3,
                "suppliers": 3,
                "contacts": 3,
                "manufacturers": 3,
                "asset_types": 3,
                "asset_statuses": 3,
                "users": 3,
                "roles": 3,
                "audit_logs": 3,
                "utility": 3,
                "asset_documents": 3,
                "asset_photos": 3,
                "locations_floormap": 3,
            },
        },
        {
            "name": "editor",
            "permissions": {
                "assets": 2,
                "sites": 2,
                "areas": 2,
                "locations": 2,
                "suppliers": 2,
                "contacts": 2,
                "manufacturers": 2,
                "asset_types": 2,
                "asset_statuses": 2,
                "users": 1,
                "roles": 1,
                "audit_logs": 1,
                "utility": 2,
                "asset_documents": 2,
                "asset_photos": 2,
                "locations_floormap": 2,
            },
        },
        {
            "name": "viewer",
            "permissions": {
                "assets": 1,
                "sites": 1,
                "areas": 1,
                "locations": 1,
                "suppliers": 1,
                "contacts": 1,
                "manufacturers": 1,
                "asset_types": 1,
                "asset_statuses": 1,
                "users": 0,
                "roles": 1,
                "audit_logs": 1,
                "utility": 1,
                "asset_documents": 1,
                "asset_photos": 1,
                "locations_floormap": 1,
            },
        },
    ]
    for role_data in base_roles:
        role = db.query(Role).filter_by(name=role_data["name"]).first()
        if not role:
            new_role = Role(
                id=uuid.uuid4(),
                name=role_data["name"],
                permissions=role_data["permissions"],
            )
            db.add(new_role)
            # print(f"Role {role_data['name']} created.")
        else:
            # print(f"Role {role_data['name']} already exists.")
            pass
    db.commit()
    db.close()


if __name__ == "__main__":
    seed_roles()
