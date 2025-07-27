from typing import Dict, List, Optional, Any, Union, TypedDict
import json
import asyncio
from datetime import datetime

# LangChain and LangGraph imports
try:
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
    from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
    from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
    from langchain_core.runnables import RunnablePassthrough, RunnableLambda
    from langchain_ollama import ChatOllama
    from langgraph.graph import StateGraph, START, END
    from langgraph.checkpoint.memory import MemorySaver
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("LangChain ecosystem not available. Install with: pip install langchain langchain-ollama langgraph")

# Fallback imports
try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None

# Optional fallback imports
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    Anthropic = None

from app.core.config import get_settings
from app.utils.helpers import chunk_text, mask_sensitive_data


class CodeReviewState(TypedDict):
    """State for the code review workflow graph."""
    diff_content: str
    file_content: Optional[str]
    filename: Optional[str]
    context: Dict[str, Any]
    analysis_type: str
    focus_areas: Optional[List[str]]
    initial_analysis: Optional[Dict[str, Any]]
    security_analysis: Optional[Dict[str, Any]]
    performance_analysis: Optional[Dict[str, Any]]
    quality_analysis: Optional[Dict[str, Any]]
    final_report: Optional[Dict[str, Any]]
    errors: List[str]


class LangChainLLMService:
    def __init__(self):
        """Initialize LangChain LLM service with configured providers."""
        self.settings = get_settings()
        self.logger = logger
        
        # Initialize LangChain models
        self.ollama_model = None
        self.openai_model = None
        self.anthropic_model = None
        
        # Initialize graph workflow
        self.workflow = None
        self.memory = MemorySaver() if LANGCHAIN_AVAILABLE else None
        
        if LANGCHAIN_AVAILABLE:
            self._initialize_models()
            self._build_workflow()
        else:
            self.logger.error("LangChain not available - falling back to basic implementation")
    
    def _initialize_models(self):
        """Initialize LangChain model instances."""
        try:
            # Initialize Ollama model (primary)
            if hasattr(self.settings, 'OLLAMA_BASE_URL'):
                self.ollama_model = ChatOllama(
                    base_url=self.settings.OLLAMA_BASE_URL,
                    model=self.settings.OLLAMA_MODEL,
                    temperature=0.1,
                    timeout=120,
                )
                self.logger.info(f"Ollama model initialized: {self.settings.OLLAMA_MODEL}")
            
            # Initialize fallback models
            if OPENAI_AVAILABLE and hasattr(self.settings, 'OPENAI_API_KEY') and self.settings.OPENAI_API_KEY:
                from langchain_openai import ChatOpenAI
                self.openai_model = ChatOpenAI(
                    api_key=self.settings.OPENAI_API_KEY,
                    model="gpt-4o-mini",
                    temperature=0.1
                )
                self.logger.info("OpenAI model initialized")
            
            if ANTHROPIC_AVAILABLE and hasattr(self.settings, 'ANTHROPIC_API_KEY') and self.settings.ANTHROPIC_API_KEY:
                from langchain_anthropic import ChatAnthropic
                self.anthropic_model = ChatAnthropic(
                    api_key=self.settings.ANTHROPIC_API_KEY,
                    model="claude-3-haiku-20240307",
                    temperature=0.1
                )
                self.logger.info("Anthropic model initialized")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize models: {e}")
    
    def _get_primary_model(self):
        """Get the primary model based on configuration."""
        if self.settings.DEFAULT_LLM_PROVIDER == "ollama" and self.ollama_model:
            return self.ollama_model
        elif self.settings.DEFAULT_LLM_PROVIDER == "openai" and self.openai_model:
            return self.openai_model
        elif self.settings.DEFAULT_LLM_PROVIDER == "anthropic" and self.anthropic_model:
            return self.anthropic_model
        
        # Fallback order
        return self.ollama_model or self.openai_model or self.anthropic_model
    
    def _build_workflow(self):
        """Build the LangGraph workflow for code analysis."""
        if not LANGCHAIN_AVAILABLE:
            return
        
        # Create the state graph
        workflow = StateGraph(CodeReviewState)
        
        # Add nodes
        workflow.add_node("initial_analysis", self._initial_analysis_node)
        workflow.add_node("security_analysis", self._security_analysis_node)
        workflow.add_node("performance_analysis", self._performance_analysis_node)
        workflow.add_node("quality_analysis", self._quality_analysis_node)
        workflow.add_node("final_report", self._final_report_node)
        
        # Add edges
        workflow.add_edge(START, "initial_analysis")
        workflow.add_edge("initial_analysis", "security_analysis")
        workflow.add_edge("security_analysis", "performance_analysis")
        workflow.add_edge("performance_analysis", "quality_analysis")
        workflow.add_edge("quality_analysis", "final_report")
        workflow.add_edge("final_report", END)
        
        # Compile the workflow
        self.workflow = workflow.compile(checkpointer=self.memory)
        self.logger.info("LangGraph workflow compiled successfully")
    
    async def _initial_analysis_node(self, state: CodeReviewState) -> CodeReviewState:
        """Initial analysis node - overview and general issues."""
        try:
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content="""You are an expert code reviewer. Provide an initial analysis of the code diff focusing on:
1. Overall changes summary
2. Potential breaking changes
3. General code quality issues
4. Areas requiring deeper analysis

Return a JSON object with:
- summary: Brief overview of changes
- breaking_changes: List of potential breaking changes
- general_issues: List of general code quality issues
- focus_areas: Areas needing specialized analysis"""),
                HumanMessage(content=f"""
File: {state['filename'] or 'Unknown'}
Diff Content:
{state['diff_content'][:3000]}

Context: {json.dumps(state['context'], indent=2)}
""")
            ])
            
            model = self._get_primary_model()
            if not model:
                raise Exception("No LLM model available")
            
            chain = prompt | model | JsonOutputParser()
            result = await chain.ainvoke({})
            
            state["initial_analysis"] = result
            self.logger.info("Initial analysis completed")
            
        except Exception as e:
            error_msg = f"Initial analysis failed: {str(e)}"
            self.logger.error(error_msg)
            state["errors"].append(error_msg)
            state["initial_analysis"] = {"summary": "Analysis failed", "error": str(e)}
        
        return state
    
    async def _security_analysis_node(self, state: CodeReviewState) -> CodeReviewState:
        """Security analysis node - security vulnerabilities and concerns."""
        try:
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content="""You are a security expert. Analyze the code diff for security issues:
1. SQL injection vulnerabilities
2. XSS vulnerabilities
3. Authentication/authorization issues
4. Data validation problems
5. Sensitive data exposure
6. Cryptographic issues

Return a JSON object with:
- security_score: Score from 1-10 (10 = very secure)
- vulnerabilities: List of security issues found
- recommendations: Security improvement suggestions"""),
                HumanMessage(content=f"""
File: {state['filename'] or 'Unknown'}
Diff Content:
{state['diff_content'][:3000]}

Initial Analysis: {json.dumps(state.get('initial_analysis', {}), indent=2)}
""")
            ])
            
            model = self._get_primary_model()
            chain = prompt | model | JsonOutputParser()
            result = await chain.ainvoke({})
            
            state["security_analysis"] = result
            self.logger.info("Security analysis completed")
            
        except Exception as e:
            error_msg = f"Security analysis failed: {str(e)}"
            self.logger.error(error_msg)
            state["errors"].append(error_msg)
            state["security_analysis"] = {"security_score": 5, "error": str(e)}
        
        return state
    
    async def _performance_analysis_node(self, state: CodeReviewState) -> CodeReviewState:
        """Performance analysis node - performance issues and optimizations."""
        try:
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content="""You are a performance expert. Analyze the code diff for performance issues:
1. Inefficient algorithms or data structures
2. Database query optimizations
3. Memory usage concerns
4. Network request optimizations
5. Caching opportunities
6. Async/await usage

Return a JSON object with:
- performance_score: Score from 1-10 (10 = excellent performance)
- bottlenecks: List of performance bottlenecks
- optimizations: Performance improvement suggestions"""),
                HumanMessage(content=f"""
File: {state['filename'] or 'Unknown'}
Diff Content:
{state['diff_content'][:3000]}

Initial Analysis: {json.dumps(state.get('initial_analysis', {}), indent=2)}
""")
            ])
            
            model = self._get_primary_model()
            chain = prompt | model | JsonOutputParser()
            result = await chain.ainvoke({})
            
            state["performance_analysis"] = result
            self.logger.info("Performance analysis completed")
            
        except Exception as e:
            error_msg = f"Performance analysis failed: {str(e)}"
            self.logger.error(error_msg)
            state["errors"].append(error_msg)
            state["performance_analysis"] = {"performance_score": 5, "error": str(e)}
        
        return state
    
    async def _quality_analysis_node(self, state: CodeReviewState) -> CodeReviewState:
        """Code quality analysis node - maintainability and best practices."""
        try:
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content="""You are a code quality expert. Analyze the code diff for quality issues:
1. Code organization and structure
2. Naming conventions
3. Documentation and comments
4. Error handling
5. Testing considerations
6. Maintainability concerns

Return a JSON object with:
- quality_score: Score from 1-10 (10 = excellent quality)
- issues: List of code quality issues
- improvements: Quality improvement suggestions"""),
                HumanMessage(content=f"""
File: {state['filename'] or 'Unknown'}
Diff Content:
{state['diff_content'][:3000]}

Initial Analysis: {json.dumps(state.get('initial_analysis', {}), indent=2)}
""")
            ])
            
            model = self._get_primary_model()
            chain = prompt | model | JsonOutputParser()
            result = await chain.ainvoke({})
            
            state["quality_analysis"] = result
            self.logger.info("Quality analysis completed")
            
        except Exception as e:
            error_msg = f"Quality analysis failed: {str(e)}"
            self.logger.error(error_msg)
            state["errors"].append(error_msg)
            state["quality_analysis"] = {"quality_score": 5, "error": str(e)}
        
        return state
    
    async def _final_report_node(self, state: CodeReviewState) -> CodeReviewState:
        """Final report node - synthesize all analyses into a comprehensive report."""
        try:
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content="""You are a senior code reviewer. Synthesize all the analysis results into a comprehensive final report.

Create a JSON object with:
- overall_score: Overall score from 1-10
- summary: Executive summary of findings
- critical_issues: List of critical issues that must be addressed
- recommendations: Prioritized list of recommendations
- approval_status: "approved", "requires_changes", or "rejected"
- reasoning: Explanation for the approval status"""),
                HumanMessage(content=f"""
File: {state['filename'] or 'Unknown'}

Initial Analysis: {json.dumps(state.get('initial_analysis', {}), indent=2)}
Security Analysis: {json.dumps(state.get('security_analysis', {}), indent=2)}
Performance Analysis: {json.dumps(state.get('performance_analysis', {}), indent=2)}
Quality Analysis: {json.dumps(state.get('quality_analysis', {}), indent=2)}

Errors encountered: {state['errors']}
""")
            ])
            
            model = self._get_primary_model()
            chain = prompt | model | JsonOutputParser()
            result = await chain.ainvoke({})
            
            state["final_report"] = result
            self.logger.info("Final report generated")
            
        except Exception as e:
            error_msg = f"Final report generation failed: {str(e)}"
            self.logger.error(error_msg)
            state["errors"].append(error_msg)
            
            # Generate fallback report
            state["final_report"] = {
                "overall_score": 5,
                "summary": "Analysis completed with errors",
                "critical_issues": state["errors"],
                "recommendations": ["Review analysis errors", "Re-run analysis"],
                "approval_status": "requires_changes",
                "reasoning": "Analysis incomplete due to errors",
                "error": str(e)
            }
        
        return state
    
    async def analyze_code_diff(
        self, 
        diff_content: str, 
        file_content: Optional[str] = None,
        filename: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        analysis_type: str = "comprehensive",
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze code diff using LangGraph workflow.
        
        Args:
            diff_content: Git diff content to analyze
            file_content: Full file content for context
            filename: Name of the file being analyzed
            context: Additional context about the PR/file
            analysis_type: Type of analysis to perform
            focus_areas: Specific areas to focus on
            
        Returns:
            Dict[str, Any]: Comprehensive analysis results
        """
        self.logger.info(
            "Starting LangGraph code diff analysis",
            filename=filename,
            analysis_type=analysis_type,
            focus_areas=focus_areas,
            diff_size=len(diff_content)
        )
        
        try:
            if not LANGCHAIN_AVAILABLE or not self.workflow:
                return await self._fallback_analysis(diff_content, filename, context)
            
            # Prepare initial state
            initial_state: CodeReviewState = {
                "diff_content": diff_content,
                "file_content": file_content,
                "filename": filename,
                "context": context or {},
                "analysis_type": analysis_type,
                "focus_areas": focus_areas,
                "initial_analysis": None,
                "security_analysis": None,
                "performance_analysis": None,
                "quality_analysis": None,
                "final_report": None,
                "errors": []
            }
            
            # Execute the workflow
            config = {"configurable": {"thread_id": f"analysis_{datetime.now().isoformat()}"}}
            final_state = await self.workflow.ainvoke(initial_state, config=config)
            
            # Format the final result
            result = self._format_analysis_result(final_state)
            
            self.logger.info(
                "LangGraph analysis completed",
                filename=filename,
                overall_score=result.get("overall_score", 0),
                issues_count=len(result.get("issues", []))
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"LangGraph analysis failed: {e}")
            return await self._fallback_analysis(diff_content, filename, context, str(e))
    
    def _format_analysis_result(self, state: CodeReviewState) -> Dict[str, Any]:
        """Format the workflow state into the expected analysis result format."""
        final_report = state.get("final_report", {})
        
        # Combine all issues from different analyses
        all_issues = []
        
        # Add issues from each analysis
        for analysis_key in ["initial_analysis", "security_analysis", "performance_analysis", "quality_analysis"]:
            analysis = state.get(analysis_key, {})
            if isinstance(analysis, dict):
                # Extract issues with different possible keys
                issues = (
                    analysis.get("general_issues", []) +
                    analysis.get("vulnerabilities", []) +
                    analysis.get("bottlenecks", []) +
                    analysis.get("issues", [])
                )
                
                for issue in issues:
                    if isinstance(issue, str):
                        all_issues.append({
                            "type": analysis_key.replace("_analysis", ""),
                            "severity": "medium",
                            "message": issue,
                            "line": None,
                            "suggestion": None
                        })
                    elif isinstance(issue, dict):
                        all_issues.append({
                            "type": analysis_key.replace("_analysis", ""),
                            "severity": issue.get("severity", "medium"),
                            "message": issue.get("message", str(issue)),
                            "line": issue.get("line"),
                            "suggestion": issue.get("suggestion")
                        })
        
        return {
            "overall_score": final_report.get("overall_score", 5),
            "summary": final_report.get("summary", "Code analysis completed"),
            "issues": all_issues,
            "recommendations": final_report.get("recommendations", []),
            "approval_status": final_report.get("approval_status", "requires_changes"),
            "detailed_analysis": {
                "initial": state.get("initial_analysis", {}),
                "security": state.get("security_analysis", {}),
                "performance": state.get("performance_analysis", {}),
                "quality": state.get("quality_analysis", {})
            },
            "workflow_errors": state.get("errors", []),
            "analysis_metadata": {
                "provider": self.settings.DEFAULT_LLM_PROVIDER,
                "model": self.settings.OLLAMA_MODEL if self.settings.DEFAULT_LLM_PROVIDER == "ollama" else "unknown",
                "timestamp": datetime.now().isoformat(),
                "workflow_used": "langgraph"
            }
        }
    
    async def _fallback_analysis(
        self, 
        diff_content: str, 
        filename: Optional[str], 
        context: Optional[Dict[str, Any]], 
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fallback analysis when LangChain is not available."""
        self.logger.warning("Using fallback analysis")
        
        return {
            "overall_score": 5,
            "summary": f"Fallback analysis for {filename or 'unknown file'}",
            "issues": [
                {
                    "type": "system",
                    "severity": "low",
                    "message": "LangChain analysis not available - using fallback",
                    "line": None,
                    "suggestion": "Install LangChain ecosystem for advanced analysis"
                }
            ],
            "recommendations": [
                "Install LangChain and LangGraph for advanced analysis",
                "Configure Ollama for local LLM support"
            ],
            "approval_status": "requires_changes",
            "analysis_metadata": {
                "provider": "fallback",
                "model": "none",
                "timestamp": datetime.now().isoformat(),
                "workflow_used": "fallback",
                "error": error
            }
        }


# Create service instance for easy import
langchain_llm_service = LangChainLLMService()
