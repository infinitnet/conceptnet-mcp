"""
Pagination handling utilities for ConceptNet API responses.

This module provides comprehensive pagination handling for the ConceptNet API,
including automatic page traversal, parallel fetching, result aggregation,
and memory-efficient processing for large result sets.
"""

import asyncio
import time
from typing import Any, Optional, List, Dict, AsyncGenerator, Union, Tuple
from urllib.parse import urlparse, parse_qs
from dataclasses import dataclass
from copy import deepcopy

import httpx

from ..utils.logging import get_logger
from ..utils.exceptions import ConceptNetAPIError, PaginationError


@dataclass
class PaginationInfo:
    """
    Container for pagination metadata.
    
    This class holds information about the current page,
    total results, and navigation links for paginated responses.
    """
    
    current_page_id: str
    next_page_url: Optional[str] = None
    previous_page_url: Optional[str] = None
    paginated_property: str = "edges"
    has_pagination: bool = False
    estimated_total_pages: Optional[int] = None
    current_page_size: int = 0


class PaginationHandler:
    """
    Handler for managing paginated ConceptNet API responses.
    
    This class provides comprehensive utilities for iterating through
    paginated results, aggregating data across multiple pages, and
    optimizing performance through parallel fetching.
    
    Key Features:
    - Complete result fetching - Get all results, not just first 20
    - Parallel processing - Fetch multiple pages concurrently when safe
    - Memory efficiency - Handle large datasets without excessive memory usage
    - Error resilience - Graceful handling of partial failures
    - Progress tracking - Logging and status updates for long operations
    - Rate limiting respect - Don't overwhelm the ConceptNet API
    - Configurable limits - Max pages, max concurrent requests, timeouts
    """
    
    def __init__(
        self,
        max_concurrent_requests: int = 3,
        max_pages: Optional[int] = None,
        request_timeout: float = 30.0,
        inter_request_delay: float = 0.1,
        max_retries_per_page: int = 2,
        memory_limit_mb: Optional[int] = None
    ):
        """
        Initialize the pagination handler.
        
        Args:
            max_concurrent_requests: Maximum number of concurrent page requests (default: 3)
            max_pages: Maximum number of pages to retrieve (None for all)
            request_timeout: Timeout for individual page requests in seconds
            inter_request_delay: Delay between requests to respect rate limits
            max_retries_per_page: Maximum retries for failed page requests
            memory_limit_mb: Optional memory usage warning threshold in MB
        """
        self.max_concurrent_requests = max_concurrent_requests
        self.max_pages = max_pages
        self.request_timeout = request_timeout
        self.inter_request_delay = inter_request_delay
        self.max_retries_per_page = max_retries_per_page
        self.memory_limit_mb = memory_limit_mb
        
        self.logger = get_logger("pagination")
        self._semaphore = asyncio.Semaphore(max_concurrent_requests)
        
    async def get_all_pages(
        self,
        client: httpx.AsyncClient,
        initial_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Fetch all pages of results from an initial ConceptNet API response.
        
        This method automatically follows pagination links and aggregates
        all results into a single response structure.
        
        Args:
            client: httpx AsyncClient instance for making requests
            initial_response: The initial API response containing pagination info
            
        Returns:
            Complete response with all paginated results merged
            
        Raises:
            PaginationError: If pagination fails or response structure is invalid
            ConceptNetAPIError: For API-related errors
        """
        try:
            # Validate initial response structure
            self.validate_pagination_structure(initial_response)
            
            # Detect pagination information
            pagination_info = self.detect_pagination_info(initial_response)
            
            if not pagination_info.has_pagination:
                self.logger.debug("Response is not paginated, returning as-is")
                return initial_response
            
            self.logger.info(
                f"Starting pagination: {pagination_info.paginated_property} "
                f"(estimated {pagination_info.estimated_total_pages or 'unknown'} pages)"
            )
            
            # Collect all page URLs to fetch
            page_urls = []
            current_url = pagination_info.next_page_url
            page_count = 1
            
            while current_url and (not self.max_pages or page_count < self.max_pages):
                page_urls.append(current_url)
                page_count += 1
                
                # For safety, we peek ahead to get the next URL, but we'll fetch in parallel
                if len(page_urls) >= 10:  # Collect URLs in batches to avoid infinite loops
                    break
                    
                # Quick peek to get next URL (we'll fetch properly later)
                try:
                    peek_response = await self._fetch_page_with_retry(client, current_url)
                    current_url = self.extract_next_page_url(peek_response)
                    if current_url in page_urls:  # Prevent circular references
                        break
                except Exception as e:
                    self.logger.warning(f"Failed to peek ahead for URL discovery: {e}")
                    break
            
            if not page_urls:
                self.logger.debug("No additional pages to fetch")
                return initial_response
            
            # Limit URLs if max_pages is set
            if self.max_pages:
                max_additional_pages = self.max_pages - 1  # -1 for initial response
                page_urls = page_urls[:max_additional_pages]
            
            self.logger.info(f"Fetching {len(page_urls)} additional pages")
            
            # Fetch all pages in parallel
            additional_responses = await self.fetch_pages_parallel(client, page_urls)
            
            # Merge all responses
            all_responses = [initial_response] + additional_responses
            merged_response = self.merge_paginated_results(all_responses)
            
            total_items = len(merged_response.get(pagination_info.paginated_property, []))
            self.logger.info(f"Pagination complete: {total_items} total items collected")
            
            return merged_response
            
        except Exception as e:
            if isinstance(e, (PaginationError, ConceptNetAPIError)):
                raise
            raise PaginationError(f"Pagination failed: {str(e)}")
    
    def extract_next_page_url(self, response: Dict[str, Any]) -> Optional[str]:
        """
        Extract next page URL from a ConceptNet API response.
        
        Args:
            response: API response potentially containing pagination metadata
            
        Returns:
            Next page URL if available, None otherwise
        """
        try:
            view = response.get('view', {})
            next_page = view.get('nextPage')
            
            if next_page:
                self.logger.debug(f"Found next page URL: {next_page}")
                return next_page
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to extract next page URL: {e}")
            return None
    
    def merge_paginated_results(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge multiple paginated responses into a single response.
        
        This method combines the paginated property (usually 'edges') from
        all responses while preserving the original response structure.
        
        Args:
            responses: List of API responses to merge
            
        Returns:
            Merged response with all paginated data combined
            
        Raises:
            PaginationError: If responses cannot be merged
        """
        if not responses:
            raise PaginationError("No responses provided for merging")
        
        if len(responses) == 1:
            return responses[0]
        
        try:
            # Use the first response as the base structure
            merged_response = deepcopy(responses[0])
            
            # Detect the paginated property from the first response
            pagination_info = self.detect_pagination_info(responses[0])
            paginated_property = pagination_info.paginated_property
            
            # Initialize the merged collection
            merged_items = merged_response.get(paginated_property, [])
            
            # Merge items from all subsequent responses
            for response in responses[1:]:
                items = response.get(paginated_property, [])
                merged_items.extend(items)
            
            # Update the merged response
            merged_response[paginated_property] = merged_items
            
            # Remove pagination metadata since we've fetched all pages
            if 'view' in merged_response:
                del merged_response['view']
            
            self.logger.debug(
                f"Merged {len(responses)} responses: "
                f"{len(merged_items)} total {paginated_property}"
            )
            
            return merged_response
            
        except Exception as e:
            raise PaginationError(f"Failed to merge responses: {str(e)}")
    
    def detect_pagination_info(self, response: Dict[str, Any]) -> PaginationInfo:
        """
        Detect if pagination is available and extract metadata.
        
        Args:
            response: API response to analyze
            
        Returns:
            PaginationInfo object with detected metadata
        """
        view = response.get('view', {})
        
        if not view:
            # No pagination metadata
            return PaginationInfo(
                current_page_id=response.get('@id', ''),
                has_pagination=False
            )
        
        current_page_id = view.get('@id', response.get('@id', ''))
        next_page_url = view.get('nextPage')
        previous_page_url = view.get('previousPage')
        paginated_property = view.get('paginatedProperty', 'edges')
        
        # Estimate total pages if possible
        estimated_total_pages = self.estimate_total_pages(response)
        
        # Current page size
        current_page_size = len(response.get(paginated_property, []))
        
        pagination_info = PaginationInfo(
            current_page_id=current_page_id,
            next_page_url=next_page_url,
            previous_page_url=previous_page_url,
            paginated_property=paginated_property,
            has_pagination=bool(next_page_url or previous_page_url),
            estimated_total_pages=estimated_total_pages,
            current_page_size=current_page_size
        )
        
        self.logger.debug(f"Detected pagination info: {pagination_info}")
        return pagination_info
    
    def estimate_total_pages(self, response: Dict[str, Any]) -> Optional[int]:
        """
        Estimate total pages if possible from response metadata.
        
        Args:
            response: API response to analyze
            
        Returns:
            Estimated total pages, or None if cannot determine
        """
        try:
            view = response.get('view', {})
            current_page_id = view.get('@id', '')
            
            if not current_page_id:
                return None
            
            # Try to extract offset and limit from current page URL
            parsed_url = urlparse(current_page_id)
            query_params = parse_qs(parsed_url.query)
            
            offset = int(query_params.get('offset', [0])[0])
            limit = int(query_params.get('limit', [20])[0])
            
            current_page_size = len(response.get(view.get('paginatedProperty', 'edges'), []))
            
            # If we got fewer items than the limit, we're likely on the last page
            if current_page_size < limit:
                current_page_number = (offset // limit) + 1
                return current_page_number
            
            # Otherwise, we can't reliably estimate without total count
            return None
            
        except (ValueError, KeyError, ZeroDivisionError):
            return None
    
    async def fetch_pages_parallel(
        self,
        client: httpx.AsyncClient,
        page_urls: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Fetch multiple pages concurrently with controlled concurrency.
        
        Args:
            client: httpx AsyncClient instance
            page_urls: List of page URLs to fetch
            
        Returns:
            List of responses in the same order as input URLs
            
        Raises:
            PaginationError: If too many pages fail to fetch
        """
        if not page_urls:
            return []
        
        self.logger.info(f"Fetching {len(page_urls)} pages in parallel (max {self.max_concurrent_requests} concurrent)")
        
        # Create tasks for all pages
        tasks = []
        for i, url in enumerate(page_urls):
            task = self._fetch_page_with_semaphore(client, url, i)
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle errors
        responses = []
        failed_pages = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Failed to fetch page {i+1}: {result}")
                failed_pages.append((i, page_urls[i], result))
            else:
                responses.append(result)
        
        # Check if we have enough successful results
        success_rate = len(responses) / len(page_urls)
        if success_rate < 0.5:  # Less than 50% success
            raise PaginationError(
                f"Too many pages failed to fetch ({len(failed_pages)}/{len(page_urls)})",
                partial_results=responses
            )
        
        if failed_pages:
            self.logger.warning(
                f"Some pages failed to fetch ({len(failed_pages)}/{len(page_urls)}), "
                f"continuing with partial results"
            )
        
        return responses
    
    async def _fetch_page_with_semaphore(
        self,
        client: httpx.AsyncClient,
        url: str,
        page_index: int
    ) -> Dict[str, Any]:
        """
        Fetch a single page with semaphore-controlled concurrency.
        
        Args:
            client: httpx AsyncClient instance
            url: Page URL to fetch
            page_index: Index of this page (for logging)
            
        Returns:
            Page response data
        """
        async with self._semaphore:
            # Add delay between requests to respect rate limits
            if self.inter_request_delay > 0:
                await asyncio.sleep(self.inter_request_delay)
            
            return await self._fetch_page_with_retry(client, url, page_index)
    
    async def _fetch_page_with_retry(
        self,
        client: httpx.AsyncClient,
        url: str,
        page_index: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Fetch a single page with retry logic.
        
        Args:
            client: httpx AsyncClient instance
            url: Page URL to fetch
            page_index: Optional page index for logging
            
        Returns:
            Page response data
            
        Raises:
            ConceptNetAPIError: If all retries fail
        """
        page_info = f"page {page_index+1}" if page_index is not None else "page"
        
        for attempt in range(self.max_retries_per_page + 1):
            try:
                start_time = time.time()
                
                response = await client.get(url, timeout=self.request_timeout)
                response.raise_for_status()
                
                response_time = time.time() - start_time
                self.logger.debug(f"Fetched {page_info} in {response_time:.3f}s")
                
                return response.json()
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code in [404, 429]:
                    # Don't retry client errors or rate limits
                    raise ConceptNetAPIError(
                        f"HTTP {e.response.status_code} for {page_info}",
                        status_code=e.response.status_code
                    )
                
                if attempt < self.max_retries_per_page:
                    wait_time = 2 ** attempt  # Exponential backoff
                    self.logger.warning(
                        f"HTTP {e.response.status_code} for {page_info}, "
                        f"retrying in {wait_time}s (attempt {attempt+1}/{self.max_retries_per_page+1})"
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise ConceptNetAPIError(
                        f"HTTP {e.response.status_code} for {page_info} after {self.max_retries_per_page} retries",
                        status_code=e.response.status_code
                    )
                    
            except (httpx.ConnectTimeout, httpx.ReadTimeout) as e:
                if attempt < self.max_retries_per_page:
                    wait_time = 2 ** attempt
                    self.logger.warning(
                        f"Timeout for {page_info}, retrying in {wait_time}s "
                        f"(attempt {attempt+1}/{self.max_retries_per_page+1})"
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise ConceptNetAPIError(f"Timeout for {page_info} after {self.max_retries_per_page} retries")
                    
            except Exception as e:
                if attempt < self.max_retries_per_page:
                    wait_time = 2 ** attempt
                    self.logger.warning(
                        f"Error fetching {page_info}: {e}, retrying in {wait_time}s "
                        f"(attempt {attempt+1}/{self.max_retries_per_page+1})"
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise ConceptNetAPIError(f"Failed to fetch {page_info} after {self.max_retries_per_page} retries: {e}")
        
        # Should never reach here
        raise ConceptNetAPIError(f"Unexpected error fetching {page_info}")
    
    def validate_pagination_structure(self, response: Dict[str, Any]) -> bool:
        """
        Ensure response has correct pagination format.
        
        Args:
            response: API response to validate
            
        Returns:
            True if structure is valid
            
        Raises:
            PaginationError: If response structure is invalid
        """
        if not isinstance(response, dict):
            raise PaginationError("Response must be a dictionary")
        
        # Check for required JSON-LD fields
        if '@id' not in response:
            raise PaginationError("Response missing required '@id' field")
        
        # If view exists, validate its structure
        view = response.get('view')
        if view is not None:
            if not isinstance(view, dict):
                raise PaginationError("'view' field must be a dictionary")
            
            # Check for required view fields
            if 'paginatedProperty' not in view:
                raise PaginationError("'view' missing 'paginatedProperty' field")
            
            paginated_property = view['paginatedProperty']
            if paginated_property not in response:
                raise PaginationError(f"Response missing paginated property '{paginated_property}'")
            
            if not isinstance(response[paginated_property], list):
                raise PaginationError(f"Paginated property '{paginated_property}' must be a list")
        
        return True
    
    async def stream_all_pages(
        self,
        client: httpx.AsyncClient,
        initial_response: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream items from all pages without loading everything into memory.
        
        This is a memory-efficient alternative to get_all_pages for very large datasets.
        
        Args:
            client: httpx AsyncClient instance
            initial_response: The initial API response
            
        Yields:
            Individual items from the paginated property
        """
        try:
            self.validate_pagination_structure(initial_response)
            pagination_info = self.detect_pagination_info(initial_response)
            
            # Yield items from initial response
            items = initial_response.get(pagination_info.paginated_property, [])
            for item in items:
                yield item
            
            if not pagination_info.has_pagination:
                return
            
            # Follow pagination links
            current_url = pagination_info.next_page_url
            page_count = 1
            
            while current_url and (not self.max_pages or page_count < self.max_pages):
                try:
                    response = await self._fetch_page_with_retry(client, current_url, page_count)
                    items = response.get(pagination_info.paginated_property, [])
                    
                    for item in items:
                        yield item
                    
                    # Get next page URL
                    current_url = self.extract_next_page_url(response)
                    page_count += 1
                    
                except Exception as e:
                    self.logger.error(f"Failed to fetch page {page_count+1}: {e}")
                    break
                    
        except Exception as e:
            if isinstance(e, PaginationError):
                raise
            raise PaginationError(f"Streaming pagination failed: {str(e)}")