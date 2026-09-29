import uuid
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import require_role
from app.modules.purchase_orders.schemas import PurchaseOrderCreate, PurchaseOrderOut, ReceiveRequest
from app.modules.purchase_orders.service import PurchaseOrderService
router=APIRouter(prefix="/purchase-orders",tags=["purchase-orders"])
WRITE=("ADMIN","PROCUREMENT_MANAGER"); READ=("ADMIN","INVENTORY_MANAGER","PROCUREMENT_MANAGER"); APPROVE=("ADMIN",)
@router.post("/",response_model=PurchaseOrderOut,status_code=201)
def create_po(payload:PurchaseOrderCreate,request:Request,db:Session=Depends(get_db),current=Depends(require_role(*WRITE))): return PurchaseOrderService(db).create_po(payload,current.id,request.headers.get("authorization",""))
@router.get("/",response_model=list[PurchaseOrderOut])
def list_pos(skip:int=0,limit:int=50,db:Session=Depends(get_db),current=Depends(require_role(*READ))): return PurchaseOrderService(db).list_pos(skip,limit)
@router.get("/{po_id}",response_model=PurchaseOrderOut)
def get_po(po_id:uuid.UUID,db:Session=Depends(get_db),current=Depends(require_role(*READ))): return PurchaseOrderService(db).get_po(po_id)
@router.post("/{po_id}/submit",response_model=PurchaseOrderOut)
def submit_po(po_id:uuid.UUID,db:Session=Depends(get_db),current=Depends(require_role(*WRITE))): return PurchaseOrderService(db).submit(po_id)
@router.post("/{po_id}/approve",response_model=PurchaseOrderOut)
def approve_po(po_id:uuid.UUID,db:Session=Depends(get_db),current=Depends(require_role(*APPROVE))): return PurchaseOrderService(db).approve(po_id,current.id)
@router.post("/{po_id}/mark-ordered",response_model=PurchaseOrderOut)
def mark_ordered(po_id:uuid.UUID,db:Session=Depends(get_db),current=Depends(require_role(*WRITE))): return PurchaseOrderService(db).mark_ordered(po_id)
@router.post("/{po_id}/close",response_model=PurchaseOrderOut)
def close_po(po_id:uuid.UUID,db:Session=Depends(get_db),current=Depends(require_role(*WRITE))): return PurchaseOrderService(db).close(po_id)
@router.post("/{po_id}/receive",response_model=PurchaseOrderOut)
def receive_po(po_id:uuid.UUID,payload:ReceiveRequest,db:Session=Depends(get_db),current=Depends(require_role(*WRITE))): return PurchaseOrderService(db).receive(po_id,payload,current.id)
