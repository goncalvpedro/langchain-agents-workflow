"""
Agent Node Implementations
Each function represents an AI agent in the Genesis Pipeline
"""

import time
import json
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser

from src.state import GenesisState
from src.logger_config import logger, log_agent_execution


# Initialize the LLM (lazy initialization to avoid env issues at import)
def get_llm():
    """Get or create ChatOpenAI instance"""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        timeout=120
    )


async def agent_product_owner(state: GenesisState) -> Dict[str, Any]:
    """
    AGENT 1: Product Owner
    Transforms user idea into a comprehensive Product Requirements Document (PRD)
    
    Outputs: prd_content
    """
    start_time = time.time()
    agent_name = "product_owner"
    
    try:
        logger.info(f"Starting {agent_name} agent", extra={'agent': agent_name, 'status': 'running'})
        
        llm = get_llm()
        
        # System prompt for PRD generation
        system_prompt = """You are a Senior Product Owner with 15 years of experience at top tech companies.
          Your task is to transform a raw user idea into a comprehensive Product Requirements Document (PRD).

          The PRD must include:
          1. Executive Summary
          2. Problem Statement
          3. Target Users & Personas
          4. Core Features (MVP and Future)
          5. User Stories (at least 5)
          6. Success Metrics (KPIs)
          7. Technical Constraints
          8. Timeline Estimate

          Be specific, actionable, and realistic. Format the output in clear markdown."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"User Idea: {state['user_idea']}")
        ]
        
        # Invoke LLM
        response = await llm.ainvoke(messages)
        prd_content = response.content
        
        # Calculate metrics
        execution_time = time.time() - start_time
        tokens_used = response.response_metadata.get('token_usage', {}).get('total_tokens', 0)
        
        # Log execution
        log_agent_execution(agent_name, execution_time, tokens_used, 'success')
        
        return {
            "prd_content": prd_content,
            "messages": state["messages"] + [response]
        }
        
    except Exception as e:
        execution_time = time.time() - start_time
        log_agent_execution(agent_name, execution_time, 0, 'error', str(e))
        logger.error(f"Error in {agent_name}: {str(e)}", extra={'agent': agent_name})
        raise


async def agent_creative_director(state: GenesisState) -> Dict[str, Any]:
    """
    AGENT 2: Creative Director (Parallel Branch A)
    Creates brand identity including color schemes, typography, and visual prompts
    
    Outputs: brand_assets (JSON structure)
    """
    start_time = time.time()
    agent_name = "creative_director"
    
    try:
        logger.info(f"Starting {agent_name} agent", extra={'agent': agent_name, 'status': 'running'})
        
        llm = get_llm()
        
        system_prompt = """You are a Creative Director specializing in brand identity and visual design.
          Based on the user's idea and PRD, create a comprehensive brand guide.

          Return your response as a JSON object with this structure:
          {
            "brand_name": "suggested brand name",
            "tagline": "compelling tagline",
            "color_palette": {
              "primary": "#HEX",
              "secondary": "#HEX",
              "accent": "#HEX",
              "background": "#HEX",
              "text": "#HEX"
            },
            "typography": {
              "heading_font": "font name",
              "body_font": "font name"
            },
            "visual_style": "description of visual direction",
            "logo_prompt": "detailed prompt for AI logo generation",
            "ui_mockup_prompts": ["prompt1", "prompt2", "prompt3"]
          }

          Be creative but align with the product's purpose and target audience."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"User Idea: {state['user_idea']}\n\nPRD Summary: {state['prd_content'][:500]}...")
        ]
        
        # Use structured output for JSON
        llm_json = llm.bind(response_format={"type": "json_object"})
        response = await llm_json.ainvoke(messages)
        
        # Parse JSON
        content = response.content if isinstance(response.content, str) else str(response.content)
        brand_assets = json.loads(content)
        
        execution_time = time.time() - start_time
        tokens_used = response.response_metadata.get('token_usage', {}).get('total_tokens', 0)
        
        log_agent_execution(agent_name, execution_time, tokens_used, 'success')
        
        return {
            "brand_assets": brand_assets,
            "messages": state["messages"] + [response]
        }
        
    except Exception as e:
        execution_time = time.time() - start_time
        log_agent_execution(agent_name, execution_time, 0, 'error', str(e))
        logger.error(f"Error in {agent_name}: {str(e)}", extra={'agent': agent_name})
        raise


async def agent_solutions_architect(state: GenesisState) -> Dict[str, Any]:
    """
    AGENT 3: Solutions Architect (Parallel Branch B)
    Designs the technical architecture and file structure
    
    Outputs: architecture_map (JSON structure)
    """
    start_time = time.time()
    agent_name = "solutions_architect"
    
    try:
        logger.info(f"Starting {agent_name} agent", extra={'agent': agent_name, 'status': 'running'})
        
        llm = get_llm()
        
        system_prompt = """You are a Solutions Architect with expertise in modern software design patterns.
          Based on the PRD, design a complete technical architecture and file structure.

          Return your response as a JSON object with this structure:
          {
            "tech_stack": {
              "frontend": ["technology", "framework"],
              "backend": ["technology", "framework"],
              "database": "database choice",
              "infrastructure": ["services"]
            },
            "architecture_pattern": "description (e.g., microservices, monolith, JAMstack)",
            "file_structure": {
              "root/": {
                "src/": {
                  "components/": ["file1.jsx", "file2.jsx"],
                  "services/": ["api.js"],
                  "utils/": ["helper.js"]
                },
                "public/": ["index.html"],
                "tests/": ["test1.spec.js"]
              }
            },
            "key_modules": [
              {
                "name": "Authentication",
                "files": ["auth.js", "login.jsx"],
                "dependencies": ["jwt", "bcrypt"]
              }
            ],
            "api_endpoints": [
              {
                "method": "POST",
                "path": "/api/users",
                "description": "Create new user"
              }
            ]
          }

          Be practical and choose technologies appropriate for the project scale."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"User Idea: {state['user_idea']}\n\nPRD: {state['prd_content'][:800]}...")
        ]
        
        llm_json = llm.bind(response_format={"type": "json_object"})
        response = await llm_json.ainvoke(messages)
        
        content = response.content if isinstance(response.content, str) else str(response.content)
        architecture_map = json.loads(content)
        
        execution_time = time.time() - start_time
        tokens_used = response.response_metadata.get('token_usage', {}).get('total_tokens', 0)
        
        log_agent_execution(agent_name, execution_time, tokens_used, 'success')
        
        return {
            "architecture_map": architecture_map,
            "messages": state["messages"] + [response]
        }
        
    except Exception as e:
        execution_time = time.time() - start_time
        log_agent_execution(agent_name, execution_time, 0, 'error', str(e))
        logger.error(f"Error in {agent_name}: {str(e)}", extra={'agent': agent_name})
        raise


async def agent_lead_developer(state: GenesisState) -> Dict[str, Any]:
    """
    AGENT 4: Lead Developer (Synchronization Point)
    Generates actual source code based on architecture and brand assets
    
    Inputs: architecture_map, brand_assets
    Outputs: source_code (dict of filename -> code)
    """
    start_time = time.time()
    agent_name = "lead_developer"
    
    try:
        logger.info(f"Starting {agent_name} agent", extra={'agent': agent_name, 'status': 'running'})
        
        llm = get_llm()
        
        system_prompt = """You are a Lead Developer capable of writing production-quality code.
          Based on the architecture plan and brand assets, generate the core source code files.

          Return your response as a JSON object where keys are file paths and values are code content:
          {
            "src/App.jsx": "import React...",
            "src/components/Header.jsx": "const Header = () => {...}",
            "src/styles/theme.js": "export const theme = {...}",
            "backend/server.js": "const express = require('express')...",
            "README.md": "# Project Name\\n\\n## Setup..."
          }

          Generate at least 5-8 key files including:
          - Main application entry point
          - At least 2 reusable components
          - Styling/theme file (using brand colors)
          - API/backend setup
          - README with setup instructions
          - Configuration files

          Code must be:
          - Production-ready with error handling
          - Well-commented
          - Follow best practices
          - Use the brand colors from brand_assets"""

        # Prepare context
        context = f"""User Idea: {state['user_idea']}

          Architecture:
          {json.dumps(state['architecture_map'], indent=2)}

          Brand Assets:
          {json.dumps(state['brand_assets'], indent=2)}"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=context)
        ]
        
        llm_json = llm.bind(response_format={"type": "json_object"})
        response = await llm_json.ainvoke(messages)
        
        content = response.content if isinstance(response.content, str) else str(response.content)
        source_code = json.loads(content)
        
        execution_time = time.time() - start_time
        tokens_used = response.response_metadata.get('token_usage', {}).get('total_tokens', 0)
        
        log_agent_execution(agent_name, execution_time, tokens_used, 'success')
        
        return {
            "source_code": source_code,
            "messages": state["messages"] + [response]
        }
        
    except Exception as e:
        execution_time = time.time() - start_time
        log_agent_execution(agent_name, execution_time, 0, 'error', str(e))
        logger.error(f"Error in {agent_name}: {str(e)}", extra={'agent': agent_name})
        raise


async def agent_growth_hacker(state: GenesisState) -> Dict[str, Any]:
    """
    AGENT 5: Growth Hacker (Final Node)
    Creates comprehensive marketing and go-to-market strategy
    
    Inputs: prd_content, brand_assets, source_code
    Outputs: marketing_plan
    """
    start_time = time.time()
    agent_name = "growth_hacker"
    
    try:
        logger.info(f"Starting {agent_name} agent", extra={'agent': agent_name, 'status': 'running'})
        
        llm = get_llm()
        
        system_prompt = """You are a Growth Hacker with expertise in viral marketing and user acquisition.
          Based on the complete project (PRD, brand, and code), create a comprehensive Go-To-Market strategy.

          Include:
          1. Target Audience Segmentation
          2. Unique Value Proposition (UVP)
          3. Launch Strategy (phases)
          4. Marketing Channels (ranked by priority)
            - Content Marketing
            - Social Media Strategy
            - Paid Advertising
            - SEO Strategy
            - Community Building
          5. Growth Metrics & Goals
          6. Budget Allocation (percentages)
          7. First 90 Days Action Plan
          8. Viral Loop Mechanics
          9. Retention Strategies
          10. Sample Social Media Posts (5 examples)

          Be specific with tactics, timelines, and expected outcomes."""

        context = f"""User Idea: {state['user_idea']}

        Product Overview:
        {state['prd_content'][:500]}...

        Brand Identity:
        Brand Name: {state['brand_assets'].get('brand_name', 'N/A')}
        Tagline: {state['brand_assets'].get('tagline', 'N/A')}

        Project Files Generated: {len(state['source_code'])} files"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=context)
        ]
        
        response = await llm.ainvoke(messages)
        marketing_plan = response.content
        
        execution_time = time.time() - start_time
        tokens_used = response.response_metadata.get('token_usage', {}).get('total_tokens', 0)
        
        log_agent_execution(agent_name, execution_time, tokens_used, 'success')
        
        return {
            "marketing_plan": marketing_plan,
            "messages": state["messages"] + [response]
        }
        
    except Exception as e:
        execution_time = time.time() - start_time
        log_agent_execution(agent_name, execution_time, 0, 'error', str(e))
        logger.error(f"Error in {agent_name}: {str(e)}", extra={'agent': agent_name})
        raise


async def agent_onboarding_specialist(state: GenesisState) -> Dict[str, Any]:
    """
    AGENT 6: Onboarding Specialist (Final Node)
    Generates installation and setup guide for the generated project
    
    Inputs: source_code, architecture_map, marketing_plan
    Outputs: install_guide
    """
    start_time = time.time()
    agent_name = "onboarding_specialist"
    
    try:
        logger.info(f"Starting {agent_name} agent", extra={'agent': agent_name, 'status': 'running'})
        
        llm = get_llm()
        
        system_prompt = """You are an Onboarding Specialist with expertise in technical documentation and developer experience.
Based on the generated source code and architecture, create a comprehensive INSTALL_GUIDE.md that explains how to set up and run the generated project.

The guide must be specific to the actual architecture and tech stack chosen by the Solutions Architect. Include:

1. **Prerequisites**
   - Required software versions (Node.js, Python, Docker, etc.)
   - System requirements
   - Required accounts/API keys

2. **Installation Steps**
   - Step-by-step setup instructions
   - Package/dependency installation commands
   - Configuration file setup
   - Environment variable configuration

3. **Project Structure Overview**
   - Brief explanation of key directories
   - Important files and their purposes

4. **Running the Project**
   - Development server startup commands
   - Production build instructions
   - Database setup/migration commands (if applicable)
   - How to verify the installation worked

5. **Common Issues & Troubleshooting**
   - Typical setup problems and solutions
   - Debugging tips

6. **Next Steps**
   - Links to relevant documentation
   - How to start developing

Be extremely specific with commands, file paths, and configuration. Use the actual tech stack from the architecture_map.
Do NOT include instructions for running the Genesis Pipeline itself - only for the GENERATED project."""

        # Prepare context with architecture and source code info
        architecture_summary = json.dumps(state['architecture_map'], indent=2)
        
        # Get list of generated files
        source_files = list(state['source_code'].keys())
        source_files_summary = "\n".join([f"- {f}" for f in source_files[:20]])  # Show first 20 files
        
        # Get tech stack info
        tech_stack = state['architecture_map'].get('tech_stack', {})
        tech_stack_summary = json.dumps(tech_stack, indent=2)
        
        context = f"""User Idea: {state['user_idea']}

Architecture & Tech Stack:
{tech_stack_summary}

Full Architecture Map:
{architecture_summary}

Generated Source Files ({len(state['source_code'])} total):
{source_files_summary}
{"... (and more)" if len(source_files) > 20 else ""}

Key Files to Note:
- Look for package.json, requirements.txt, Dockerfile, or similar dependency files
- Check for README files or configuration examples
- Identify entry points (main.js, app.py, index.jsx, etc.)"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=context)
        ]
        
        response = await llm.ainvoke(messages)
        install_guide = response.content
        
        execution_time = time.time() - start_time
        tokens_used = response.response_metadata.get('token_usage', {}).get('total_tokens', 0)
        
        log_agent_execution(agent_name, execution_time, tokens_used, 'success')
        
        return {
            "install_guide": install_guide,
            "messages": state["messages"] + [response]
        }
        
    except Exception as e:
        execution_time = time.time() - start_time
        log_agent_execution(agent_name, execution_time, 0, 'error', str(e))
        logger.error(f"Error in {agent_name}: {str(e)}", extra={'agent': agent_name})
        raise