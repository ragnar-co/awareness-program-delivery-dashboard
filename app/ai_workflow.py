"""Bonus AI workflow: draft a client-facing status update.

Calls the company-provided AI gateway (OpenRouter — OpenAI-compatible chat
completions API) using AI_API_KEY / AI_BASE_URL / AI_MODEL. The draft is
grounded ONLY in the rows pulled for the selected client — the model is
given the already-separated pending/accepted/overdue lists so it cannot
claim a pending-acceptance item as "done".
"""
import os

import httpx

from .analytics import accepted_items, overdue_items, pending_acceptance
from .db import session

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "anthropic/claude-sonnet-5"
MODEL = os.environ.get("AI_MODEL", DEFAULT_MODEL)


MAX_LISTED_ITEMS = 20


def _format_items(items: list[dict]) -> str:
    if not items:
        return "- (none)"
    shown = items[:MAX_LISTED_ITEMS]
    lines = [
        f"- [{i['deliverable_id']}] {i['deliverable_name']} (owner: {i['owner']}, due: {i['due_date']})"
        for i in shown
    ]
    remaining = len(items) - len(shown)
    if remaining > 0:
        lines.append(f"- ... และอีก {remaining} รายการ (รวมทั้งหมด {len(items)} รายการ)")
    return "\n".join(lines)


def build_prompt(client: str, as_of: str) -> dict:
    pending = pending_acceptance(as_of, client)
    accepted = accepted_items(as_of, client)
    overdue = overdue_items(as_of, client)

    prompt = f"""คุณคือผู้ดูแล Security Awareness Program กำลังร่างอัปเดตความคืบหน้าสำหรับลูกค้า "{client}" ณ วันที่อ้างอิง {as_of}

ข้อมูลงานที่ดึงจากระบบจริง ตัวเลขรวมในแต่ละหมวดถูกนับมาให้แล้ว ไม่ต้องนับเอง ห้ามเติมงานที่ไม่อยู่ในรายการ และห้ามเรียกงานที่ "รอตรวจรับ" ว่า "เสร็จสมบูรณ์" หรือ "ส่งมอบแล้ว" เด็ดขาด — ให้เรียกว่า "รอลูกค้าตรวจรับ" เท่านั้น

งานที่รอลูกค้าตรวจรับ (awaiting_acceptance) — รวม {len(pending)} รายการ:
{_format_items(pending)}

งานที่ลูกค้ารับรองแล้ว (accepted) — รวม {len(accepted)} รายการ:
{_format_items(accepted)}

งานที่เลยกำหนดส่ง และยังไม่ถูกรับรอง (overdue, ยังไม่ accepted) — รวม {len(overdue)} รายการ:
{_format_items(overdue)}

จงร่างอัปเดตสถานะงานสั้น กระชับ เป็นภาษาไทย แบ่งเป็น 3 หัวข้อตามลำดับนี้เท่านั้น:
1. งานที่รอตรวจรับ (ระบุว่ากำลังรอการยืนยันจากลูกค้า ไม่ใช่งานที่เสร็จแล้ว ใช้ตัวเลขรวมที่ให้มา ไม่ต้องนับเอง)
2. งานที่ลูกค้ารับรองแล้ว (สรุปจำนวนรวม ไม่ต้องไล่รายชื่อถ้ามีจำนวนมาก)
3. เรื่องที่ควรติดตาม (เน้นงานเลยกำหนดและผู้รับผิดชอบ ใช้ตัวเลขรวมที่ให้มา)

ถ้าหัวข้อใดไม่มีรายการ ให้เขียนว่า "ไม่มีรายการในรอบนี้" ห้ามสรุปภาพรวมว่า "งานทั้งหมดเสร็จสมบูรณ์" ถ้ายังมีรายการค้างอยู่ในข้อ 1 หรือ 3 ตอบให้กระชับ ไม่เกิน 300 คำ"""

    return {
        "prompt": prompt,
        "pending": pending,
        "accepted": accepted,
        "overdue": overdue,
    }


def generate_draft(client: str, as_of: str, db_path: str = None) -> dict:
    built = build_prompt(client, as_of)

    api_key = os.environ.get("AI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "AI_API_KEY is not set — the AI draft workflow needs the company-provided "
            "API key (OpenRouter) to generate updates."
        )

    base_url = os.environ.get("AI_BASE_URL", DEFAULT_BASE_URL)
    response = httpx.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": MODEL,
            "max_tokens": 1024,
            "reasoning": {"max_tokens": 0, "exclude": True},
            "messages": [{"role": "user", "content": built["prompt"]}],
        },
        timeout=60,
    )
    response.raise_for_status()
    choice = response.json()["choices"][0]
    content = choice["message"].get("content")
    if not content:
        raise RuntimeError(
            f"AI gateway returned no content (finish_reason={choice.get('finish_reason')!r}) — "
            "the draft was not generated or saved."
        )

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
