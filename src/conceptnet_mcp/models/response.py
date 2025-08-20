"""
Pydantic models for ConceptNet API responses.

This module defines the data models for representing responses from the ConceptNet API,
including structured data containers, pagination metadata, and error handling models.
"""

from typing import Any, Optional, List, Dict, Generic, TypeVar, Union
from pydantic import BaseModel, Field, field_validator
from .concept import Concept, ConceptNode
from .edge import Edge


T = TypeVar('T')


class ViewInfo(BaseModel):
    """
    Pagination metadata for ConceptNet API responses.
    
    Contains information about the current view of data, including
    pagination links and the property being paginated.
    """
    
    id: str = Field(
        alias="@id",
        description="URI representing the current view with pagination parameters"
    )
    next_page: Optional[str] = Field(
        default=None,
        alias="nextPage",
        description="URI for the next page of results, if available"
    )
    previous_page: Optional[str] = Field(
        default=None,
        alias="previousPage", 
        description="URI for the previous page of results, if available"
    )
    paginated_property: str = Field(
        alias="paginatedProperty",
        description="The name of the property that is being paginated (e.g., 'edges')"
    )
    
    @property
    def has_next_page(self) -> bool:
        """Return True if there is a next page available."""
        return self.next_page is not None
    
    @property
    def has_previous_page(self) -> bool:
        """Return True if there is a previous page available."""
        return self.previous_page is not None
    
    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return f"ViewInfo(paginating '{self.paginated_property}', has_next={self.has_next_page})"


class APIResponse(BaseModel):
    """
    Base model for common ConceptNet API response structure.
    
    Contains the JSON-LD context and common fields present in most
    ConceptNet API responses.
    """
    
    context: List[str] = Field(
        alias="@context",
        default_factory=lambda: ["http://api.conceptnet.io/ld/conceptnet5.7/context.ld.json"],
        description="JSON-LD context for the response"
    )
    id: str = Field(
        alias="@id",
        description="The unique ConceptNet URI for this resource"
    )
    
    @field_validator('context')
    @classmethod
    def validate_context(cls, v: List[str]) -> List[str]:
        """Ensure the context contains the expected ConceptNet context."""
        expected_context = "http://api.conceptnet.io/ld/conceptnet5.7/context.ld.json"
        if expected_context not in v:
            # Add the expected context if it's missing
            v.append(expected_context)
        return v


class ConceptResponse(APIResponse):
    """
    Response model for concept lookup operations.
    
    Contains the concept data, associated edges, and pagination
    metadata returned by the ConceptNet API.
    """
    
    edges: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of edges (relationships) connected to this concept"
    )
    view: Optional[ViewInfo] = Field(
        default=None,
        description="Pagination metadata for the edges"
    )
    
    @property
    def edge_count(self) -> int:
        """Return the total number of edges in this response."""
        return len(self.edges)
    
    @property
    def is_paginated(self) -> bool:
        """Return True if this response is part of a paginated result set."""
        return self.view is not None
    
    def get_edges_by_relation(self, relation: str) -> List[Dict[str, Any]]:
        """
        Filter edges by relation type.
        
        Args:
            relation: The relation type to filter by
            
        Returns:
            List of edges matching the specified relation
        """
        return [
            edge for edge in self.edges
            if edge.get('rel', {}).get('@id', '').endswith(f'/{relation}')
        ]
    
    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return f"ConceptResponse({self.id}) with {self.edge_count} edges"


class EdgeListResponse(APIResponse):
    """
    Response model for edge/relationship queries.
    
    Contains a list of edges and pagination metadata for
    relationship queries from the ConceptNet API.
    """
    
    edges: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of edges matching the query criteria"
    )
    view: Optional[ViewInfo] = Field(
        default=None,
        description="Pagination metadata for the edges"
    )
    
    @property
    def edge_count(self) -> int:
        """Return the total number of edges in this response."""
        return len(self.edges)
    
    @property
    def is_paginated(self) -> bool:
        """Return True if this response is part of a paginated result set."""
        return self.view is not None
    
    def get_unique_concepts(self) -> List[str]:
        """
        Extract unique concept URIs from all edges.
        
        Returns:
            List of unique concept URIs that appear in the edges
        """
        concepts = set()
        for edge in self.edges:
            if 'start' in edge and '@id' in edge['start']:
                concepts.add(edge['start']['@id'])
            if 'end' in edge and '@id' in edge['end']:
                concepts.add(edge['end']['@id'])
        return sorted(list(concepts))
    
    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return f"EdgeListResponse with {self.edge_count} edges"


class RelatedConceptsResponse(BaseModel):
    """
    Response model for related concepts queries.
    
    Contains a list of concepts related to the query concept,
    typically with similarity scores.
    """
    
    related: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of related concepts with similarity scores"
    )
    
    @property
    def related_count(self) -> int:
        """Return the number of related concepts."""
        return len(self.related)
    
    def get_top_related(self, n: int = 5) -> List[Dict[str, Any]]:
        """
        Get the top N most related concepts.
        
        Args:
            n: Number of top concepts to return
            
        Returns:
            List of the most related concepts
        """
        # Sort by weight/score if available, otherwise return first n
        sorted_related = sorted(
            self.related,
            key=lambda x: x.get('weight', 0),
            reverse=True
        )
        return sorted_related[:n]
    
    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return f"RelatedConceptsResponse with {self.related_count} related concepts"


class RelatednessResponse(BaseModel):
    """
    Response model for concept relatedness calculations.
    
    Contains the calculated relatedness score and metadata
    about the calculation between two concepts.
    """
    
    value: float = Field(
        description="The relatedness score between the two concepts",
        ge=0.0,
        le=1.0
    )
    concept1: str = Field(
        description="URI of the first concept"
    )
    concept2: str = Field(
        description="URI of the second concept"
    )
    
    @field_validator('value')
    @classmethod
    def validate_relatedness_score(cls, v: float) -> float:
        """Ensure the relatedness score is between 0 and 1."""
        if v < 0.0 or v > 1.0:
            raise ValueError("Relatedness score must be between 0.0 and 1.0")
        return v
    
    @property
    def is_strong_relationship(self) -> bool:
        """Return True if the concepts have a strong relationship (score > 0.5)."""
        return self.value > 0.5
    
    @property
    def is_weak_relationship(self) -> bool:
        """Return True if the concepts have a weak relationship (score < 0.2)."""
        return self.value < 0.2
    
    def get_relationship_strength(self) -> str:
        """
        Get a human-readable description of the relationship strength.
        
        Returns:
            String describing the relationship strength
        """
        if self.value >= 0.8:
            return "very strong"
        elif self.value >= 0.6:
            return "strong"
        elif self.value >= 0.4:
            return "moderate"
        elif self.value >= 0.2:
            return "weak"
        else:
            return "very weak"
    
    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return f"Relatedness({self.concept1} <-> {self.concept2}): {self.value:.3f} ({self.get_relationship_strength()})"


class ConceptUriResponse(BaseModel):
    """
    Response model for concept URI generation.
    
    Contains the original text and its corresponding ConceptNet URI.
    """
    
    text: str = Field(
        description="The original input text"
    )
    uri: str = Field(
        description="The generated ConceptNet URI"
    )
    language: str = Field(
        description="The language code used for URI generation"
    )
    
    @field_validator('uri')
    @classmethod
    def validate_concept_uri(cls, v: str) -> str:
        """Validate that the URI follows ConceptNet format."""
        if not v.startswith('/c/'):
            raise ValueError("Generated URI must be a valid ConceptNet concept URI")
        return v
    
    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return f"'{self.text}' -> {self.uri}"


class ErrorResponse(BaseModel):
    """
    Response model for API error conditions.
    
    Standardizes error responses from the ConceptNet API
    and internal server errors.
    """
    
    error: str = Field(
        description="Error type or code"
    )
    message: str = Field(
        description="Human-readable error message"
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details and context"
    )
    status_code: Optional[int] = Field(
        default=None,
        description="HTTP status code associated with the error"
    )
    
    @property
    def is_client_error(self) -> bool:
        """Return True if this is a client error (4xx status code)."""
        return self.status_code is not None and 400 <= self.status_code < 500
    
    @property
    def is_server_error(self) -> bool:
        """Return True if this is a server error (5xx status code)."""
        return self.status_code is not None and 500 <= self.status_code < 600
    
    def __str__(self) -> str:
        """Return a human-readable string representation."""
        if self.status_code:
            return f"Error {self.status_code}: {self.message}"
        return f"Error: {self.message}"


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic model for paginated API responses.
    
    Wraps paginated results from the ConceptNet API with metadata
    about the total count, current page, and navigation links.
    """
    
    items: List[T] = Field(
        description="The list of items in this page"
    )
    view: Optional[ViewInfo] = Field(
        default=None,
        description="Pagination metadata"
    )
    total_items: Optional[int] = Field(
        default=None,
        description="Total number of items across all pages (if known)"
    )
    
    @property
    def item_count(self) -> int:
        """Return the number of items in this page."""
        return len(self.items)
    
    @property
    def has_next_page(self) -> bool:
        """Return True if there is a next page available."""
        return self.view is not None and self.view.has_next_page
    
    @property
    def has_previous_page(self) -> bool:
        """Return True if there is a previous page available."""
        return self.view is not None and self.view.has_previous_page
    
    def __str__(self) -> str:
        """Return a human-readable string representation."""
        total_str = f" of {self.total_items}" if self.total_items else ""
        return f"PaginatedResponse({self.item_count} items{total_str})"