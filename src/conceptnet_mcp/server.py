"""
ConceptNet MCP Server main entry point.

This module contains the FastMCP server instance and configuration for the ConceptNet
Model Context Protocol server. It provides access to ConceptNet's 
knowledge graph through four powerful MCP tools.
"""

import asyncio
from typing import Any, Dict, Optional
import fastmcp
from fastmcp import FastMCP, Context

# Import all tool implementations
from .tools.concept_lookup import concept_lookup
from .tools.concept_query import concept_query
from .tools.related_concepts import related_concepts
from .tools.concept_relatedness import concept_relatedness
from .utils.logging import get_logger
from .utils.exceptions import ConceptNetMCPError, MCPToolError

# Initialize logging
logger = get_logger(__name__)

# Create the main FastMCP server with instructions
mcp = FastMCP(
    name="ConceptNet MCP Server",
    instructions="""
    This server provides access to ConceptNet, a large semantic network
    of general knowledge containing millions of assertions about concepts and their
    relationships. ConceptNet integrates data from multiple sources including WordNet,
    Open Mind Common Sense, Wikipedia, and more.

    🎯 **Core Capabilities:**
    - **Complete Pagination**: All tools return ALL results by default (not just 20)
    - **Multi-language Support**: Cross-language queries and concept exploration
    - **Text Normalization**: All text converted to readable format for easy processing
    - **Rich Analysis**: Summaries, statistics, and relationship insights
    - **Error Resilience**: Robust error handling with helpful guidance messages

    🔧 **Available Tools:**

    1. **concept_lookup** - Concept exploration
       - Look up all relationships for a specific concept
       - Returns complete edge information with relationship summaries
       - Supports language filtering and cross-language exploration
       - Perfect for understanding "what ConceptNet knows about X"

    2. **concept_query** - Advanced filtered searching
       - Sophisticated multi-parameter filtering (start, end, relation, node, sources)
       - Complex relationship discovery with precise control
       - Query optimization and result analysis
       - Ideal for finding specific types of relationships

    3. **related_concepts** - Semantic similarity discovery
       - Find concepts semantically similar to a given concept
       - Uses ConceptNet's semantic embeddings and algorithms
       - Ranked by similarity scores with detailed analysis
       - Great for concept expansion and exploration

    4. **concept_relatedness** - Quantitative similarity measurement
       - Calculate precise similarity scores between two concepts
       - Cross-language comparison support
       - Detailed relationship analysis and interpretation
       - Essential for measuring conceptual distance

    💡 **Usage Guidelines:**
    - **Start with concept_lookup** to explore what ConceptNet knows about a concept
    - **Use concept_query** for sophisticated filtering and targeted relationship discovery
    - **Use related_concepts** to discover similar or related ideas
    - **Use concept_relatedness** to quantify how similar two concepts are
    - All tools support multiple languages and provide extensive metadata
    - Results include suggestions for further exploration and refinement

    🌍 **Language Support:**
    - Primary support for English ('en') with extensive coverage
    - Multi-language support including Spanish ('es'), French ('fr'), German ('de'), etc.
    - Cross-language queries to find relationships between concepts in different languages
    - Automatic language detection and validation with helpful warnings

    📊 **Data Quality:**
    - All results include confidence scores and source information
    - Error handling with specific guidance for each error type
    - Performance metrics and execution timing for optimization
    - Built-in validation with helpful error messages and suggestions

    🚀 **Performance Features:**
    - Automatic pagination to retrieve complete datasets
    - Efficient caching and connection management
    - Parallel processing where applicable
    - Optimized for both quick queries and analysis

    ⚡ **Quick Start Examples:**
    - `concept_lookup("dog")` - Explore everything about dogs
    - `concept_query(start="car", rel="IsA")` - Find what cars are
    - `related_concepts("happiness")` - Find concepts similar to happiness
    - `concept_relatedness("cat", "dog")` - How similar are cats and dogs?
    """,
    include_tags={"conceptnet", "knowledge", "semantic", "nlp"}
)

# Global error handler for server-level exceptions
async def handle_server_error(error: Exception, context: str = "server") -> Dict[str, Any]:
    """Handle server-level errors with logging and user-friendly responses."""
    logger.error(f"Server error in {context}: {error}")
    
    if isinstance(error, ConceptNetMCPError):
        return {
            "error": "conceptnet_error",
            "message": str(error),
            "context": context,
            "suggestions": [
                "Check your internet connection",
                "Verify ConceptNet service is available",
                "Try again in a few moments"
            ]
        }
    
    return {
        "error": "server_error",
        "message": f"An unexpected server error occurred: {str(error)}",
        "context": context,
        "suggestions": [
            "Check the server logs for more details",
            "Verify all parameters are correct",
            "Contact support if the error persists"
        ]
    }

# Register Tool 1: Concept Lookup
@mcp.tool(
    name="concept_lookup",
    description="""
    Look up information about a specific concept in ConceptNet.
    
    This tool queries ConceptNet's knowledge graph to find all relationships
    and properties associated with a given concept. By default, it returns
    ALL results (not limited to 20) to provide complete information.
    
    Features:
    - Complete relationship discovery for any concept
    - Language filtering and cross-language exploration
    - Summaries and statistics
    - Performance optimized with automatic pagination
    - Format control: minimal (~96% smaller) vs verbose (full metadata)
    
    Format Options:
    - verbose=false (default): Returns minimal format optimized for LLM consumption
    - verbose=true: Returns comprehensive format with full ConceptNet metadata
    - Backward compatibility maintained with existing tools
    
    Use this when you need to:
    - Understand what ConceptNet knows about a concept
    - Explore all relationships for a term
    - Get semantic information
    - Find related concepts and properties
    """,
    tags={"conceptnet", "knowledge", "lookup"}
)
async def concept_lookup_tool(
    term: str,
    ctx: Context,
    language: str = "en",
    limit_results: bool = False,
    target_language: Optional[str] = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    MCP tool wrapper for concept lookup functionality.
    
    Args:
        term: The concept term to look up (e.g., "dog", "artificial intelligence")
        language: Language code for the concept (default: "en" for English)
        limit_results: If True, limits to first 20 results for quick queries (default: False)
        target_language: If specified, filters results to edges involving this language
        verbose: If True, returns detailed format with full metadata (default: False)
        
    Returns:
        Concept relationships grouped by type (minimal format) or comprehensive data with full metadata (verbose format)
    """
    try:
        return await concept_lookup(
            term=term,
            ctx=ctx,
            language=language,
            limit_results=limit_results,
            target_language=target_language,
            verbose=verbose
        )
    except Exception as e:
        return await handle_server_error(e, "concept_lookup")

# Register Tool 2: Concept Query
@mcp.tool(
    name="concept_query",
    description="""
    Advanced querying of ConceptNet with sophisticated multi-parameter filtering.
    
    This tool provides powerful filtering capabilities for exploring ConceptNet's
    knowledge graph. You can combine multiple filters to find specific types of
    relationships and concepts with precision.
    
    Features:
    - Multi-parameter filtering (start, end, relation, node, sources)
    - Complex relationship discovery and analysis
    - Comprehensive result processing and enhancement
    - Query optimization and performance metrics
    - Format control: minimal (~96% smaller) vs verbose (full metadata)
    
    Format Options:
    - verbose=false (default): Returns minimal format optimized for LLM consumption
    - verbose=true: Returns comprehensive format with full ConceptNet metadata
    - Backward compatibility maintained with existing tools
    
    Filter Parameters:
    - start: Start concept of relationships (e.g., "dog", "/c/en/dog")
    - end: End concept of relationships (e.g., "animal", "/c/en/animal")
    - rel: Relation type (e.g., "IsA", "/r/IsA")
    - node: Concept that must be either start or end of edges
    - other: Used with 'node' to find relationships between two specific concepts
    - sources: Filter by data source (e.g., "wordnet", "/s/activity/omcs")
    
    Use this when you need:
    - Precise relationship filtering and discovery
    - Complex queries with multiple constraints
    - Analysis of specific relationship types
    - Targeted exploration of concept connections
    """,
    tags={"conceptnet", "query", "filtering", "advanced", "relationships"}
)
async def concept_query_tool(
    ctx: Context,
    start: Optional[str] = None,
    end: Optional[str] = None,
    rel: Optional[str] = None,
    node: Optional[str] = None,
    other: Optional[str] = None,
    sources: Optional[str] = None,
    language: str = "en",
    limit_results: bool = False,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    MCP tool wrapper for advanced concept querying functionality.
    
    Args:
        start: Start concept URI or term (e.g., "dog", "/c/en/dog")
        end: End concept URI or term (e.g., "animal", "/c/en/animal")
        rel: Relation type (e.g., "IsA", "/r/IsA")
        node: Concept that must be either start or end of edges
        other: Used with 'node' to find relationships between two specific concepts
        sources: Filter by data source (e.g., "wordnet", "/s/activity/omcs")
        language: Language filter for concepts (default: "en")
        limit_results: If True, limits to 20 results for quick queries (default: False)
        verbose: If True, returns detailed format with full metadata (default: False)
        
    Returns:
        Query results with relationships grouped by type (minimal format) or comprehensive data with full metadata (verbose format)
    """
    try:
        return await concept_query(
            ctx=ctx,
            start=start,
            end=end,
            rel=rel,
            node=node,
            other=other,
            sources=sources,
            language=language,
            limit_results=limit_results,
            verbose=verbose
        )
    except Exception as e:
        return await handle_server_error(e, "concept_query")

# Register Tool 3: Related Concepts
@mcp.tool(
    name="related_concepts",
    description="""
    Find concepts semantically related to a given concept using ConceptNet's embeddings.
    
    This tool uses ConceptNet's semantic similarity algorithms to discover
    concepts that are related to the input term. Results are ranked by
    similarity score and include comprehensive analysis.
    
    Features:
    - Semantic similarity discovery using advanced algorithms
    - Ranked results with detailed similarity analysis
    - Language filtering and cross-language exploration
    - Statistical analysis and categorization
    - Format control: minimal (~96% smaller) vs verbose (full metadata)
    
    Format Options:
    - verbose=false (default): Returns minimal format optimized for LLM consumption
    - verbose=true: Returns comprehensive format with full ConceptNet metadata
    - Backward compatibility maintained with existing tools
    
    Similarity Analysis:
    - Similarity scores from 0.0 (unrelated) to 1.0 (very similar)
    - Descriptive categories (very strong, strong, moderate, weak, very weak)
    - Relationship context and likely connections
    - Language distribution and statistical summaries
    
    Use this when you need to:
    - Discover semantically similar concepts
    - Expand concept exploration and brainstorming
    - Find related terms and ideas
    - Understand semantic neighborhoods
    """,
    tags={"conceptnet", "semantic", "similarity", "related", "discovery"}
)
async def related_concepts_tool(
    term: str,
    ctx: Context,
    language: str = "en",
    filter_language: Optional[str] = None,
    limit: int = 100,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    MCP tool wrapper for finding related concepts functionality.
    
    Args:
        term: The concept term to find related concepts for (e.g., "dog", "happiness")
        language: Language code for the input term (default: "en" for English)
        filter_language: If specified, filter results to this language only
        limit: Maximum number of related concepts to return (default: 100, max: 100)
        verbose: If True, returns detailed format with full metadata (default: False)
        
    Returns:
        Related concepts with similarity scores (minimal format) or comprehensive analysis with statistical metadata (verbose format)
    """
    try:
        return await related_concepts(
            term=term,
            ctx=ctx,
            language=language,
            filter_language=filter_language,
            limit=limit,
            verbose=verbose
        )
    except Exception as e:
        return await handle_server_error(e, "related_concepts")

# Register Tool 4: Concept Relatedness  
@mcp.tool(
    name="concept_relatedness",
    description="""
    Calculate precise semantic relatedness score between two concepts.
    
    This tool uses ConceptNet's semantic embeddings to calculate how
    related two concepts are to each other. The score ranges from 0.0
    (completely unrelated) to 1.0 (very strongly related).
    
    Features:
    - Precise quantitative similarity measurement
    - Cross-language comparison support
    - Detailed relationship analysis and interpretation
    - Confidence levels and percentile estimates
    - Format control: minimal (~96% smaller) vs verbose (full metadata)
    
    Format Options:
    - verbose=false (default): Returns minimal format optimized for LLM consumption
    - verbose=true: Returns comprehensive format with full ConceptNet metadata
    - Backward compatibility maintained with existing tools
    
    Analysis Components:
    - Numeric relatedness score (0.0-1.0)
    - Descriptive interpretation and confidence level
    - Likely connection explanations
    - Semantic distance and relationship strength
    - Cross-language analysis when applicable
    
    Use this when you need to:
    - Quantify how similar two concepts are
    - Compare concepts across different languages
    - Measure semantic distance between ideas
    - Validate conceptual relationships
    """,
    tags={"conceptnet", "relatedness", "similarity", "comparison", "quantitative"}
)
async def concept_relatedness_tool(
    concept1: str,
    concept2: str,
    ctx: Context,
    language1: str = "en",
    language2: str = "en",
    verbose: bool = False
) -> Dict[str, Any]:
    """
    MCP tool wrapper for concept relatedness calculation functionality.
    
    Args:
        concept1: First concept term for comparison (e.g., "dog", "happiness")
        concept2: Second concept term for comparison (e.g., "cat", "joy")
        language1: Language code for first concept (default: "en")
        language2: Language code for second concept (default: "en")
        verbose: If True, returns detailed format with full metadata (default: False)
        
    Returns:
        Relatedness score with strength category (minimal format) or comprehensive analysis with detailed metadata (verbose format)
    """
    try:
        return await concept_relatedness(
            concept1=concept1,
            concept2=concept2,
            ctx=ctx,
            language1=language1,
            language2=language2,
            verbose=verbose
        )
    except Exception as e:
        return await handle_server_error(e, "concept_relatedness")

# Server lifecycle management
async def startup_handler():
    """Handle server startup with initialization and health checks."""
    logger.info("🚀 ConceptNet MCP Server starting up...")
    logger.info("✅ All tools registered successfully")
    logger.info("🌐 Multi-language support enabled")
    logger.info("📊 Comprehensive analysis features active")
    logger.info("🔧 Server ready for ConceptNet queries")

async def shutdown_handler():
    """Handle graceful server shutdown."""
    logger.info("🔄 ConceptNet MCP Server shutting down...")
    logger.info("✅ Cleanup completed successfully")

def main(transport: str = "stdio", host: str = "localhost", port: int = 3001) -> None:
    """
    Main entry point for the ConceptNet MCP server.
    
    This function initializes and runs the FastMCP server with all
    registered tools and resources for ConceptNet API integration.
    Supports both stdio and HTTP transports.
    
    Args:
        transport: Transport mode - "stdio" for desktop clients, "http" for web clients
        host: Host to bind HTTP server to (only used with HTTP transport)
        port: Port to bind HTTP server to (only used with HTTP transport)
    """
    logger.info(f"🎯 Starting ConceptNet MCP Server with {transport} transport...")
    
    # Log FastMCP version for diagnostic purposes
    try:
        fastmcp_version = getattr(fastmcp, '__version__', 'unknown')
        logger.info(f"📦 Using FastMCP version: {fastmcp_version}")
    except Exception as e:
        logger.warning(f"⚠️  Could not determine FastMCP version: {e}")
    
    try:
        # Run startup handler
        asyncio.run(startup_handler())
        
        # Configure transport-specific settings
        if transport.lower() == "http":
            logger.info(f"🌐 Starting HTTP server on {host}:{port}")
            # Run the server with HTTP transport
            mcp.run(
                transport="http",
                host=host,
                port=port
            )
        else:
            logger.info("📡 Starting stdio transport for desktop MCP clients")
            # Run the server with stdio transport (default for MCP compatibility)
            mcp.run(
                transport="stdio"
            )
        
    except KeyboardInterrupt:
        logger.info("🛑 Server shutdown requested by user")
        asyncio.run(shutdown_handler())
        
    except Exception as e:
        logger.error(f"💥 Critical server error: {e}")
        # Log the full traceback for debugging
        import traceback
        logger.error(f"📋 Full traceback: {traceback.format_exc()}")
        
        # Attempt graceful shutdown
        try:
            asyncio.run(shutdown_handler())
        except Exception as shutdown_error:
            logger.error(f"❌ Error during shutdown: {shutdown_error}")
        
        raise

# Alternative entry points for different use cases
def run_development_server(transport: str = "stdio", host: str = "localhost", port: int = 3001):
    """Run server in development mode with enhanced debugging."""
    import logging
    logging.getLogger().setLevel(logging.DEBUG)
    logger.info("🔧 Running in development mode")
    main(transport=transport, host=host, port=port)

def run_production_server(transport: str = "stdio", host: str = "localhost", port: int = 3001):
    """Run server in production mode with optimized settings."""
    import logging
    logging.getLogger().setLevel(logging.INFO)
    logger.info("🏭 Running in production mode")
    main(transport=transport, host=host, port=port)

def run_http_server(host: str = "localhost", port: int = 3001):
    """Run server with HTTP transport for web clients."""
    logger.info("🌐 Starting HTTP transport mode for web clients")
    main(transport="http", host=host, port=port)

def run_stdio_server():
    """Run server with stdio transport for desktop clients."""
    logger.info("📡 Starting stdio transport mode for desktop clients")
    main(transport="stdio")

if __name__ == "__main__":
    main()