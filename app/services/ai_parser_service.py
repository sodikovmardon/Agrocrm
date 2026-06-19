import json
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.provider import llm_structured_output
from app.core.redis import (
    delete_parsed_entry,
    get_parsed_entry,
    store_parsed_entry,
)
from app.repositories.farm_repo import FarmRepository
from app.repositories.finance_repo import FinanceRepository
from app.repositories.inventory_repo import InventoryRepository
from app.repositories.production_repo import ProductionRepository


# Maps AI inventory categories to finance expense categories.
_PURCHASE_EXPENSE_CATEGORY = {
    "feed": "feed",
    "medicine": "medicine",
    "vaccine": "vaccine",
}


PARSING_SYSTEM_PROMPT = """You are an AI assistant for a smart farm management system called AgroSmart AI.
Your task is to parse the farmer's natural language text and extract structured operations.

Available operation types:
1. "production" - Record production (milk, eggs, weight gain, meat). Requires record_type, quantity, unit.
2. "consumption" - Record consumption of feed, medicine, etc. Requires item_name, quantity, unit.
3. "purchase" - Record purchase of inventory items. Requires item_name, item_category, quantity, unit, amount.
4. "expense" - Record other expenses. Requires amount, notes.

For production:
- record_type must be one of: milk, egg, weight_gain, meat
- unit must be: liter, kg, piece, gram

For consumption/purchase:
- item_category must be one of: feed, medicine, vaccine, product

Return a JSON object with:
{
  "operations": [
    {
      "operation_type": "production|consumption|purchase|expense",
      "record_type": "...",  // required for production
      "animal_id": null,     // if animal mentioned, provide UUID or null
      "group_id": null,      // if group mentioned, provide UUID or null
      "item_name": "...",    // for consumption/purchase
      "item_category": "...", // for consumption/purchase
      "quantity": 0.0,
      "unit": "...",
      "amount": 0.0,         // for purchase/expense
      "notes": "..."
    }
  ],
  "warnings": [
    "Warning message if something is unclear"
  ]
}

If you cannot parse the text, set operations to empty array and add a warning."""


async def parse_farmer_text(text: str, session: AsyncSession, farm_id: Optional[str] = None) -> Dict[str, Any]:
    system_prompt = PARSING_SYSTEM_PROMPT
    if farm_id:
        farm_repo = FarmRepository(session)
        farm = await farm_repo.get(uuid.UUID(farm_id))
        if farm:
            system_prompt += f"\nFarm context: {farm.name} in {farm.region}, {farm.district}."

    result = await llm_structured_output(
        system_prompt=system_prompt,
        user_prompt=text,
    )

    try:
        parsed = json.loads(result)
    except (json.JSONDecodeError, TypeError) as e:
        return {
            "operations": [],
            "warnings": [f"Failed to parse AI response: {str(e)}. Please try rephrasing your input."],
        }

    operations = parsed.get("operations", [])
    warnings = parsed.get("warnings", [])

    if not operations:
        warnings.append("No operations could be extracted from your text. Please be more specific.")

    entry_id = str(uuid.uuid4())
    await store_parsed_entry(entry_id, operations, warnings)

    return {
        "entry_id": entry_id,
        "operations": operations,
        "warnings": warnings,
    }


async def commit_parsed_entry(
    entry_id: str,
    operations: List[Dict[str, Any]],
    user_id: uuid.UUID,
    session: AsyncSession,
) -> Dict[str, Any]:
    stored_entry = await get_parsed_entry(entry_id)
    if stored_entry is None:
        stored_operations = operations
    else:
        stored_operations = stored_entry.get("operations", [])

    if not stored_operations:
        stored_operations = operations

    committed_count = 0
    errors: List[str] = []

    farm_repo = FarmRepository(session)
    prod_repo = ProductionRepository(session)
    inv_repo = InventoryRepository(session)
    finance_repo = FinanceRepository(session)

    farm_id = None

    for op in stored_operations:
        try:
            op_type = op.get("operation_type")
            if op_type == "production":
                if farm_id is None:
                    farm_id = await _resolve_farm_id(op, user_id, session)
                if farm_id is None:
                    errors.append("Could not determine farm for production record.")
                    continue

                animal_id = None
                if op.get("animal_id"):
                    animal_id = uuid.UUID(op["animal_id"])
                group_id = None
                if op.get("group_id"):
                    group_id = uuid.UUID(op["group_id"])

                from app.schemas.production import ProductionRecordCreate
                from datetime import datetime, timezone

                record_data = ProductionRecordCreate(
                    animal_id=animal_id,
                    group_id=group_id,
                    type=op.get("record_type", "milk"),
                    quantity=op.get("quantity", 0),
                    unit=op.get("unit", "liter"),
                    notes=op.get("notes"),
                    recorded_at=datetime.now(timezone.utc),
                )
                await prod_repo.create(record_data, farm_id=farm_id, created_by=user_id)
                committed_count += 1

            elif op_type == "consumption":
                if farm_id is None:
                    farm_id = await _resolve_farm_id(op, user_id, session)
                if farm_id is None:
                    errors.append("Could not determine farm for consumption.")
                    continue

                item_name = op.get("item_name")
                quantity = op.get("quantity", 0)
                if not item_name:
                    errors.append("Item name is required for consumption.")
                    continue

                item = await inv_repo.get_item_by_name_and_farm(farm_id, item_name)
                if item is None:
                    errors.append(f"Inventory item '{item_name}' not found.")
                    continue

                from decimal import Decimal
                await inv_repo.reduce_quantity(item.id, Decimal(str(quantity)))
                committed_count += 1

            elif op_type == "purchase":
                if farm_id is None:
                    farm_id = await _resolve_farm_id(op, user_id, session)
                if farm_id is None:
                    errors.append("Could not determine farm for purchase.")
                    continue

                from app.schemas.inventory import InventoryItemCreate
                from decimal import Decimal

                item_category = op.get("item_category", "product")
                amount = op.get("amount")
                purchase_data = InventoryItemCreate(
                    name=op.get("item_name", "Unknown Item"),
                    category=item_category,
                    unit=op.get("unit", "piece"),
                    current_quantity=Decimal(str(op.get("quantity", 0))),
                    average_cost=Decimal(str(amount)) / Decimal(str(op.get("quantity", 1))) if op.get("quantity") and amount else None,
                )
                await inv_repo.create(purchase_data, farm_id=farm_id)

                # Record the money spent on the purchase as a finance expense.
                if amount:
                    await _record_expense(
                        finance_repo=finance_repo,
                        farm_id=farm_id,
                        user_id=user_id,
                        amount=Decimal(str(amount)),
                        category=_PURCHASE_EXPENSE_CATEGORY.get(item_category, "other_expense"),
                        description=op.get("notes") or f"Sotib olindi: {op.get('item_name', '')}".strip(),
                    )
                committed_count += 1

            elif op_type == "expense":
                from decimal import Decimal

                if farm_id is None:
                    farm_id = await _resolve_farm_id(op, user_id, session)
                if farm_id is None:
                    errors.append("Could not determine farm for expense.")
                    continue

                amount = op.get("amount")
                if not amount:
                    errors.append("Amount is required for expense.")
                    continue

                await _record_expense(
                    finance_repo=finance_repo,
                    farm_id=farm_id,
                    user_id=user_id,
                    amount=Decimal(str(amount)),
                    category="other_expense",
                    description=op.get("notes"),
                )
                committed_count += 1

        except Exception as e:
            errors.append(f"Operation failed: {str(e)}")

    await delete_parsed_entry(entry_id)

    return {
        "success": len(errors) == 0,
        "committed_count": committed_count,
        "errors": errors,
    }


async def _resolve_farm_id(op: Dict[str, Any], user_id: uuid.UUID, session: AsyncSession) -> Optional[uuid.UUID]:
    from app.models.farm import Farm
    from sqlalchemy import select

    stmt = select(Farm.id).where(Farm.owner_id == user_id).limit(1)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def _record_expense(
    finance_repo: FinanceRepository,
    farm_id: uuid.UUID,
    user_id: uuid.UUID,
    amount: "Decimal",
    category: str,
    description: Optional[str],
) -> None:
    from datetime import datetime, timezone

    from app.schemas.finance import FinanceTransactionCreate

    tx = FinanceTransactionCreate(
        type="expense",
        category=category,
        amount=amount,
        description=description,
        recorded_at=datetime.now(timezone.utc),
    )
    await finance_repo.create(tx, farm_id=farm_id, created_by=user_id)
