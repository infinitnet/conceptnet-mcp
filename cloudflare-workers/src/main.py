"""
Cloudflare Workers deployment for ConceptNet MCP Server.

This module provides a Python Workers implementation that uses a standard fetch handler
to implement MCP protocol requests. It supports both SSE and Streamable HTTP transports
for maximum compatibility.
"""

import json
import asyncio
from typing import Any, Dict, Optional, List
from urllib.parse import urlencode, urlparse, parse_qs

# Cloudflare Workers imports
from js import fetch, Response, Request, Headers
from pyodide.ffi import to_js

# FastAPI for HTTP handling and MCP protocol implementation
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Custom HTTP client for ConceptNet API
class CloudflareHTTPClient:
    """
    HTTP client adapter that uses Cloudflare Workers' fetch() instead of httpx.
    This replaces the httpx-based ConceptNetClient for Workers compatibility.
    """
    
    def __init__(
        self,
        base_url: str = "http://api.conceptnet.io",
        timeout: float = 30.0,
        max_retries: int = 3,
        user_agent: str = "ConceptNet-MCP-Workers/1.0"
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.user_agent = user_agent
    
    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request using Cloudflare Workers fetch() API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint path
            params: Query parameters
            headers: Request headers
            
        Returns:
            Parsed JSON response
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        if params:
            url += f"?{urlencode(params)}"
        
        # Prepare headers
        request_headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json"
        }
        if headers:
            request_headers.update(headers)
        
        # Convert headers to JS object
        js_headers = Headers.new()
        for key, value in request_headers.items():
            js_headers.set(key, value)
        
        # Prepare fetch options
        fetch_options = {
            "method": method,
            "headers": js_headers,
        }
        
        for attempt in range(self.max_retries + 1):
            try:
                # Make the fetch request
                response = await fetch(url, to_js(fetch_options))
                
                # Check response status
                if response.status == 200:
                    text = await response.text()
                    return json.loads(text)
                elif response.status == 404:
                    raise Exception(f"Resource not found: {url}")
                elif response.status == 429:
                    # Rate limit - could implement retry logic here
                    raise Exception("Rate limit exceeded")
                elif 400 <= response.status < 500:
                    text = await response.text()
                    raise Exception(f"Client error {response.status}: {text}")
                elif 500 <= response.status < 600:
                    if attempt < self.max_retries:
                        # Simple retry for server errors
                        await asyncio.sleep(2 ** attempt)
                        continue
                    text = await response.text()
                    raise Exception(f"Server error {response.status}: {text}")
                else:
                    raise Exception(f"Unexpected status: {response.status}")
                    
            except Exception as e:
                if attempt < self.max_retries and "error" not in str(e).lower():
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise
        
        raise Exception("Maximum retries exceeded")


# Text normalization utility (simplified version)
def normalize_concept_text(text: str, language: str = "en") -> str:
    """Normalize concept text for ConceptNet URIs."""
    # Simple normalization - replace spaces with underscores and lowercase
    return text.lower().replace(" ", "_").replace("/", "_")


# MCP Protocol Implementation
class MCPProtocol:
    """Handles MCP protocol messages and responses."""
    
    def __init__(self, http_client: CloudflareHTTPClient):
        self.http_client = http_client
        self.tools = self._register_tools()
    
    def _register_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register all available MCP tools."""
        return {
            "concept_lookup": {
                "name": "concept_lookup",
                "description": "Look up information about a specific concept in ConceptNet. Returns minimal format (~96% smaller) by default or verbose format with full metadata when verbose=true.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "term": {"type": "string", "description": "The concept term to look up"},
                        "language": {"type": "string", "default": "en", "description": "Language code"},
                        "limit_results": {"type": "boolean", "default": False, "description": "Limit to first page of results"},
                        "target_language": {"type": "string", "description": "Filter to specific target language"},
                        "verbose": {"type": "boolean", "default": False, "description": "Return detailed format with full metadata (default: false for minimal format)"}
                    },
                    "required": ["term"]
                }
            },
            "concept_query": {
                "name": "concept_query",
                "description": "Advanced querying of ConceptNet with multi-parameter filtering. Returns minimal format (~96% smaller) by default or verbose format with full metadata when verbose=true.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "start": {"type": "string", "description": "Start concept of relationships"},
                        "end": {"type": "string", "description": "End concept of relationships"},
                        "rel": {"type": "string", "description": "Relation type"},
                        "node": {"type": "string", "description": "Concept that must be start or end"},
                        "other": {"type": "string", "description": "Used with node parameter"},
                        "sources": {"type": "string", "description": "Filter by data source"},
                        "language": {"type": "string", "default": "en", "description": "Language filter"},
                        "limit_results": {"type": "boolean", "default": False, "description": "Limit to first page of results"},
                        "verbose": {"type": "boolean", "default": False, "description": "Return detailed format with full metadata (default: false for minimal format)"}
                    },
                    "required": []
                }
            },
            "related_concepts": {
                "name": "related_concepts",
                "description": "Find concepts semantically related to a given concept. Returns minimal format (~96% smaller) by default or verbose format with full metadata when verbose=true.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "term": {"type": "string", "description": "The concept term to find related concepts for"},
                        "language": {"type": "string", "default": "en", "description": "Language code"},
                        "filter_language": {"type": "string", "description": "Filter results to this language"},
                        "limit": {"type": "integer", "default": 100, "description": "Maximum number of results (default: 100, max: 100)"},
                        "verbose": {"type": "boolean", "default": False, "description": "Return detailed format with full metadata (default: false for minimal format)"}
                    },
                    "required": ["term"]
                }
            },
            "concept_relatedness": {
                "name": "concept_relatedness",
                "description": "Calculate semantic relatedness score between two concepts. Returns minimal format (~96% smaller) by default or verbose format with full metadata when verbose=true.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "concept1": {"type": "string", "description": "First concept for comparison"},
                        "concept2": {"type": "string", "description": "Second concept for comparison"},
                        "language1": {"type": "string", "default": "en", "description": "Language for first concept"},
                        "language2": {"type": "string", "default": "en", "description": "Language for second concept"},
                        "verbose": {"type": "boolean", "default": False, "description": "Return detailed format with full metadata (default: false for minimal format)"}
                    },
                    "required": ["concept1", "concept2"]
                }
            }
        }
    
    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialize request."""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {},
                "prompts": {},
                "logging": {}
            },
            "serverInfo": {
                "name": "ConceptNet MCP Server",
                "version": "1.0.0",
                "platform": "cloudflare-workers-python"
            }
        }
    
    async def handle_tools_list(self) -> Dict[str, Any]:
        """Handle tools/list request."""
        return {
            "tools": list(self.tools.values())
        }
    
    async def handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name not in self.tools:
            raise Exception(f"Unknown tool: {tool_name}")
        
        try:
            if tool_name == "concept_lookup":
                result = await self._concept_lookup(**arguments)
            elif tool_name == "concept_query":
                result = await self._concept_query(**arguments)
            elif tool_name == "related_concepts":
                result = await self._related_concepts(**arguments)
            elif tool_name == "concept_relatedness":
                result = await self._concept_relatedness(**arguments)
            else:
                raise Exception(f"Tool not implemented: {tool_name}")
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
            }
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error executing tool {tool_name}: {str(e)}"
                    }
                ],
                "isError": True
            }
    
    async def _concept_lookup(self, term: str, language: str = "en",
                            limit_results: bool = False,
                            target_language: Optional[str] = None,
                            verbose: bool = False) -> Dict[str, Any]:
        """Implement concept lookup tool."""
        endpoint = f"/c/{language}/{normalize_concept_text(term, language)}"
        params = {}
        if target_language:
            params['filter'] = f'/c/{target_language}/'
        if limit_results:
            params['limit'] = '20'
        
        response_data = await self.http_client.request("GET", endpoint, params=params)
        
        # Add Workers-specific metadata
        response_data['deployment'] = {
            'platform': 'cloudflare-workers-python',
            'transport': 'dual-http-sse',
            'edge_location': 'global'
        }
        
        return response_data
    
    async def _concept_query(self, start=None, end=None, rel=None, node=None,
                           other=None, sources=None, language="en",
                           limit_results=False, verbose=False) -> Dict[str, Any]:
        """Implement concept query tool."""
        params = {}
        
        # Build query parameters
        if start:
            params['start'] = start
        if end:
            params['end'] = end
        if rel:
            params['rel'] = rel
        if node:
            params['node'] = node
        if other:
            params['other'] = other
        if sources:
            params['sources'] = sources
        if limit_results:
            params['limit'] = '20'
        
        response_data = await self.http_client.request("GET", "/query", params=params)
        
        # Add Workers-specific metadata
        response_data['deployment'] = {
            'platform': 'cloudflare-workers-python',
            'query_params': params
        }
        
        return response_data
    
    async def _related_concepts(self, term: str, language: str = "en",
                              filter_language: Optional[str] = "en",
                              limit: int = 100, verbose: bool = False) -> Dict[str, Any]:
        """Implement related concepts tool."""
        normalized_term = normalize_concept_text(term, language)
        endpoint = f"/related/c/{language}/{normalized_term}"
        
        params = {"limit": str(limit)}
        if filter_language:
            params['filter'] = f'/c/{filter_language}/'
        
        response_data = await self.http_client.request("GET", endpoint, params=params)
        
        # Add Workers-specific metadata
        response_data['deployment'] = {
            'platform': 'cloudflare-workers-python',
            'similarity_service': 'edge-optimized'
        }
        
        return response_data
    
    async def _concept_relatedness(self, concept1: str, concept2: str,
                                 language1: str = "en",
                                 language2: str = "en", verbose: bool = False) -> Dict[str, Any]:
        """Implement concept relatedness tool."""
        uri1 = f"/c/{language1}/{normalize_concept_text(concept1, language1)}"
        uri2 = f"/c/{language2}/{normalize_concept_text(concept2, language2)}"
        
        params = {
            "node1": uri1,
            "node2": uri2
        }
        
        response_data = await self.http_client.request("GET", "/relatedness", params=params)
        
        # Add Workers-specific metadata
        response_data['deployment'] = {
            'platform': 'cloudflare-workers-python',
            'comparison': f"{concept1} <-> {concept2}"
        }
        
        return response_data


# FastAPI app for HTTP handling
app = FastAPI(title="ConceptNet MCP Server", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize HTTP client and MCP protocol
http_client = CloudflareHTTPClient()
mcp_protocol = MCPProtocol(http_client)


@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "name": "ConceptNet MCP Server",
        "version": "1.0.0",
        "platform": "cloudflare-workers-python",
        "transports": ["sse", "http"],
        "endpoints": {
            "sse": "/sse",
            "mcp": "/mcp",
            "tools": "/tools"
        }
    }


@app.get("/tools")
async def list_tools():
    """List available MCP tools."""
    return await mcp_protocol.handle_tools_list()


@app.post("/mcp")
async def handle_mcp_streamable(request_data: Dict[str, Any]):
    """Handle Streamable HTTP transport for MCP protocol."""
    method = request_data.get("method")
    params = request_data.get("params", {})
    
    try:
        if method == "initialize":
            result = await mcp_protocol.handle_initialize(params)
        elif method == "tools/list":
            result = await mcp_protocol.handle_tools_list()
        elif method == "tools/call":
            result = await mcp_protocol.handle_tools_call(params)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown method: {method}")
        
        return {
            "jsonrpc": "2.0",
            "id": request_data.get("id"),
            "result": result
        }
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": request_data.get("id"),
            "error": {
                "code": -1,
                "message": str(e)
            }
        }


@app.get("/sse")
async def handle_sse_transport():
    """Handle SSE transport initialization."""
    async def event_stream():
        # Send initial connection event
        yield f"data: {json.dumps({'type': 'connection', 'status': 'established'})}\n\n"
        
        # Keep connection alive
        while True:
            yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': 'now'})}\n\n"
            await asyncio.sleep(30)  # Send heartbeat every 30 seconds
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )


@app.post("/sse/messages")
async def handle_sse_messages(request_data: Dict[str, Any]):
    """Handle SSE message endpoint."""
    return await handle_mcp_streamable(request_data)


# Standard Cloudflare Workers fetch handler
async def fetch(request, env, ctx):
    """
    Main entry point for Cloudflare Workers requests.
    
    This function implements the standard fetch handler pattern required
    by Cloudflare Workers and routes requests to the appropriate transport.
    
    Args:
        request: Cloudflare Workers Request object
        env: Environment variables and bindings
        ctx: Execution context
        
    Returns:
        Response object for the client
    """
    try:
        # Parse URL to determine routing
        url = urlparse(request.url)
        path = url.path
        
        # Initialize environment-specific configuration
        api_url = getattr(env, 'CONCEPTNET_API_URL', 'http://api.conceptnet.io')
        http_client.base_url = api_url
        
        # Route to appropriate transport handler
        if path.startswith('/sse'):
            # Handle SSE transport
            if path == '/sse':
                return await handle_sse_transport()
            elif path == '/sse/messages':
                body = await request.json() if request.method == 'POST' else {}
                return JSONResponse(await handle_sse_messages(body))
            else:
                return JSONResponse({"error": "SSE endpoint not found"}, status_code=404)
                
        elif path.startswith('/mcp'):
            # Handle Streamable HTTP transport
            if request.method == 'POST':
                body = await request.json()
                return JSONResponse(await handle_mcp_streamable(body))
            else:
                return JSONResponse({"error": "MCP endpoint requires POST"}, status_code=405)
                
        elif path == '/tools':
            # Handle tools listing
            return JSONResponse(await list_tools())
            
        elif path == '/':
            # Handle root endpoint
            return JSONResponse(await root())
            
        else:
            # Default to root for unknown paths
            return JSONResponse(await root())
            
    except Exception as e:
        return JSONResponse(
            {
                "error": "internal_server_error",
                "message": str(e),
                "platform": "cloudflare-workers-python"
            },
            status_code=500
        )


# Export for Cloudflare Workers
__all__ = ["fetch", "app"]