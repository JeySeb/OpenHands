"""
TaskConvAgent - Specialized agent for Task-Based Conversational Systems
"""

from openhands.agenthub.taskconv_agent.taskconv_agent import TaskConvAgent
from openhands.controller.agent import Agent

Agent.register('TaskConvAgent', TaskConvAgent)