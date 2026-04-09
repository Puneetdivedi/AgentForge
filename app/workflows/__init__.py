"""Workflow/Cog loader for YAML-based workflow execution"""
import yaml
import os
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class WorkflowLoader:
    """Loader for workflow (cog) YAML files"""
    
    def __init__(self, workflows_dir: str = "config/workflows"):
        self.workflows_dir = workflows_dir
    
    def load_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Load a workflow from YAML"""
        filepath = os.path.join(self.workflows_dir, f"{workflow_id}.yaml")
        
        if not os.path.exists(filepath):
            logger.warning(f"Workflow file not found: {filepath}")
            return None
        
        try:
            with open(filepath, "r") as f:
                workflow = yaml.safe_load(f)
            
            logger.info(f"Loaded workflow: {workflow_id}")
            return workflow
        
        except Exception as e:
            logger.error(f"Failed to load workflow {workflow_id}: {e}")
            return None
    
    def load_all_workflows(self) -> Dict[str, Dict[str, Any]]:
        """Load all workflows from directory"""
        workflows = {}
        
        if not os.path.exists(self.workflows_dir):
            logger.warning(f"Workflows directory not found: {self.workflows_dir}")
            return workflows
        
        for filename in os.listdir(self.workflows_dir):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                workflow_id = os.path.splitext(filename)[0]
                workflow = self.load_workflow(workflow_id)
                
                if workflow:
                    workflows[workflow_id] = workflow
        
        return workflows
    
    async def execute_workflow(self,
                              workflow_id: str,
                              input_data: Dict[str, Any],
                              agent_registry) -> List[Dict[str, Any]]:
        """Execute a workflow"""
        workflow = self.load_workflow(workflow_id)
        
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        results = []
        current_output = input_data
        
        for step in workflow.get("steps", []):
            agent_id = step.get("agent")
            
            # Get agent
            agent = agent_registry.get_agent(agent_id)
            if not agent:
                logger.warning(f"Agent not found in workflow step: {agent_id}")
                continue
            
            # Execute agent
            from app.agents.base import AgentContext
            context = AgentContext(
                user_id=input_data.get("user_id", "unknown"),
                session_id=input_data.get("session_id", "unknown")
            )
            
            response = await agent.process(
                input_data.get("input", ""),
                context
            )
            
            results.append({
                "agent": agent_id,
                "output": response
            })
            
            current_output = response
        
        return results
