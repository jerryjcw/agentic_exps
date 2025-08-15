from pydantic import BaseModel
from typing import Dict, Any, Optional


class WorkflowRequest(BaseModel):
    """Request model for running a flexible workflow."""
    job_config: Dict[str, Any]
    agent_config: Dict[str, Any]
    template_config: Dict[str, Any]


class WorkflowResponse(BaseModel):
    """Response model for workflow execution results."""
    status: str
    output_file: Optional[str] = None
    json_file: Optional[str] = None
    events_generated: Optional[int] = None
    response_length: Optional[int] = None
    execution_results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None