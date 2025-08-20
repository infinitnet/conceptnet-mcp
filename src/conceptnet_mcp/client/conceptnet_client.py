"""
ConceptNet API HTTP client implementation.

This module provides the main HTTP client for interacting with the ConceptNet API,
including async operations, error handling, retry logic, and response processing.
"""

import asyncio
import json
import time
from typing import Any, Optional, Dict, List, Union
from urllib.parse import urlencode, urljoin

import httpx
from pydantic import ValidationError

from ..models.query import QueryFilters, ConceptLookupQuery, RelatedConceptsQuery, RelatednessQuery
from ..models.response import (
    ConceptResponse, EdgeListResponse, RelatedConceptsResponse, 
    RelatednessResponse, ConceptUriResponse, ErrorResponse
)
from ..utils.exceptions import (
    ConceptNetAPIError, ConceptNotFoundError, RateLimitExceededError,
    InvalidConceptURIError, ValidationError as MCPValidationError
)
from ..utils.logging import get_logger
from ..utils.text_utils import normalize_concept_text
from .pagination import PaginationHandler


class ConceptNetClient:
    """
    Async HTTP client for ConceptNet API.
    
    This client provides comprehensive access to ConceptNet API endpoints with:
    - Async operations using httpx
    - Automatic retry logic with exponential backoff
    - Rate limiting awareness
    - Complete pagination support
    - Comprehensive error handling
    - Integration with Pydantic models
    """
    
    def __init__(
        self,
        base_url: str = "http://api.conceptnet.io",
        timeout_connect: float = 10.0,
        timeout_read: float = 30.0,
        timeout_total: float = 60.0,
        max_retries: int = 3,
        retry_backoff_factor: float = 1.0,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        user_agent: str = "ConceptNet-MCP-Client/1.0",
        max_concurrent_pagination: int = 3,
        max_pages: Optional[int] = None
    ):
        """
        Initialize the ConceptNet API client.
        
        Args:
            base_url: Base URL for the ConceptNet API
            timeout_connect: Connection timeout in seconds
            timeout_read: Read timeout in seconds
            timeout_total: Total request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_backoff_factor: Exponential backoff factor for retries
            max_connections: Maximum number of connections in pool
            max_keepalive_connections: Maximum keep-alive connections
            user_agent: User-Agent header for requests
            max_concurrent_pagination: Maximum concurrent requests for pagination
            max_pages: Maximum pages to fetch during pagination (None for all)
        """
        self.base_url = base_url.rstrip('/')
        self.max_retries = max_retries
        self.retry_backoff_factor = retry_backoff_factor
        self.user_agent = user_agent
        
        # Configure timeouts
        self.timeout = httpx.Timeout(
            connect=timeout_connect,
            read=timeout_read,
            write=timeout_read,
            pool=timeout_total
        )
        
        # Configure connection limits
        self.limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
            keepalive_expiry=5.0
        )
        
        # Initialize pagination handler
        self.pagination_handler = PaginationHandler(
            max_concurrent_requests=max_concurrent_pagination,
            max_pages=max_pages,
            request_timeout=timeout_read,
            inter_request_delay=0.1,  # Respect rate limits
            max_retries_per_page=2
        )
        
        self._client: Optional[httpx.AsyncClient] = None
        self.logger = get_logger("client")
    
    async def __aenter__(self) -> "ConceptNetClient":
        """Async context manager entry."""
        await self._ensure_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
    
    async def _ensure_client(self) -> None:
        """Ensure the httpx client is initialized."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                limits=self.limits,
                headers={"User-Agent": self.user_agent},
                follow_redirects=True
            )
    
    async def close(self) -> None:
        """Close the HTTP client and clean up resources."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make an HTTP request with retry logic and error handling.
        
        Args:
            method: HTTP method
            endpoint: API endpoint path
            params: Query parameters
            **kwargs: Additional httpx request arguments
            
        Returns:
            Parsed JSON response
            
        Raises:
            ConceptNetAPIError: For API errors
            RateLimitExceededError: For rate limit errors
            ConceptNotFoundError: For 404 errors
        """
        await self._ensure_client()
        
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        for attempt in range(self.max_retries + 1):
            try:
                start_time = time.time()
                
                response = await self._client.request(
                    method=method,
                    url=url,
                    params=params,
                    **kwargs
                )
                
                response_time = time.time() - start_time
                
                # Log the request
                self.logger.debug(
                    f"{method} {url} -> {response.status_code} "
                    f"({response_time:.3f}s)"
                )
                
                # Handle different response status codes
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    raise ConceptNotFoundError(f"Resource not found: {url}")
                elif response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    raise RateLimitExceededError(retry_after=retry_after)
                elif 400 <= response.status_code < 500:
                    # Client error - don't retry
                    error_data = self._parse_error_response(response)
                    raise ConceptNetAPIError(
                        f"Client error {response.status_code}: {error_data.get('message', 'Unknown error')}",
                        status_code=response.status_code,
                        response_data=error_data
                    )
                elif 500 <= response.status_code < 600:
                    # Server error - retry
                    if attempt < self.max_retries:
                        wait_time = self.retry_backoff_factor * (2 ** attempt)
                        self.logger.warning(
                            f"Server error {response.status_code}, retrying in {wait_time}s "
                            f"(attempt {attempt + 1}/{self.max_retries + 1})"
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        error_data = self._parse_error_response(response)
                        raise ConceptNetAPIError(
                            f"Server error {response.status_code}: {error_data.get('message', 'Unknown error')}",
                            status_code=response.status_code,
                            response_data=error_data
                        )
                else:
                    raise ConceptNetAPIError(
                        f"Unexpected status code: {response.status_code}",
                        status_code=response.status_code
                    )
                    
            except httpx.ConnectTimeout:
                if attempt < self.max_retries:
                    wait_time = self.retry_backoff_factor * (2 ** attempt)
                    self.logger.warning(
                        f"Connection timeout, retrying in {wait_time}s "
                        f"(attempt {attempt + 1}/{self.max_retries + 1})"
                    )
                    await asyncio.sleep(wait_time)
                    continue
                raise ConceptNetAPIError("Connection timeout after retries")
                
            except httpx.ReadTimeout:
                if attempt < self.max_retries:
                    wait_time = self.retry_backoff_factor * (2 ** attempt)
                    self.logger.warning(
                        f"Read timeout, retrying in {wait_time}s "
                        f"(attempt {attempt + 1}/{self.max_retries + 1})"
                    )
                    await asyncio.sleep(wait_time)
                    continue
                raise ConceptNetAPIError("Read timeout after retries")
                
            except httpx.NetworkError as e:
                if attempt < self.max_retries:
                    wait_time = self.retry_backoff_factor * (2 ** attempt)
                    self.logger.warning(
                        f"Network error: {e}, retrying in {wait_time}s "
                        f"(attempt {attempt + 1}/{self.max_retries + 1})"
                    )
                    await asyncio.sleep(wait_time)
                    continue
                raise ConceptNetAPIError(f"Network error after retries: {e}")
                
            except RateLimitExceededError:
                # Don't retry rate limit errors immediately
                raise
                
        # Should never reach here
        raise ConceptNetAPIError("Maximum retries exceeded")
    
    def _parse_error_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Parse error response from API."""
        try:
            return response.json()
        except (json.JSONDecodeError, ValueError):
            return {"message": response.text or "Unknown error"}
    
    async def get_concept(
        self,
        term: str,
        language: str = "en",
        get_all_pages: bool = True,
        target_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get concept data with optional complete pagination.
        
        Args:
            term: The concept term to look up
            language: Language code for the concept
            get_all_pages: Whether to fetch all pages of results
            target_language: Filter results to specific language
            
        Returns:
            Complete concept data with all edges
            
        Raises:
            ConceptNotFoundError: If concept doesn't exist
            ConceptNetAPIError: For API errors
        """
        # Create and validate query
        try:
            query = ConceptLookupQuery(
                term=term,
                language=language,
                target_language=target_language,
                limit_results=not get_all_pages
            )
        except ValidationError as e:
            raise MCPValidationError("term", term, str(e))
        
        concept_uri = query.to_concept_uri()
        self.logger.info(f"Fetching concept: {concept_uri}")
        
        # Make initial request
        endpoint = f"/c/{language}/{normalize_concept_text(term, language)}"
        params = {}
        if target_language:
            params['filter'] = f'/c/{target_language}'
        
        response_data = await self._make_request("GET", endpoint, params=params)
        
        if not get_all_pages:
            return response_data
        
        # Use pagination handler for complete results
        try:
            complete_response = await self.pagination_handler.get_all_pages(
                self._client, response_data
            )
            
            total_edges = len(complete_response.get('edges', []))
            self.logger.info(f"Retrieved {total_edges} edges for concept {concept_uri}")
            return complete_response
            
        except Exception as e:
            self.logger.warning(f"Pagination failed for {concept_uri}: {e}, returning partial results")
            return response_data
    
    async def query_concepts(
        self,
        filters: QueryFilters,
        get_all_pages: bool = True,
        target_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Advanced filtering with query parameters.
        
        Args:
            filters: QueryFilters instance with search criteria
            get_all_pages: Whether to fetch all pages of results
            target_language: Filter results to specific language
            
        Returns:
            Query results matching the filters
            
        Raises:
            ConceptNetAPIError: For API errors
        """
        self.logger.info(f"Querying concepts with filters: {filters}")
        
        # Convert to query parameters
        params = filters.to_query_params()
        if target_language:
            # Add language filter to existing params
            for key in ['start', 'end', 'node', 'other']:
                if key in params and not params[key].startswith('/c/' + target_language + '/'):
                    if params[key].startswith('/c/'):
                        continue  # Keep as-is if already language-specific
        
        response_data = await self._make_request("GET", "/query", params=params)
        
        if not get_all_pages:
            return response_data
        
        # Use pagination handler for complete results
        try:
            complete_response = await self.pagination_handler.get_all_pages(
                self._client, response_data
            )
            
            total_edges = len(complete_response.get('edges', []))
            self.logger.info(f"Query returned {total_edges} edges")
            return complete_response
            
        except Exception as e:
            self.logger.warning(f"Pagination failed for query: {e}, returning partial results")
            return response_data
    
    async def get_related(
        self,
        term: str,
        language: str = "en",
        filter_language: Optional[str] = "en",
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Find semantically similar concepts.
        
        Args:
            term: The concept term to find relations for
            language: Language of the input term
            filter_language: Filter results to specific language
            limit: Maximum number of related concepts to return
            
        Returns:
            Related concepts with similarity scores
            
        Raises:
            ConceptNetAPIError: For API errors
        """
        try:
            query = RelatedConceptsQuery(
                term=term,
                language=language,
                filter_language=filter_language,
                limit=limit
            )
        except ValidationError as e:
            raise MCPValidationError("term", term, str(e))
        
        concept_uri = query.to_concept_uri()
        self.logger.info(f"Finding related concepts for: {concept_uri}")
        
        endpoint = f"/related{concept_uri}"
        params = {"limit": str(limit)}
        if filter_language:
            params['filter'] = f'/c/{filter_language}'
        
        response_data = await self._make_request("GET", endpoint, params=params)
        
        self.logger.info(f"Found {len(response_data.get('related', []))} related concepts")
        return response_data
    
    async def get_relatedness(
        self,
        concept1: str,
        concept2: str,
        language1: str = "en",
        language2: str = "en"
    ) -> Dict[str, Any]:
        """
        Calculate similarity score between two concepts.
        
        Args:
            concept1: First concept term
            concept2: Second concept term
            language1: Language of the first concept
            language2: Language of the second concept
            
        Returns:
            Relatedness score and metadata
            
        Raises:
            ConceptNetAPIError: For API errors
        """
        try:
            query = RelatednessQuery(
                concept1=concept1,
                concept2=concept2,
                language1=language1,
                language2=language2
            )
        except ValidationError as e:
            raise MCPValidationError("concepts", f"{concept1}, {concept2}", str(e))
        
        uri1, uri2 = query.to_concept_uris()
        self.logger.info(f"Calculating relatedness: {uri1} <-> {uri2}")
        
        endpoint = f"/relatedness"
        params = {
            "node1": uri1,
            "node2": uri2
        }
        
        response_data = await self._make_request("GET", endpoint, params=params)
        
        score = response_data.get('value', 0.0)
        self.logger.info(f"Relatedness score: {score:.3f}")
        return response_data
    
    async def get_uri(self, text: str, language: str = "en") -> Dict[str, Any]:
        """
        Convert text to ConceptNet URI format.
        
        Args:
            text: Text to convert to URI
            language: Language code for the text
            
        Returns:
            URI generation result
            
        Raises:
            InvalidConceptURIError: For invalid text input
        """
        if not text or not text.strip():
            raise InvalidConceptURIError(text, "Non-empty text required")
        
        # Normalize the text
        normalized = normalize_concept_text(text, language)
        uri = f"/c/{language}/{normalized}"
        
        self.logger.debug(f"Generated URI: '{text}' -> {uri}")
        
        return {
            "text": text,
            "uri": uri,
            "language": language
        }
    
    async def health_check(self) -> bool:
        """
        Check if the ConceptNet API is accessible.
        
        Returns:
            True if API is healthy, False otherwise
        """
        try:
            # Simple request to check API health
            response_data = await self._make_request("GET", "/c/en/test")
            return True
        except Exception as e:
            self.logger.warning(f"Health check failed: {e}")
            return False