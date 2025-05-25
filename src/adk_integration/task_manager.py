"""
Task Manager - Handles task creation and coordination between agents
This manages the workflow of tasks through the multi-agent system
"""
from typing import Dict, List, Any, Optional
from google.adk.agents import Task, TaskResult
import uuid
import json
from datetime import datetime

class EnergyTaskManager:
    """Manages tasks and coordination between energy optimization agents"""
    
    def __init__(self):
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, TaskResult] = {}
        
    def create_bill_analysis_task(self, bill_data: Dict[str, Any]) -> Task:
        """Create a task for bill analysis"""
        task = Task(
            id=str(uuid.uuid4()),
            type='bill_analysis',
            description='Analyze uploaded energy bill and extract usage patterns',
            input_data=bill_data,
            required_capabilities=['pdf_parsing', 'data_extraction'],
            priority='high',
            created_at=datetime.now()
        )
        
        self.active_tasks[task.id] = task
        return task
    
    def create_market_research_task(self, analysis_result: Dict[str, Any]) -> Task:
        """Create a task for market research based on bill analysis"""
        task = Task(
            id=str(uuid.uuid4()),
            type='market_research',
            description='Find better energy plans based on usage profile',
            input_data={
                'usage_profile': analysis_result.get('usage_profile'),
                'location': analysis_result.get('location'),
                'current_plan': analysis_result.get('current_plan')
            },
            required_capabilities=['api_integration', 'plan_comparison'],
            priority='medium',
            created_at=datetime.now(),
            depends_on=[analysis_result.get('task_id')]
        )
        
        self.active_tasks[task.id] = task
        return task
    
    def create_savings_calculation_task(self, market_data: Dict[str, Any], 
                                      analysis_data: Dict[str, Any]) -> Task:
        """Create a task for calculating potential savings"""
        task = Task(
            id=str(uuid.uuid4()),
            type='savings_calculation',
            description='Calculate potential savings from plan switches',
            input_data={
                'available_plans': market_data.get('plans'),
                'current_usage': analysis_data.get('usage_profile'),
                'current_costs': analysis_data.get('cost_breakdown')
            },
            required_capabilities=['financial_modeling', 'projection'],
            priority='high',
            created_at=datetime.now()
        )
        
        self.active_tasks[task.id] = task
        return task
    
    def create_comprehensive_optimization_workflow(self, bill_data: Dict[str, Any]) -> List[Task]:
        """Create a complete workflow of tasks for energy optimization"""
        
        # Task 1: Analyze the bill
        analysis_task = self.create_bill_analysis_task(bill_data)
        
        # Task 2: Research market (depends on analysis)
        market_task = Task(
            id=str(uuid.uuid4()),
            type='market_research',
            description='Research energy market for better plans',
            input_data={'depends_on_analysis': True},
            required_capabilities=['api_integration'],
            priority='medium',
            depends_on=[analysis_task.id]
        )
        
        # Task 3: Calculate savings (depends on both previous tasks)
        savings_task = Task(
            id=str(uuid.uuid4()),
            type='savings_calculation',
            description='Calculate potential savings',
            input_data={'depends_on_market_and_analysis': True},
            required_capabilities=['financial_modeling'],
            priority='high',
            depends_on=[analysis_task.id, market_task.id]
        )
        
        # Task 4: Find rebates (can run in parallel with market research)
        rebate_task = Task(
            id=str(uuid.uuid4()),
            type='rebate_search',
            description='Find applicable rebates and incentives',
            input_data={'depends_on_analysis': True},
            required_capabilities=['rebate_search'],
            priority='low',
            depends_on=[analysis_task.id]
        )
        
        # Task 5: Optimize usage (depends on analysis)
        optimization_task = Task(
            id=str(uuid.uuid4()),
            type='usage_optimization',
            description='Provide usage optimization recommendations',
            input_data={'depends_on_analysis': True},
            required_capabilities=['pattern_analysis', 'optimization'],
            priority='medium',
            depends_on=[analysis_task.id]
        )
        
        tasks = [analysis_task, market_task, savings_task, rebate_task, optimization_task]
        
        for task in tasks:
            self.active_tasks[task.id] = task
            
        return tasks
    
    def complete_task(self, task_id: str, result: TaskResult):
        """Mark a task as completed and store the result"""
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
            self.completed_tasks[task_id] = result
    
    def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Get the result of a completed task"""
        return self.completed_tasks.get(task_id)