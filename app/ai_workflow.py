"""Bonus AI workflow: draft a client-facing status update.

Calls the Claude API (Messages API) using the company-provided
ANTHROPIC_API_KEY / ANTHROPIC_BASE_URL. The draft is grounded ONLY in the
rows pulled for the selected client — the model is given the already
-separated pending/accepted/overdue lists so it cannot claim a
pending-acceptance item as "done".
"""
import os

from .analytics import accepted_items, overdue_items, pending_acceptance
from .db import session

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")


def _format_items(items: list[dict]) -> str:
    if not items:
        return "- (none)"
    return "\n".join(
        f"- [{i['deliverable_id']}] {i['deliverable_name']} (owner: {i['owner']}, due: {i['due_date']})"
        for i in items
    )


def build_prompt(client: str, as_of: str) -> dict:
    pending = pending_acceptance(as_of, client)
    accepted = accepted_items(as_of, client)
    overdue = overdue_items(as_of, client)

    prompt = f"""คุณคือผู้ดูแล Security Awareness Program กำลังร่างอัปเดตความคืบหน้าสำหรับลูกค้า "{client}" ณ วันที่อ้างอิง {as_of}

ข้อมูลงานที่ดึงจากระบบจริง ห้ามเติมงานที่ไม่อยู่ในรายการ และห้ามเรียกงานที่ "รอตรวจรับ" ว่า "เสร็จสมบูรณ์" หรือ "ส่งมอบแล้ว" เด็ดขาด — ให้เรียกว่า "รอลูกค้าตรวจรับ" เท่านั้น

งานที่รอลูกค้าตรวจรับ (awaiting_acceptance):
{_format_items(pending)}

งานที่ลูกค้ารับรองแล้ว (accepted):
{_format_items(accepted)}

งานที่เลยกำหนดส่ง และยังไม่ถูกรับรอง (overdue, ยังไม่ accepted):
{_format_items(overdue)}

จงร่างอัปเดตสถานะงานสั้น กระชับ เป็นภาษาไทย แบ่งเป็น 3 หัวข้อตามลำดับนี้เท่านั้น:
1. งานที่รอตรวจรับ (ระบุว่ากำลังรอการยืนยันจากลูกค้า ไม่ใช่งานที่เสร็จแล้ว)
2. งานที่ลูกค้ารับรองแล้ว
3. เรื่องที่ควรติดตาม (เน้นงานเลยกำหนดและผู้รับผิดชอบ)

ถ้าหัวข้อใดไม่มีรายการ ให้เขียนว่า "ไม่มีรายการในรอบนี้" ห้ามสรุปภาพรวมว่า "งานทั้งหมดเสร็จสมบูรณ์" ถ้ายังมีรายการค้างอยู่ในข้อ 1 หรือ 3"""

    return {
        "prompt": prompt,
        "pending": pending,
        "accepted": accepted,
        "overdue": overdue,
    }


def generate_draft(client: str, as_of: str, db_path: str = None) -> dict:
    built = build_prompt(client, as_of)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set — the AI draft workflow needs the company-provided "
            "Claude API key to generate updates."
        )

    import anthropic

    client_sdk = anthropic.Anthropic(api_key=api_key, base_url=os.environ.get("ANTHROPIC_BASE_URL"))
    response = client_sdk.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": built["prompt"]}],
    )
    content = "".join(block.text for block in response.content if block.type == "text")

    with session(db_path) as conn:
        conn.execute(
            "INSERT INTO ai_drafts (client_name, as_of, content, model) VALUES (?, ?, ?, ?)",
            (client, as_of, content, MODEL),
        )

    return {
        "client": client,
        "as_of": as_of,
        "content": content,
        "model": MODEL,
        "counts": {
            "pending_acceptance": len(built["pending"]),
            "accepted": len(built["accepted"]),
            "overdue": len(built["overdue"]),
        },
    }


def list_drafts(client: str | None = None, db_path: str = None, limit: int = 20) -> list[dict]:
    with session(db_path) as conn:
        if client:
            rows = conn.execute(
                "SELECT * FROM ai_drafts WHERE client_name = ? ORDER BY created_at DESC LIMIT ?",
                (client, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM ai_drafts ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
    return [dict(r) for r in rows]
