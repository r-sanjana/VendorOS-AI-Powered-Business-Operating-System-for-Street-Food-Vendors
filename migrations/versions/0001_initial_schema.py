"""Initial VendorOS schema - all tables

Revision ID: 0001_initial_schema
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
import uuid

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Enums ─────────────────────────────────────────────────────────────────

    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_type WHERE typname = 'userrole'
        ) THEN
            CREATE TYPE userrole AS ENUM (
                'ADMIN',
                'VENDOR',
                'EMPLOYEE',
                'CUSTOMER'
            );
        END IF;
    END $$;
    """)

    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_type WHERE typname = 'inventorycategory'
        ) THEN
            CREATE TYPE inventorycategory AS ENUM (
                'RICE',
                'OIL',
                'CHICKEN',
                'SPICES',
                'VEGETABLES',
                'PACKAGING',
                'BEVERAGES',
                'OTHER'
            );
        END IF;
    END $$;
    """)

    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_type WHERE typname = 'movementtype'
        ) THEN
            CREATE TYPE movementtype AS ENUM (
                'IN',
                'OUT',
                'WASTE',
                'ADJUST'
            );
        END IF;
    END $$;
    """)

    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_type WHERE typname = 'paymentmethod'
        ) THEN
            CREATE TYPE paymentmethod AS ENUM (
                'CASH',
                'UPI',
                'CARD'
            );
        END IF;
    END $$;
    """)

    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_type WHERE typname = 'expensecategory'
        ) THEN
            CREATE TYPE expensecategory AS ENUM (
                'RAW_MATERIALS',
                'GAS',
                'ELECTRICITY',
                'RENT',
                'TRANSPORTATION',
                'SALARY',
                'MAINTENANCE',
                'MARKETING',
                'OTHER'
            );
        END IF;
    END $$;
    """)

    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role",sa.Enum("ADMIN","VENDOR","EMPLOYEE","CUSTOMER",name="userrole",create_type=False,),nullable=False,),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── vendors ───────────────────────────────────────────────────────────────
    op.create_table(
        "vendors",
        sa.Column("id", sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column("business_name", sa.String(200), nullable=False),
        sa.Column("owner_name", sa.String(120), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("address", sa.String(400), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("fssai_number", sa.String(50), nullable=True),
        sa.Column("gst_number", sa.String(20), nullable=True),
        sa.Column("owner_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_vendors_id", "vendors", ["id"])
    op.create_index("ix_vendors_email", "vendors", ["email"])

    # ── inventory_items ───────────────────────────────────────────────────────
    op.create_table(
        "inventory_items",
        sa.Column("id", sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("category",sa.Enum("RICE","OIL","CHICKEN","SPICES","VEGETABLES","PACKAGING","BEVERAGES","OTHER",name="inventorycategory",create_type=False,),nullable=False,),
        sa.Column("unit", sa.String(30), nullable=False, server_default="kg"),
        sa.Column("current_stock", sa.Numeric(12, 3), nullable=False, server_default="0"),
        sa.Column("reorder_level", sa.Numeric(12, 3), nullable=False, server_default="0"),
        sa.Column("cost_per_unit", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("vendor_id", sa.UUID(), sa.ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_inventory_items_id", "inventory_items", ["id"])
    op.create_index("ix_inventory_items_vendor_id", "inventory_items", ["vendor_id"])

    # ── stock_movements ───────────────────────────────────────────────────────
    op.create_table(
        "stock_movements",
        sa.Column("id", sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column("item_id", sa.UUID(), sa.ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("movement_type",sa.Enum("IN","OUT","WASTE","ADJUST",name="movementtype",create_type=False,),nullable=False,),
        sa.Column("quantity", sa.Numeric(12, 3), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_stock_movements_id", "stock_movements", ["id"])
    op.create_index("ix_stock_movements_item_id", "stock_movements", ["item_id"])

    # ── sales ─────────────────────────────────────────────────────────────────
    op.create_table(
        "sales",
        sa.Column("id", sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column("sale_date", sa.Date(), nullable=False),
        sa.Column("payment_method",sa.Enum("CASH","UPI","CARD",name="paymentmethod",create_type=False,),nullable=False,),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("vendor_id", sa.UUID(), sa.ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_sales_id", "sales", ["id"])
    op.create_index("ix_sales_vendor_id", "sales", ["vendor_id"])
    op.create_index("ix_sales_sale_date", "sales", ["sale_date"])

    # ── sale_items ────────────────────────────────────────────────────────────
    op.create_table(
        "sale_items",
        sa.Column("id", sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column("sale_id", sa.UUID(), sa.ForeignKey("sales.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_name", sa.String(150), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_sale_items_id", "sale_items", ["id"])
    op.create_index("ix_sale_items_sale_id", "sale_items", ["sale_id"])

    # ── expenses ──────────────────────────────────────────────────────────────
    op.create_table(
        "expenses",
        sa.Column("id", sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column("expense_date", sa.Date(), nullable=False),
        sa.Column("category",sa.Enum("RAW_MATERIALS","GAS","ELECTRICITY","RENT","TRANSPORTATION","SALARY","MAINTENANCE","MARKETING","OTHER",name="expensecategory",create_type=False,),nullable=False,),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("receipt_url", sa.String(512), nullable=True),
        sa.Column("vendor_id", sa.UUID(), sa.ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_expenses_id", "expenses", ["id"])
    op.create_index("ix_expenses_vendor_id", "expenses", ["vendor_id"])
    op.create_index("ix_expenses_expense_date", "expenses", ["expense_date"])


def downgrade() -> None:
    op.drop_table("expenses")
    op.drop_table("sale_items")
    op.drop_table("sales")
    op.drop_table("stock_movements")
    op.drop_table("inventory_items")
    op.drop_table("vendors")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS expensecategory")
    op.execute("DROP TYPE IF EXISTS paymentmethod")
    op.execute("DROP TYPE IF EXISTS movementtype")
    op.execute("DROP TYPE IF EXISTS inventorycategory")
    op.execute("DROP TYPE IF EXISTS userrole")