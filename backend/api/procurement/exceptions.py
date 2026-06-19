"""
Custom exceptions for procurement module.
"""

from backend.core.exceptions.base import MIOSException


class ProcurementException(MIOSException):
    """Base exception for procurement module."""
    pass


class RequisitionNotFoundException(ProcurementException):
    """Raised when purchase requisition is not found."""
    
    def __init__(self, requisition_id: int):
        self.requisition_id = requisition_id
        super().__init__(
            message=f"Purchase requisition {requisition_id} not found",
            status_code=404
        )


class RequisitionInvalidStatusTransition(ProcurementException):
    """Raised when requisition status transition is invalid."""
    
    def __init__(self, current_status: str, target_status: str):
        self.current_status = current_status
        self.target_status = target_status
        super().__init__(
            message=f"Cannot transition requisition from {current_status} to {target_status}",
            status_code=400
        )


class RequisitionAlreadyConverted(ProcurementException):
    """Raised when requisition already has a PO."""
    
    def __init__(self, requisition_id: int, po_number: str):
        self.requisition_id = requisition_id
        self.po_number = po_number
        super().__init__(
            message=f"Requisition {requisition_id} already converted to PO {po_number}",
            status_code=400
        )


class PurchaseOrderNotFoundException(ProcurementException):
    """Raised when purchase order is not found."""
    
    def __init__(self, po_id: int):
        self.po_id = po_id
        super().__init__(
            message=f"Purchase order {po_id} not found",
            status_code=404
        )


class PurchaseOrderInvalidStatusTransition(ProcurementException):
    """Raised when PO status transition is invalid."""
    
    def __init__(self, current_status: str, target_status: str):
        self.current_status = current_status
        self.target_status = target_status
        super().__init__(
            message=f"Cannot transition PO from {current_status} to {target_status}",
            status_code=400
        )


class PurchaseOrderFinancialDataImmutable(ProcurementException):
    """Raised when attempting to modify financial data on approved PO."""
    
    def __init__(self, po_id: int):
        self.po_id = po_id
        super().__init__(
            message=f"Cannot modify financial data on approved PO {po_id}",
            status_code=403
        )


class GoodsReceiptNotFoundException(ProcurementException):
    """Raised when goods receipt is not found."""
    
    def __init__(self, receipt_id: int):
        self.receipt_id = receipt_id
        super().__init__(
            message=f"Goods receipt {receipt_id} not found",
            status_code=404
        )


class DuplicateRequisitionNumber(ProcurementException):
    """Raised when requisition number already exists."""
    
    def __init__(self, requisition_number: str):
        self.requisition_number = requisition_number
        super().__init__(
            message=f"Requisition number {requisition_number} already exists",
            status_code=409
        )


class DuplicatePONumber(ProcurementException):
    """Raised when PO number already exists."""
    
    def __init__(self, po_number: str):
        self.po_number = po_number
        super().__init__(
            message=f"PO number {po_number} already exists",
            status_code=409
        )


class VendorNotFoundException(ProcurementException):
    """Raised when vendor is not found."""
    
    def __init__(self, vendor_id: int):
        self.vendor_id = vendor_id
        super().__init__(
            message=f"Vendor {vendor_id} not found",
            status_code=404
        )


class InsufficientApprovalAuthority(ProcurementException):
    """Raised when user lacks approval authority for amount."""
    
    def __init__(self, amount: float, user_limit: float):
        self.amount = amount
        self.user_limit = user_limit
        super().__init__(
            message=f"Amount {amount} exceeds your approval limit of {user_limit}",
            status_code=403
        )
