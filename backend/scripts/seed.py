"""
Seed Field Service demo data (fictional only).

Targets:
  - 1 primary demo org + 1 isolation org
  - ≥2 roles (admin/dispatcher + technicians)
  - 12 customers, 15 assets, 20 work orders, 5 technicians + history

Usage:
  cd backend
  python -m scripts.seed
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import delete

from app.core.database import SessionLocal
from app.core.security import hash_password, hash_portal_token
from app.models import (
    Asset,
    Attachment,
    AuditEvent,
    Checklist,
    ChecklistItem,
    Customer,
    CustomerPortalLink,
    CustomerSignoff,
    JobActivity,
    Organization,
    PartUsed,
    ServiceLocation,
    TimeEntry,
    User,
    WorkOrder,
    WorkOrderAssignment,
)
from app.models.enums import (
    JobActivityType,
    UserRole,
    WorkOrderPriority,
    WorkOrderStatus,
)

DEMO_ORG_ID = uuid.UUID("00000000-0000-4000-8000-000000000010")
OTHER_ORG_ID = uuid.UUID("00000000-0000-4000-8000-000000000099")
DEMO_PASSWORD = "demo"
# Known raw portal token for DEMO.md (hash stored at rest only)
DEMO_PORTAL_RAW_TOKEN = "demo-portal-status-token-m6-northwind"
UTC = timezone.utc


CUSTOMER_SPECS = [
    ("Northwind Bakery", "ops@northwind-bakery.example", "555-0101"),
    ("Cedar Ridge Clinic", "facilities@cedar-clinic.example", "555-0102"),
    ("Maple Street Books", "front@maplebooks.example", "555-0103"),
    ("Harborview Apartments", "maint@harborview.example", "555-0104"),
    ("Brightline Auto Shop", "service@brightline-auto.example", "555-0105"),
    ("Summit Dental Group", "admin@summitdental.example", "555-0106"),
    ("Riverbend Cafe", "manager@riverbend-cafe.example", "555-0107"),
    ("Oak & Iron Gym", "ops@oakiron-gym.example", "555-0108"),
    ("Pinecrest Library", "building@pinecrest-lib.example", "555-0109"),
    ("Lakeside Veterinary", "desk@lakeside-vet.example", "555-0110"),
    ("Westfield Co-op Market", "facilities@westfield-coop.example", "555-0111"),
    ("Copper Lantern Inn", "gm@copper-lantern.example", "555-0112"),
]

ASSET_SPECS = [
    (0, "Rooftop HVAC Unit A", "HVAC-RTU-1001", "HVAC", "CoolAir", "CA-900"),
    (0, "Walk-in Cooler", "REF-WLK-2044", "Refrigeration", "FrostKing", "FK-22"),
    (1, "Air Handler Wing B", "HVAC-AHU-3301", "HVAC", "CoolAir", "AH-400"),
    (1, "Emergency Generator", "PWR-GEN-7788", "Power", "VoltSafe", "VS-150"),
    (2, "Boiler Plant", "BLR-MAIN-12", "Plumbing", "HeatWell", "HW-80"),
    (3, "Elevator Bank 1", "ELV-BK1-09", "Elevator", "LiftCo", "LC-X3"),
    (3, "Fire Panel Lobby", "FIR-PNL-01", "Safety", "SafeWatch", "SW-9"),
    (4, "Compressor Bay 2", "AIR-CMP-552", "Compressed Air", "BlastAir", "BA-60"),
    (5, "Sterilizer Unit", "MED-STR-441", "Medical", "SteriPro", "SP-2"),
    (6, "Espresso Machine Line", "KIT-ESP-19", "Kitchen", "BaristaMax", "BM-Pro"),
    (7, "Pool Pump System", "PLB-PMP-77", "Plumbing", "FlowRight", "FR-30"),
    (8, "Chiller Plant", "HVAC-CHL-05", "HVAC", "CoolAir", "CH-500"),
    (9, "X-Ray Cooling Loop", "MED-XRY-03", "Medical", "MedCool", "MC-1"),
    (10, "Freezer Aisle 4", "REF-FRZ-A4", "Refrigeration", "FrostKing", "FK-40"),
    (11, "Guest Laundry Dryer Bank", "LND-DRY-08", "Laundry", "SpinWell", "SW-D4"),
]

JOB_TITLES = [
    "Quarterly HVAC filter service",
    "Walk-in cooler not holding temp",
    "Air handler vibration complaint",
    "Generator weekly exercise check",
    "Boiler pressure relief inspection",
    "Elevator call button intermittent",
    "Fire panel trouble light",
    "Compressor oil change",
    "Sterilizer cycle timeout",
    "Espresso machine descaling",
    "Pool pump seal leak",
    "Chiller condenser coil cleaning",
    "X-ray cooler flow alarm",
    "Freezer door gasket replacement",
    "Dryer lint trap backlog",
    "Emergency after-hours HVAC call",
    "Install new thermostat",
    "Recurring refrigerant leak check",
    "Preventive maintenance — rooftop",
    "Customer-reported noise investigation",
]


def _clear_org(db, org_id: uuid.UUID) -> None:
    """Remove seeded rows for an org (child tables first)."""
    db.execute(
        delete(CustomerPortalLink).where(CustomerPortalLink.organization_id == org_id)
    )
    db.execute(delete(ChecklistItem).where(ChecklistItem.organization_id == org_id))
    db.execute(delete(Checklist).where(Checklist.organization_id == org_id))
    db.execute(delete(CustomerSignoff).where(CustomerSignoff.organization_id == org_id))
    db.execute(delete(Attachment).where(Attachment.organization_id == org_id))
    db.execute(delete(PartUsed).where(PartUsed.organization_id == org_id))
    db.execute(delete(TimeEntry).where(TimeEntry.organization_id == org_id))
    db.execute(delete(JobActivity).where(JobActivity.organization_id == org_id))
    db.execute(
        delete(WorkOrderAssignment).where(WorkOrderAssignment.organization_id == org_id)
    )
    db.execute(delete(WorkOrder).where(WorkOrder.organization_id == org_id))
    db.execute(delete(AuditEvent).where(AuditEvent.organization_id == org_id))
    db.execute(delete(Asset).where(Asset.organization_id == org_id))
    db.execute(delete(ServiceLocation).where(ServiceLocation.organization_id == org_id))
    db.execute(delete(Customer).where(Customer.organization_id == org_id))
    db.execute(delete(User).where(User.organization_id == org_id))
    db.execute(delete(Organization).where(Organization.id == org_id))
    db.flush()


def seed() -> None:
    db = SessionLocal()
    try:
        _clear_org(db, DEMO_ORG_ID)
        _clear_org(db, OTHER_ORG_ID)

        org = Organization(
            id=DEMO_ORG_ID,
            name="Demo Field Ops LLC",
            slug="demo-field-ops",
        )
        other = Organization(
            id=OTHER_ORG_ID,
            name="Other Tenant HVAC",
            slug="other-tenant-hvac",
        )
        db.add_all([org, other])
        db.flush()

        password_hash = hash_password(DEMO_PASSWORD)
        dispatcher = User(
            id=uuid.UUID("00000000-0000-4000-8000-000000000001"),
            organization_id=DEMO_ORG_ID,
            email="dispatcher@demo.local",
            password_hash=password_hash,
            display_name="Dana Dispatcher",
            role=UserRole.DISPATCHER.value,
            phone="555-1000",
        )
        admin = User(
            id=uuid.UUID("00000000-0000-4000-8000-000000000000"),
            organization_id=DEMO_ORG_ID,
            email="admin@demo.local",
            password_hash=password_hash,
            display_name="Alex Admin",
            role=UserRole.ADMIN.value,
            phone="555-1001",
        )

        tech_specs = [
            ("00000000-0000-4000-8000-000000000002", "tech@demo.local", "Terry Technician", "HVAC"),
            ("00000000-0000-4000-8000-000000000003", "tech2@demo.local", "Sam Rivera", "Plumbing"),
            ("00000000-0000-4000-8000-000000000004", "tech3@demo.local", "Jordan Lee", "Electrical"),
            ("00000000-0000-4000-8000-000000000005", "tech4@demo.local", "Casey Nguyen", "HVAC"),
            ("00000000-0000-4000-8000-000000000006", "tech5@demo.local", "Riley Brooks", "General"),
        ]
        technicians: list[User] = []
        for uid, email, name, skills in tech_specs:
            technicians.append(
                User(
                    id=uuid.UUID(uid),
                    organization_id=DEMO_ORG_ID,
                    email=email,
                    password_hash=password_hash,
                    display_name=name,
                    role=UserRole.TECHNICIAN.value,
                    skills=skills,
                )
            )

        other_user = User(
            id=uuid.UUID("00000000-0000-4000-8000-000000000090"),
            organization_id=OTHER_ORG_ID,
            email="other@demo.local",
            password_hash=password_hash,
            display_name="Other Org Dispatcher",
            role=UserRole.DISPATCHER.value,
        )
        db.add_all([dispatcher, admin, *technicians, other_user])
        db.flush()

        customers: list[Customer] = []
        locations: list[ServiceLocation] = []
        for idx, (name, email, phone) in enumerate(CUSTOMER_SPECS):
            cust = Customer(
                id=uuid.uuid5(DEMO_ORG_ID, f"customer-{idx}"),
                organization_id=DEMO_ORG_ID,
                name=name,
                email=email,
                phone=phone,
                notes="Fictional demo customer",
            )
            customers.append(cust)
            locations.append(
                ServiceLocation(
                    id=uuid.uuid5(DEMO_ORG_ID, f"location-{idx}"),
                    organization_id=DEMO_ORG_ID,
                    customer_id=cust.id,
                    name=f"{name} — Main Site",
                    address_line1=f"{100 + idx} Demo Avenue",
                    city="Springfield",
                    region="IL",
                    postal_code=f"6270{idx % 10}",
                    country="US",
                )
            )
        db.add_all(customers)
        db.add_all(locations)
        db.flush()

        other_customer = Customer(
            id=uuid.uuid5(OTHER_ORG_ID, "customer-0"),
            organization_id=OTHER_ORG_ID,
            name="Secret Other Tenant Site",
            email="secret@other-tenant.example",
            phone="555-9999",
        )
        db.add(other_customer)
        db.flush()

        assets: list[Asset] = []
        for idx, (cust_idx, name, serial, atype, mfr, model) in enumerate(ASSET_SPECS):
            assets.append(
                Asset(
                    id=uuid.uuid5(DEMO_ORG_ID, f"asset-{idx}"),
                    organization_id=DEMO_ORG_ID,
                    customer_id=customers[cust_idx].id,
                    service_location_id=locations[cust_idx].id,
                    name=name,
                    serial_number=serial,
                    asset_type=atype,
                    manufacturer=mfr,
                    model_number=model,
                    warranty_expires_on=date(2027, 6, 1) + timedelta(days=idx * 10),
                    maintenance_notes=(
                        "Seeded maintenance history for Service Memory demos. "
                        "Watch for recurring filter clog and seal/leak patterns."
                    ),
                )
            )
        db.add_all(assets)
        db.flush()

        now = datetime.now(tz=UTC)
        statuses = [
            WorkOrderStatus.DRAFT,
            WorkOrderStatus.SCHEDULED,
            WorkOrderStatus.EN_ROUTE,
            WorkOrderStatus.IN_PROGRESS,
            WorkOrderStatus.WAITING_FOR_PARTS,
            WorkOrderStatus.COMPLETED,
            WorkOrderStatus.CANCELLED,
            WorkOrderStatus.COMPLETED,
            WorkOrderStatus.SCHEDULED,
            WorkOrderStatus.IN_PROGRESS,
            WorkOrderStatus.COMPLETED,
            WorkOrderStatus.SCHEDULED,
            WorkOrderStatus.COMPLETED,
            WorkOrderStatus.EN_ROUTE,
            WorkOrderStatus.DRAFT,
            WorkOrderStatus.COMPLETED,
            WorkOrderStatus.SCHEDULED,
            WorkOrderStatus.COMPLETED,
            WorkOrderStatus.IN_PROGRESS,
            WorkOrderStatus.COMPLETED,
        ]
        priorities = [
            WorkOrderPriority.NORMAL,
            WorkOrderPriority.HIGH,
            WorkOrderPriority.LOW,
            WorkOrderPriority.URGENT,
        ]

        work_orders: list[WorkOrder] = []
        for i, title in enumerate(JOB_TITLES):
            asset = assets[i % len(assets)]
            cust = next(c for c in customers if c.id == asset.customer_id)
            loc = next(loc for loc in locations if loc.customer_id == cust.id)
            due_at = now + timedelta(days=(i % 7) - 2, hours=9)
            # Spread windows so seed data does not flood overlap warnings
            scheduled_start = due_at.replace(minute=0, second=0, microsecond=0) + timedelta(
                hours=(i % 5)
            )
            scheduled_end = scheduled_start + timedelta(hours=2)
            wo = WorkOrder(
                id=uuid.uuid5(DEMO_ORG_ID, f"wo-{i}"),
                organization_id=DEMO_ORG_ID,
                customer_id=cust.id,
                service_location_id=loc.id,
                asset_id=asset.id,
                title=title,
                description=f"Demo work order #{i + 1}: {title}",
                status=statuses[i].value,
                priority=priorities[i % len(priorities)].value,
                due_at=due_at,
                scheduled_start=scheduled_start,
                scheduled_end=scheduled_end,
                skill_required=technicians[i % 5].skills,
                estimate_amount=Decimal("150.00") + Decimal(i * 25),
                labor_rate=Decimal("95.00"),
                created_by_id=dispatcher.id,
            )
            work_orders.append(wo)
        db.add_all(work_orders)
        db.flush()

        for i, wo in enumerate(work_orders):
            tech = technicians[i % 5]
            db.add(
                WorkOrderAssignment(
                    organization_id=DEMO_ORG_ID,
                    work_order_id=wo.id,
                    technician_id=tech.id,
                    assigned_at=now - timedelta(days=max(0, 10 - i)),
                    notes="Seeded assignment",
                )
            )
            cl = Checklist(
                organization_id=DEMO_ORG_ID,
                work_order_id=wo.id,
                name="Standard site checklist",
                template_key="standard_site",
            )
            db.add(cl)
            db.flush()
            for j, label in enumerate(
                ("Arrive on site", "PPE confirmed", "Customer notified", "Work area secured")
            ):
                db.add(
                    ChecklistItem(
                        organization_id=DEMO_ORG_ID,
                        checklist_id=cl.id,
                        label=label,
                        is_required=True,
                        is_completed=wo.status
                        in (
                            WorkOrderStatus.COMPLETED.value,
                            WorkOrderStatus.IN_PROGRESS.value,
                        )
                        and j < 2,
                        sort_order=j,
                        completed_at=now - timedelta(hours=j) if j < 2 else None,
                    )
                )

            # Recurring-failure themes for Service Memory demos (filter clog / leak / seal).
            asset_ref = assets[i % len(assets)]
            if asset_ref.asset_type == "HVAC" or "filter" in title.lower() or "HVAC" in title:
                note_text = (
                    f"Recurring filter clog on {asset_ref.name}: replaced dirty filter media, "
                    f"coil airflow restricted; recommend quarterly filter PM."
                )
            elif asset_ref.asset_type == "Refrigeration" or "leak" in title.lower() or "cooler" in title.lower():
                note_text = (
                    f"Recurring refrigerant leak / gasket seal issue on {asset_ref.name}: "
                    f"found weep at joint, topped charge temporarily; schedule leak follow-up."
                )
            elif "vibration" in title.lower() or "noise" in title.lower():
                note_text = (
                    f"Intermittent vibration/noise on {asset_ref.name}; "
                    f"checked mounts and bearings — monitor for recurrence."
                )
            else:
                note_text = (
                    f"History note for job {i + 1}: inspected {asset_ref.name}."
                )
            db.add(
                JobActivity(
                    organization_id=DEMO_ORG_ID,
                    work_order_id=wo.id,
                    actor_user_id=tech.id,
                    activity_type=JobActivityType.NOTE.value,
                    note=note_text,
                    occurred_at=now - timedelta(days=i % 14, hours=2),
                )
            )
            db.add(
                JobActivity(
                    organization_id=DEMO_ORG_ID,
                    work_order_id=wo.id,
                    actor_user_id=dispatcher.id,
                    activity_type=JobActivityType.STATUS_CHANGE.value,
                    note=f"Status set to {wo.status}",
                    occurred_at=now - timedelta(days=i % 14, hours=1),
                )
            )

            if wo.status in (
                WorkOrderStatus.COMPLETED.value,
                WorkOrderStatus.IN_PROGRESS.value,
                WorkOrderStatus.WAITING_FOR_PARTS.value,
            ):
                started = now - timedelta(days=i % 10, hours=4)
                ended = started + timedelta(hours=2, minutes=15) if wo.status == WorkOrderStatus.COMPLETED.value else None
                minutes = 135 if ended else None
                db.add(
                    TimeEntry(
                        organization_id=DEMO_ORG_ID,
                        work_order_id=wo.id,
                        technician_id=tech.id,
                        started_at=started,
                        ended_at=ended,
                        minutes=minutes,
                        notes="Seeded labor time",
                        was_corrected=False,
                    )
                )
                db.add(
                    PartUsed(
                        organization_id=DEMO_ORG_ID,
                        work_order_id=wo.id,
                        part_name="Filter media pack" if i % 2 == 0 else "Seal kit",
                        quantity=Decimal("1"),
                        unit_cost=Decimal("24.50") + Decimal(i),
                    )
                )
                db.add(
                    Attachment(
                        organization_id=DEMO_ORG_ID,
                        work_order_id=wo.id,
                        filename=f"job-{i + 1}-photo.jpg",
                        content_type="image/jpeg",
                        storage_key=f"demo/attachments/job-{i + 1}-photo.jpg",
                        byte_size=1024 * (20 + i),
                        uploaded_by_id=tech.id,
                    )
                )

            if wo.status == WorkOrderStatus.COMPLETED.value:
                db.add(
                    CustomerSignoff(
                        organization_id=DEMO_ORG_ID,
                        work_order_id=wo.id,
                        signer_name="Pat Customer",
                        signed_at=now - timedelta(days=i % 8),
                        acknowledgement_text=(
                            "I acknowledge the work described was completed. "
                            "This is not a certified e-signature."
                        ),
                        signature_storage_key=f"demo/signoffs/job-{i + 1}.png",
                    )
                )

            db.add(
                AuditEvent(
                    organization_id=DEMO_ORG_ID,
                    actor_user_id=dispatcher.id,
                    entity_type="work_order",
                    entity_id=wo.id,
                    action="seed_created",
                    payload={"title": wo.title, "status": wo.status},
                )
            )

        # Seed one active customer portal link on an in-progress HVAC job
        portal_wo = next(
            (
                wo
                for wo in work_orders
                if wo.status == WorkOrderStatus.IN_PROGRESS.value
            ),
            work_orders[3],
        )
        db.add(
            CustomerPortalLink(
                id=uuid.uuid5(DEMO_ORG_ID, "portal-link-demo"),
                organization_id=DEMO_ORG_ID,
                work_order_id=portal_wo.id,
                token_hash=hash_portal_token(DEMO_PORTAL_RAW_TOKEN),
                expires_at=now + timedelta(days=7),
                created_by_id=dispatcher.id,
            )
        )

        db.commit()
        print("Field Service seed complete.")
        print(f"  Org: {org.name} ({org.slug})")
        print(f"  Customers: {len(customers)} (+1 other-org isolation row)")
        print(f"  Assets: {len(assets)}")
        print(f"  Work orders: {len(work_orders)}")
        print(f"  Technicians: {len(technicians)}")
        print(f"  Demo portal status URL path: /status/{DEMO_PORTAL_RAW_TOKEN}")
        print("Demo credentials (password for all: demo):")
        print("  admin@demo.local          (admin)")
        print("  dispatcher@demo.local     (dispatcher)")
        print("  tech@demo.local           (technician)")
        print("  tech2@demo.local … tech5@demo.local")
        print("  other@demo.local          (other tenant — isolation tests)")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> None:
    seed()


if __name__ == "__main__":
    main()
