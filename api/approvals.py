"""
api/approvals.py
================
Manager approval/rejection endpoints for high-value held orders.
"""
from __future__ import annotations
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.auth import get_current_user
from db.supabase_client import get_client

router = APIRouter(prefix="/api", tags=["approvals"])


class ApprovalAction(BaseModel):
    action: str          # "approve" | "reject"
    reviewer_note: str = ""


@router.get("/approvals")
def list_pending_approvals(current_user: dict = Depends(get_current_user)):
    """List all orders with status='pending'."""
    client = get_client()
    resp   = (
        client.table("pending_approvals")
        .select("*")
        .eq("status", "pending")
        .order("created_at", desc=True)
        .execute()
    )
    return {"ok": True, "pending": resp.data or []}


@router.post("/approve/{approval_id}")
def action_approval(
    approval_id: int,
    body: ApprovalAction,
    current_user: dict = Depends(get_current_user),
):
    """
    Approve or reject a held order.

    Body:
        action       : "approve" or "reject"
        reviewer_note: Optional explanation.
    """
    if current_user.get("role") != "manager":
        raise HTTPException(status_code=403, detail="Only a manager can approve or reject held orders")

    if body.action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="action must be 'approve' or 'reject'")

    new_status = "approved" if body.action == "approve" else "rejected"
    client     = get_client()

    # Check it exists and is still pending
    check = (
        client.table("pending_approvals")
        .select("id,status")
        .eq("id", approval_id)
        .single()
        .execute()
    )
    if not check.data:
        raise HTTPException(status_code=404, detail=f"Approval {approval_id} not found")
    if check.data["status"] != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"Approval {approval_id} is already '{check.data['status']}'",
        )

    resp = (
        client.table("pending_approvals")
        .update({
            "status"       : new_status,
            "reviewed_at"  : datetime.now(timezone.utc).isoformat(),
            "reviewer_note": body.reviewer_note,
        })
        .eq("id", approval_id)
        .execute()
    )
    return {"ok": True, "approval_id": approval_id, "new_status": new_status, "data": resp.data}


@router.get("/decisions")
def list_decisions(limit: int = 50, current_user: dict = Depends(get_current_user)):
    """Retrieve recent ordering decisions for the dashboard."""
    client = get_client()
    resp   = (
        client.table("decisions")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return {"ok": True, "decisions": resp.data or []}
