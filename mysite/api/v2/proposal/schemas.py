from pydantic import BaseModel
from typing import Optional


class ProposalRequestModel(BaseModel):
    """Pydantic model for proposal creation request."""
    estimate_id: int
    additional_info: Optional[str] = None  # Adjust based on actual request data


class ProposalResponseModel(BaseModel):
    """Pydantic model for proposal creation response."""
    proposal_id: int
    pdf_path: str
    message: str
