import logging
import sys
import os
import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.flexible_agents import main_async_with_config
from api.models import WorkflowRequest, WorkflowResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Flexible Agent API",
    description="API for running flexible agent workflows",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/workflow/run", response_model=WorkflowResponse)
async def run_workflow(request: WorkflowRequest):
    """
    Run a flexible agent workflow with the provided configurations.
    
    Args:
        request: WorkflowRequest containing job_config, agent_config, and template_config
        
    Returns:
        WorkflowResponse with execution results or error information
    """
    try:
        logger.info("Starting workflow execution")
        
        # Convert JSON objects to YAML strings for the main_async_with_config function
        job_config_yaml = yaml.dump(request.job_config, default_flow_style=False)
        agent_config_yaml = yaml.dump(request.agent_config, default_flow_style=False)
        template_config_yaml = yaml.dump(request.template_config, default_flow_style=False)
        
        # Call the main async function with the provided configurations
        exit_code, results = await main_async_with_config(
            job_config_content=job_config_yaml,
            agent_config_content=agent_config_yaml,
            template_config_content=template_config_yaml
        )
        
        if exit_code == 0:
            # Success case - return the actual results
            return WorkflowResponse(
                status="completed",
                output_file=results.get("output_file"),
                json_file=results.get("json_file"),
                events_generated=results.get("events_generated"),
                response_length=results.get("response_length"),
                execution_results=results.get("execution_results"),
                error_message=None
            )
        else:
            # Error case - results dictionary contains error information
            return WorkflowResponse(
                status="failed",
                error_message=results.get("error_message", "Workflow execution failed"),
                execution_results=results if isinstance(results, dict) else None
            )
            
    except Exception as e:
        logger.error(f"Error running workflow: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error running workflow: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Flexible Agent API is running"}


@app.get("/")
async def root():
    """Root endpoint with basic information."""
    return {
        "message": "Flexible Agent API",
        "version": "1.0.0",
        "endpoints": {
            "run_workflow": "/workflow/run",
            "health": "/health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)