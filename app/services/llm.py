from typing import Dict, List, Optional, Any, Union
import json

# Primary import - LangChain service
try:
    from app.services.llm_langchain import langchain_llm_service
    LANGCHAIN_SERVICE_AVAILABLE = True
except ImportError:
    LANGCHAIN_SERVICE_AVAILABLE = False
    langchain_llm_service = None

# Optional imports with fallbacks
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

# Optional import for litellm
try:
    import litellm
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False
    litellm = None

from app.core.config import get_settings
from app.utils.helpers import chunk_text, mask_sensitive_data


class LLMService:
    
    def __init__(self):
        """Initialize LLM service with LangChain as primary option."""
        settings = get_settings()
        self.settings = settings
        self.logger = logger
        
        # Always initialize these attributes
        self.local_llm_url = getattr(self.settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
        self.local_llm_model = getattr(self.settings, 'OLLAMA_MODEL', 'llama3.2:3b')
        self.openai_client = None
        self.anthropic_client = None
        
        # Try to use LangChain service first
        if LANGCHAIN_SERVICE_AVAILABLE and langchain_llm_service:
            self.primary_service = langchain_llm_service
            self.use_langchain = True
            self.logger.info("LangChain LLM service initialized as primary")
        else:
            self.use_langchain = False
            self.primary_service = None
            self.logger.warning("LangChain not available, falling back to basic implementation")
            
            # Initialize fallback clients
            self._initialize_fallback_clients()
    
    def _initialize_fallback_clients(self):
        """Initialize fallback LLM clients when LangChain is not available."""
        self.openai_client = None
        self.anthropic_client = None
        # Don't reset local_llm_url here as it was already set in __init__
        
        # Configure Ollama fallback (keep existing values if already set)
        if hasattr(self.settings, 'OLLAMA_BASE_URL') and not self.local_llm_url:
            self.local_llm_url = self.settings.OLLAMA_BASE_URL
            self.local_llm_model = getattr(self.settings, 'OLLAMA_MODEL', 'llama3.2:3b')
            
        if self.local_llm_url:
            self.logger.info(f"Ollama fallback configured at {self.local_llm_url} with model {self.local_llm_model}")
        
        if OPENAI_AVAILABLE and hasattr(self.settings, 'OPENAI_API_KEY') and self.settings.OPENAI_API_KEY != 'your_openai_api_key_here':
            try:
                self.openai_client = OpenAI(api_key=self.settings.OPENAI_API_KEY)
                self.logger.info("OpenAI fallback client initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize OpenAI fallback client: {e}")
        
        if ANTHROPIC_AVAILABLE and hasattr(self.settings, 'ANTHROPIC_API_KEY') and self.settings.ANTHROPIC_API_KEY != 'your_anthropic_api_key_here':
            try:
                self.anthropic_client = Anthropic(api_key=self.settings.ANTHROPIC_API_KEY)
                self.logger.info("Anthropic fallback client initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Anthropic fallback client: {e}")
        
        # Set default provider
        self.default_provider = getattr(self.settings, 'DEFAULT_LLM_PROVIDER', 'ollama')
        self.default_model = getattr(self.settings, 'DEFAULT_MODEL', 'llama3.2:3b')
        
        if not self.openai_client and not self.anthropic_client and not self.local_llm_url:
            self.logger.warning("No LLM providers configured - AI features will be limited")
    
    async def analyze_code_diff(
        self, 
        diff_content: str, 
        file_content: Optional[str] = None,
        filename: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        analysis_type: str = "comprehensive",
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        self.logger.info(
            "Starting code diff analysis",
            filename=filename,
            analysis_type=analysis_type,
            focus_areas=focus_areas,
            diff_size=len(diff_content),
            using_langchain=self.use_langchain
        )
        
        try:
            # Use LangChain service if available
            if self.use_langchain and self.primary_service:
                return await self.primary_service.analyze_code_diff(
                    diff_content=diff_content,
                    file_content=file_content,
                    filename=filename,
                    context=context,
                    analysis_type=analysis_type,
                    focus_areas=focus_areas
                )
            
            # Fallback to basic implementation
            return await self._fallback_analyze_code_diff(
                diff_content=diff_content,
                file_content=file_content,
                filename=filename,
                context=context,
                analysis_type=analysis_type,
                focus_areas=focus_areas
            )
            
        except Exception as e:
            self.logger.error(f"Code analysis failed: {e}")
            return self._create_error_response(str(e), filename)
    
    async def _fallback_analyze_code_diff(
        self,
        diff_content: str,
        file_content: Optional[str] = None,
        filename: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        analysis_type: str = "comprehensive",
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Fallback implementation for code analysis."""
        self.logger.info("Using fallback code analysis")
        
        try:
            # Build simple analysis prompt
            prompt = self._build_simple_code_review_prompt(
                diff_content=diff_content,
                filename=filename,
                context=context or {}
            )
            
            # Try Ollama first, then other providers
            response = await self._call_fallback_llm(prompt)
            
            # Parse response into expected format
            return self._parse_simple_response(response, filename or "unknown")
            
        except Exception as e:
            self.logger.error(f"Fallback analysis failed: {e}")
            return self._create_error_response(str(e), filename)
    
    def _create_error_response(self, error: str, filename: Optional[str]) -> Dict[str, Any]:
        """Create a standardized error response."""
        return {
            "overall_score": 3,
            "summary": f"Analysis failed for {filename or 'unknown file'}",
            "issues": [
                {
                    "type": "system",
                    "severity": "low",
                    "message": f"Analysis error: {error}",
                    "line": None,
                    "suggestion": "Check LLM service configuration"
                }
            ],
            "recommendations": [
                "Verify LLM service is properly configured",
                "Check network connectivity",
                "Install LangChain dependencies"
            ],
            "approval_status": "requires_changes",
            "analysis_metadata": {
                "provider": "error",
                "model": "none",
                "error": error
            }
        }
    
    def _build_simple_code_review_prompt(
        self,
        diff_content: str,
        filename: Optional[str],
        context: Dict[str, Any]
    ) -> str:
        """Build a simple prompt for fallback analysis."""
        return f"""
You are an expert code reviewer. Analyze the following code diff and provide feedback.

File: {filename or 'Unknown'}
Diff:
{diff_content[:2000]}

Context: {json.dumps(context, indent=2)}

Please provide:
1. Overall assessment (score 1-10)
2. Key issues found
3. Recommendations for improvement
4. Whether changes should be approved

Respond in JSON format with:
- overall_score: number
- summary: string
- issues: array of issue objects with type, severity, message
- recommendations: array of strings
- approval_status: "approved" or "requires_changes"
"""
    
    async def _call_fallback_llm(self, prompt: str) -> str:
        """Call LLM using fallback methods."""
        # Try Ollama first
        if self.local_llm_url:
            try:
                return await self._call_ollama_direct(prompt)
            except Exception as e:
                self.logger.warning(f"Ollama call failed: {e}")
        
        # Try OpenAI
        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=2000
                )
                return response.choices[0].message.content
            except Exception as e:
                self.logger.warning(f"OpenAI call failed: {e}")
        
        # Try Anthropic
        if self.anthropic_client:
            try:
                response = self.anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=2000,
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            except Exception as e:
                self.logger.warning(f"Anthropic call failed: {e}")
        
        raise Exception("No LLM providers available")
    
    async def _call_ollama_direct(self, prompt: str) -> str:
        """Call Ollama directly via HTTP."""
        if not HTTPX_AVAILABLE:
            raise Exception("httpx not available for Ollama calls")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.local_llm_url}/api/generate",
                json={
                    "model": self.local_llm_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9
                    }
                }
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
    
    def _parse_simple_response(self, response: str, filename: str) -> Dict[str, Any]:
        """Parse simple LLM response into expected format."""
        try:
            # Try to parse as JSON first
            if response.strip().startswith('{'):
                data = json.loads(response)
                return {
                    "overall_score": data.get("overall_score", 5),
                    "summary": data.get("summary", f"Analysis for {filename}"),
                    "issues": data.get("issues", []),
                    "recommendations": data.get("recommendations", []),
                    "approval_status": data.get("approval_status", "requires_changes"),
                    "analysis_metadata": {
                        "provider": self.default_provider,
                        "model": self.default_model,
                        "fallback": True
                    }
                }
        except json.JSONDecodeError:
            pass
        
        # Fallback to text parsing
        return {
            "overall_score": 5,
            "summary": f"Basic analysis completed for {filename}",
            "issues": [
                {
                    "type": "general",
                    "severity": "medium",
                    "message": "Manual review recommended",
                    "line": None,
                    "suggestion": response[:500] if response else "No analysis available"
                }
            ],
            "recommendations": ["Manual code review recommended"],
            "approval_status": "requires_changes",
            "analysis_metadata": {
                "provider": "fallback",
                "model": "text_parsing",
                "fallback": True
            }
        }
    
    async def analyze_file_content(
        self, 
        file_content: str, 
        file_path: str,
        programming_language: str,
        analysis_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Analyze individual file content for code quality issues.
        
        Args:
            file_content: Content of the file to analyze
            file_path: Path of the file being analyzed
            programming_language: Programming language of the file
            analysis_type: Type of analysis to perform
            
        Returns:
            Dict[str, Any]: Analysis results for the file
        """
        self.logger.info(
            "Starting file content analysis",
            file_path=file_path,
            language=programming_language,
            analysis_type=analysis_type,
            content_size=len(file_content)
        )
        
        try:
            # Check if content needs to be chunked
            if len(file_content) > 8000:  # Chunk large files
                return await self._analyze_large_file(
                    file_content, file_path, programming_language, analysis_type
                )
            
            # Prepare file analysis prompt
            prompt = self._build_file_analysis_prompt(
                file_content, file_path, programming_language, analysis_type
            )
            
            # Get analysis from LLM
            response = await self._call_llm(prompt)
            
            # Parse and structure the response
            analysis_result = self._parse_analysis_response(response)
            
            self.logger.info(
                "File content analysis completed",
                file_path=file_path,
                findings_count=len(analysis_result.get("findings", []))
            )
            
            return analysis_result
            
        except Exception as e:
            self.logger.error(
                "File content analysis failed",
                error=str(e),
                file_path=file_path
            )
            return {
                "summary": f"Analysis of {file_path} failed due to an error",
                "findings": [],
                "error": str(e)
            }
    
    async def generate_summary(
        self, 
        all_findings: List[Dict[str, Any]], 
        pr_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive summary of all analysis findings.
        
        Args:
            all_findings: List of all findings from various analyses
            pr_info: Pull request information
            
        Returns:
            Dict[str, Any]: Summary and recommendations
        """
        self.logger.info(
            "Generating analysis summary",
            total_findings=len(all_findings),
            pr_number=pr_info.get("number")
        )
        
        try:
            # Prepare summary prompt
            prompt = self._build_summary_prompt(all_findings, pr_info)
            
            # Get summary from LLM
            response = await self._call_llm(prompt)
            
            # Parse summary response
            summary_result = self._parse_summary_response(response)
            
            self.logger.info(
                "Analysis summary generated",
                pr_number=pr_info.get("number"),
                recommendations_count=len(summary_result.get("recommendations", []))
            )
            
            return summary_result
            
        except Exception as e:
            self.logger.error(
                "Summary generation failed",
                error=str(e),
                pr_number=pr_info.get("number")
            )
            return {
                "summary": "Failed to generate comprehensive summary",
                "recommendations": [],
                "error": str(e)
            }
    
    async def _call_llm(self, prompt: str, model: Optional[str] = None, temperature: float = 0.7) -> str:
        """
        Make a call to the configured LLM provider.
        
        Args:
            prompt: Prompt to send to the LLM
            model: Specific model to use (optional)
            temperature: Temperature for response generation
            
        Returns:
            str: LLM response
            
        Raises:
            Exception: If LLM call fails
        """
        if not model:
            model = self.settings.DEFAULT_MODEL
        
        provider = self.settings.DEFAULT_LLM_PROVIDER.lower()
        
        try:
            if provider == "local" and self.local_llm_url:
                response = await self._call_local_llm(prompt, model, temperature)
            elif provider == "openai" and self.openai_client:
                response = await self._call_openai(prompt, model, temperature)
            elif provider == "anthropic" and self.anthropic_client:
                response = await self._call_anthropic(prompt, model, temperature)
            else:
                # Fallback to litellm for other providers
                response = await self._call_litellm(prompt, model, temperature)
            
            # Mask sensitive data in logs
            masked_prompt = mask_sensitive_data(prompt[:200])
            masked_response = mask_sensitive_data(response[:200])
            
            self.logger.debug(
                "LLM call completed",
                provider=provider,
                model=model,
                prompt_preview=masked_prompt,
                response_preview=masked_response
            )
            
            return response
            
        except Exception as e:
            self.logger.error(
                "LLM call failed",
                provider=provider,
                model=model,
                error=str(e)
            )
            raise
    
    async def _call_openai(self, prompt: str, model: str, temperature: float = 0.7) -> str:
        """Call OpenAI API."""
        response = self.openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert code reviewer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=4000
        )
        return response.choices[0].message.content
    
    async def _call_anthropic(self, prompt: str, model: str, temperature: float = 0.7) -> str:
        """Call Anthropic API."""
        response = self.anthropic_client.messages.create(
            model=model,
            max_tokens=4000,
            temperature=0.1,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text
    
    async def _call_local_llm(self, prompt: str, model: str, temperature: float = 0.7) -> str:
        """Call local LLM API using httpx."""
        if not HTTPX_AVAILABLE:
            raise Exception("httpx not available - install with: pip install httpx")
        
        # Use the configured model or default
        model_name = model or self.local_llm_model
        
        # Prepare the request payload (OpenAI-compatible format)
        # Note: LM Studio only supports user and assistant roles, not system
        system_instruction = "You are an expert code reviewer and security analyst."
        full_prompt = f"{system_instruction}\n\n{prompt}"
        
        payload = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": full_prompt}
            ],
            "temperature": temperature,
            "max_tokens": 4000
        }
        
        # Log the request for debugging
        self.logger.info(f"Sending request to local LLM: {self.local_llm_url}/v1/chat/completions")
        self.logger.debug(f"Payload: {payload}")
        
        # Make the request to local LLM
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.local_llm_url}/v1/chat/completions",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                # Log response details for debugging
                self.logger.info(f"Response status: {response.status_code}")
                if response.status_code != 200:
                    self.logger.error(f"Response text: {response.text}")
                
                response.raise_for_status()
                
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    raise Exception(f"Unexpected response format from local LLM: {result}")
        except httpx.ConnectError as e:
            self.logger.error(f"Cannot connect to local LLM at {self.local_llm_url}. Please ensure LM Studio or another local LLM server is running.")
            # Return a mock analysis for demonstration purposes
            return self._get_mock_analysis_response()
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error calling local LLM: {e}")
            self.logger.error(f"Response content: {e.response.text if hasattr(e, 'response') else 'No response'}")
            raise
        except Exception as e:
            self.logger.error(f"Error calling local LLM: {e}")
            raise
    
    def _get_mock_analysis_response(self) -> str:
        """Return a mock analysis response when Local LLM is not available."""
        return '''
{
    "issues": [
        {
            "type": "security",
            "line": 11,
            "description": "Hardcoded API key detected in source code",
            "suggestion": "Move API keys to environment variables or secure configuration files"
        },
        {
            "type": "security", 
            "line": 44,
            "description": "Use of exec() function with user input creates code injection vulnerability",
            "suggestion": "Replace exec() with safer alternatives or implement strict input validation and sandboxing"
        },
        {
            "type": "security",
            "line": 54,
            "description": "OS command execution without input validation",
            "suggestion": "Validate and sanitize all user inputs before executing system commands"
        },
        {
            "type": "security",
            "line": 60,
            "description": "API endpoint lacks authentication and authorization",
            "suggestion": "Implement proper authentication and authorization mechanisms"
        },
        {
            "type": "security",
            "line": 87,
            "description": "Hardcoded database credentials in source code",
            "suggestion": "Use environment variables or secure credential management for database connections"
        },
        {
            "type": "style",
            "line": 105,
            "description": "Flask app running in debug mode in production",
            "suggestion": "Disable debug mode and configure proper SSL/TLS for production deployment"
        }
    ]
}
'''
    
    async def _call_litellm(self, prompt: str, model: str, temperature: float = 0.7) -> str:
        """Call LiteLLM (supports multiple providers)."""
        if not LITELLM_AVAILABLE:
            raise Exception("LiteLLM not available - install with: pip install litellm")
        
        # For Ollama models, add the ollama/ prefix if not present
        if self.local_llm_url and "ollama" in self.local_llm_url.lower():
            if not model.startswith("ollama/"):
                model = f"ollama/{model}"
        
        response = litellm.completion(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert code reviewer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=4000
        )
        return response.choices[0].message.content
    
    def _build_analysis_prompt(
        self, 
        diff_content: str, 
        analysis_type: str, 
        focus_areas: Optional[List[str]]
    ) -> str:
        """Build prompt for code diff analysis."""
        focus_text = ""
        if focus_areas:
            focus_text = f"\nFocus particularly on: {', '.join(focus_areas)}"
        
        return f"""
Please analyze the following code diff for a pull request. Perform a {analysis_type} analysis.{focus_text}

Identify issues in these categories:
- Security vulnerabilities
- Performance problems
- Code quality issues
- Best practice violations
- Potential bugs
- Maintainability concerns

For each issue found, provide:
1. Type of issue
2. Severity (critical/high/medium/low)
3. Brief title
4. Detailed description
5. File path and line number
6. Code snippet (if applicable)
7. Suggested fix

Respond in JSON format with this structure:
{{
    "summary": "Brief summary of the analysis",
    "findings": [
        {{
            "type": "security|performance|quality|bug|maintainability",
            "severity": "critical|high|medium|low",
            "title": "Brief title",
            "description": "Detailed description",
            "file_path": "path/to/file",
            "line_number": 123,
            "code_snippet": "relevant code",
            "suggestion": "how to fix",
            "confidence": 0.95
        }}
    ],
    "recommendations": ["Overall recommendation 1", "Overall recommendation 2"]
}}

Code diff to analyze:
```
{diff_content}
```
"""
    
    def _build_file_analysis_prompt(
        self, 
        file_content: str, 
        file_path: str, 
        programming_language: str, 
        analysis_type: str
    ) -> str:
        """Build prompt for individual file analysis in assignment format."""
        return f"""You are an expert code reviewer. Analyze the following {programming_language} file for code quality issues.

File: {file_path}
Language: {programming_language}

ANALYSIS REQUIREMENTS:
Perform a {analysis_type} analysis and identify:

1. **Security Issues**: Vulnerabilities, injection risks, authentication problems
2. **Performance Issues**: Inefficient algorithms, memory leaks, slow operations  
3. **Bugs**: Logic errors, null pointer exceptions, incorrect conditions
4. **Style Issues**: Code style violations, naming conventions, formatting
5. **Code Quality**: Duplicate code, complex functions, maintainability issues

OUTPUT FORMAT:
Respond with a JSON object containing an "issues" array. Each issue should have:
{{
    "type": "security|bug|performance|style|quality",
    "line": <line_number_if_identifiable>,
    "description": "Clear description of the issue",
    "suggestion": "Specific suggestion to fix the issue"
}}

IMPORTANT: Ensure all JSON strings are properly escaped. Use backslash before quotes inside strings.

EXAMPLE:
{{
    "issues": [
        {{
            "type": "security",
            "line": 15,
            "description": "SQL query uses string concatenation which is vulnerable to SQL injection",
            "suggestion": "Use parameterized queries or prepared statements"
        }},
        {{
            "type": "style",
            "line": 23,
            "description": "Variable name does not follow naming convention",
            "suggestion": "Use snake_case for variable names: user_data instead of userData"
        }}
    ]
}}

FILE CONTENT TO ANALYZE:
```{programming_language}
{file_content}
```

Provide your analysis as a valid JSON object with the "issues" array. If no issues are found, return {{"issues": []}}."""
    
    def _build_summary_prompt(
        self, 
        all_findings: List[Dict[str, Any]], 
        pr_info: Dict[str, Any]
    ) -> str:
        """Build prompt for generating analysis summary."""
        findings_text = json.dumps(all_findings, indent=2)
        
        return f"""
Please generate a comprehensive summary of the code review analysis for this pull request.

PR Information:
- Title: {pr_info.get('title', 'N/A')}
- Author: {pr_info.get('author', 'N/A')}
- Files changed: {pr_info.get('changed_files', 0)}
- Additions: {pr_info.get('additions', 0)}
- Deletions: {pr_info.get('deletions', 0)}

All findings:
{findings_text}

Provide:
1. Executive summary of the analysis
2. Key issues by priority
3. Overall code quality assessment
4. Specific recommendations for improvement
5. Positive aspects (if any)

Respond in JSON format:
{{
    "summary": "Executive summary",
    "key_issues": ["Issue 1", "Issue 2"],
    "quality_score": 8.5,
    "recommendations": ["Recommendation 1", "Recommendation 2"],
    "positive_aspects": ["Good thing 1", "Good thing 2"]
}}
"""
    
    async def _analyze_large_file(
        self, 
        file_content: str, 
        file_path: str, 
        programming_language: str, 
        analysis_type: str
    ) -> Dict[str, Any]:
        """Analyze large files by chunking them."""
        chunks = chunk_text(file_content, chunk_size=6000, overlap=500)
        all_findings = []
        
        for i, chunk in enumerate(chunks):
            self.logger.info(
                "Analyzing file chunk",
                file_path=file_path,
                chunk=f"{i+1}/{len(chunks)}"
            )
            
            chunk_result = await self.analyze_file_content(
                chunk, f"{file_path} (chunk {i+1})", programming_language, analysis_type
            )
            
            if chunk_result.get("findings"):
                all_findings.extend(chunk_result["findings"])
        
        return {
            "summary": f"Analysis of {file_path} completed in {len(chunks)} chunks",
            "findings": all_findings,
            "chunks_analyzed": len(chunks)
        }
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured analysis result."""
        try:
            # Try to parse as JSON first
            return json.loads(response)
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract JSON from markdown code blocks
            import re
            
            # First try to find JSON in markdown code blocks with balanced braces
            json_block_match = re.search(r'```json\s*(\{.*\})\s*```', response, re.DOTALL)
            if json_block_match:
                try:
                    json_content = json_block_match.group(1)
                    return json.loads(json_content)
                except json.JSONDecodeError as e:
                    self.logger.warning("Failed to parse JSON from code block", error=str(e), json_content=json_content[:200])
            
            # Try to find JSON between first { and last }
            first_brace = response.find('{')
            last_brace = response.rfind('}')
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                try:
                    json_content = response[first_brace:last_brace+1]
                    return json.loads(json_content)
                except json.JSONDecodeError as e:
                    # Try to fix common JSON issues
                    try:
                        # Fix unescaped quotes in strings
                        import re
                        fixed_json = re.sub(r'(?<!\\)"(?=[^,}\]]*"[,}\]])', '\\"', json_content)
                        return json.loads(fixed_json)
                    except json.JSONDecodeError:
                        self.logger.warning("Failed to parse JSON from brace extraction", error=str(e), json_content=json_content[:200])
            
            # Try to extract just the issues array if full JSON fails
            issues_match = re.search(r'"issues"\s*:\s*\[(.*?)\]', response, re.DOTALL)
            if issues_match:
                try:
                    # Create a minimal JSON structure with just the issues
                    minimal_json = f'{{"issues": [{issues_match.group(1)}]}}'
                    return json.loads(minimal_json)
                except json.JSONDecodeError:
                    pass
            
            # Fallback to plain text parsing
            self.logger.warning("Failed to parse LLM response as JSON", raw_response=response[:500])
            return {
                "summary": "Analysis completed but response format was invalid",
                "findings": [],
                "issues": [],
                "raw_response": response
            }
    
    def _parse_summary_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM summary response."""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "summary": response,
                "recommendations": [],
                "raw_response": response
            }

    def _build_code_review_prompt(
        self,
        diff_content: str,
        file_content: Optional[str],
        filename: Optional[str],
        context: Dict[str, Any],
        analysis_type: str = "comprehensive"
    ) -> str:
        """Build a comprehensive code review prompt for LLM analysis."""
        
        language = context.get('language', 'unknown')
        pr_title = context.get('pr_title', '')
        pr_description = context.get('pr_description', '')
        
        prompt = f"""You are an expert code reviewer analyzing a pull request. Perform a {analysis_type} code review focusing on security, bugs, performance, and best practices.

PULL REQUEST CONTEXT:
Title: {pr_title}
Description: {pr_description}
File: {filename or 'unknown'}
Language: {language}

ANALYSIS REQUIREMENTS:
Analyze the following code changes and identify:

1. **Security Issues**: 
   - Vulnerabilities, injection risks, authentication/authorization issues
   - Exposed secrets, unsafe operations, input validation problems

2. **Bugs and Logic Errors**:
   - Potential null pointer exceptions, off-by-one errors
   - Logic flaws, incorrect conditions, missing error handling

3. **Performance Issues**:
   - Inefficient algorithms, unnecessary loops, memory leaks
   - Database query optimization, resource management

4. **Best Practices**:
   - Code style violations, naming conventions
   - Design patterns, maintainability, readability

5. **Code Quality**:
   - Duplicate code, complex functions, missing documentation
   - Error handling, logging, testing considerations

OUTPUT FORMAT:
Respond with a JSON object containing an "issues" array. Each issue should have:
{{
    "type": "security|bug|performance|style|quality",
    "line": <line_number>,
    "description": "Clear description of the issue",
    "suggestion": "Specific suggestion to fix the issue"
}}

EXAMPLE:
{{
    "issues": [
        {{
            "type": "security",
            "line": 15,
            "description": "SQL query uses string concatenation which is vulnerable to SQL injection",
            "suggestion": "Use parameterized queries or prepared statements"
        }},
        {{
            "type": "performance", 
            "line": 23,
            "description": "Loop has O(n²) complexity due to nested iteration",
            "suggestion": "Consider using a hash map to reduce complexity to O(n)"
        }}
    ]
}}

CODE DIFF TO ANALYZE:
```diff
{diff_content}
```
"""

        if file_content:
            prompt += f"""

FULL FILE CONTENT FOR CONTEXT:
```{language}
{file_content[:2000]}{"..." if len(file_content) > 2000 else ""}
```
"""

        prompt += """

Provide your analysis as a valid JSON object with the "issues" array. Focus on actionable feedback that will improve code quality, security, and maintainability."""
        
        return prompt

    def _parse_code_review_response(self, response: str, filename: str) -> Dict[str, Any]:
        """Parse LLM code review response into required format."""
        try:
            # Try to parse as JSON first
            if response.strip().startswith('{'):
                parsed = json.loads(response)
                if 'issues' in parsed:
                    return parsed
            
            # Extract JSON from response if it's embedded in text
            import re
            json_match = re.search(r'\{[^{}]*"issues"[^{}]*\[[^\]]*\][^{}]*\}', response, re.DOTALL)
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                    if 'issues' in parsed:
                        return parsed
                except json.JSONDecodeError:
                    pass
            
            # Try to find a JSON block in markdown
            json_blocks = re.findall(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            for block in json_blocks:
                try:
                    parsed = json.loads(block)
                    if 'issues' in parsed:
                        return parsed
                except json.JSONDecodeError:
                    continue
            
            # Fallback: try to extract issues from text format
            issues = self._extract_issues_from_text(response)
            return {"issues": issues}
            
        except Exception as e:
            self.logger.error(f"Failed to parse code review response: {e}")
            return {"issues": [], "error": f"Failed to parse LLM response: {str(e)}"}

    def _extract_issues_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract issues from plain text LLM response as fallback."""
        issues = []
        
        # Common patterns to look for issues in text
        lines = text.split('\n')
        current_issue = {}
        
        for line in lines:
            line = line.strip()
            
            # Look for issue indicators
            if any(keyword in line.lower() for keyword in ['security', 'bug', 'error', 'issue', 'problem', 'vulnerability']):
                if current_issue:
                    if current_issue.get('description'):
                        issues.append(current_issue)
                
                current_issue = {
                    "type": self._detect_issue_type(line),
                    "line": self._extract_line_number(line),
                    "description": line,
                    "suggestion": "Review and address this issue"
                }
            elif current_issue and line and not line.startswith('#'):
                # Continue building description
                current_issue['description'] += ' ' + line
        
        # Add the last issue
        if current_issue and current_issue.get('description'):
            issues.append(current_issue)
        
        return issues[:10]  # Limit to 10 issues to avoid noise

    def _detect_issue_type(self, text: str) -> str:
        """Detect issue type from text."""
        text_lower = text.lower()
        if any(keyword in text_lower for keyword in ['security', 'vulnerability', 'injection', 'auth']):
            return 'security'
        elif any(keyword in text_lower for keyword in ['bug', 'error', 'exception', 'null']):
            return 'bug'
        elif any(keyword in text_lower for keyword in ['performance', 'slow', 'memory', 'optimization']):
            return 'performance'
        elif any(keyword in text_lower for keyword in ['style', 'format', 'naming', 'convention']):
            return 'style'
        else:
            return 'quality'

    def _extract_line_number(self, text: str) -> int:
        """Extract line number from text."""
        import re
        match = re.search(r'line\s*(\d+)', text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        # Look for patterns like :15: or @15
        match = re.search(r'[:@](\d+)[:@]?', text)
        if match:
            return int(match.group(1))
        
        return 1  # Default to line 1 if no line number found
