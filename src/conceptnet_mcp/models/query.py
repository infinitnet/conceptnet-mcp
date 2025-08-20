"""
Pydantic models for ConceptNet API queries.

This module defines the data models for representing various types of queries
to the ConceptNet API, including search parameters, filters, and pagination options.
"""

from typing import Optional, Set
from pydantic import BaseModel, Field, field_validator, model_validator
from typing_extensions import Self


class QueryFilters(BaseModel):
    """
    Query parameters for ConceptNet API advanced search.
    
    This model encapsulates all the filtering options available for the ConceptNet
    query endpoint, providing validation and sensible defaults for pagination.
    """
    
    start: Optional[str] = Field(
        default=None,
        description="Filter by start concept URI (e.g., '/c/en/dog')"
    )
    end: Optional[str] = Field(
        default=None,
        description="Filter by end concept URI (e.g., '/c/en/animal')"
    )
    rel: Optional[str] = Field(
        default=None,
        description="Filter by relation type URI (e.g., '/r/IsA')"
    )
    node: Optional[str] = Field(
        default=None,
        description="Filter by concept that appears as either start or end"
    )
    other: Optional[str] = Field(
        default=None,
        description="Filter by concept different from the 'node' parameter"
    )
    sources: Optional[str] = Field(
        default=None,
        description="Filter by source dataset or contributor"
    )
    limit: int = Field(
        default=20,
        description="Maximum number of results to return",
        ge=1,
        le=1000
    )
    offset: int = Field(
        default=0,
        description="Number of results to skip for pagination",
        ge=0
    )
    
    @field_validator('start', 'end', 'node', 'other')
    @classmethod
    def validate_concept_uris(cls, v: Optional[str]) -> Optional[str]:
        """Validate concept URIs start with '/c/'."""
        if v is not None and not v.startswith('/c/'):
            raise ValueError("Concept URIs must start with '/c/'")
        return v
    
    @field_validator('rel')
    @classmethod
    def validate_relation_uri(cls, v: Optional[str]) -> Optional[str]:
        """Validate relation URIs start with '/r/'."""
        if v is not None and not v.startswith('/r/'):
            raise ValueError("Relation URIs must start with '/r/'")
        return v
    
    @model_validator(mode='after')
    def validate_query_logic(self) -> Self:
        """Validate that the query parameters make logical sense together."""
        # If 'other' is specified, 'node' must also be specified
        if self.other is not None and self.node is None:
            raise ValueError("'other' parameter requires 'node' parameter to be specified")
        
        # 'node' and 'other' cannot be the same
        if self.node is not None and self.other is not None and self.node == self.other:
            raise ValueError("'node' and 'other' parameters cannot be the same")
        
        # At least one filter parameter should be specified for meaningful queries
        filter_params = [self.start, self.end, self.rel, self.node, self.sources]
        if all(param is None for param in filter_params):
            raise ValueError("At least one filter parameter must be specified")
        
        return self
    
    def to_query_params(self) -> dict[str, str]:
        """
        Convert this model to a dictionary suitable for HTTP query parameters.
        
        Returns:
            Dictionary of non-None parameters as strings
        """
        params = {}
        
        if self.start is not None:
            params['start'] = self.start
        if self.end is not None:
            params['end'] = self.end
        if self.rel is not None:
            params['rel'] = self.rel
        if self.node is not None:
            params['node'] = self.node
        if self.other is not None:
            params['other'] = self.other
        if self.sources is not None:
            params['sources'] = self.sources
        
        params['limit'] = str(self.limit)
        params['offset'] = str(self.offset)
        
        return params
    
    def get_specified_filters(self) -> Set[str]:
        """
        Get the names of all filter parameters that have been specified.
        
        Returns:
            Set of parameter names that are not None
        """
        specified = set()
        if self.start is not None:
            specified.add('start')
        if self.end is not None:
            specified.add('end')
        if self.rel is not None:
            specified.add('rel')
        if self.node is not None:
            specified.add('node')
        if self.other is not None:
            specified.add('other')
        if self.sources is not None:
            specified.add('sources')
        return specified
    
    def __str__(self) -> str:
        """Return a human-readable string representation."""
        filters = self.get_specified_filters()
        return f"QueryFilters({', '.join(filters)}, limit={self.limit}, offset={self.offset})"
    
    def __repr__(self) -> str:
        """Return a detailed string representation for debugging."""
        return (f"QueryFilters(start='{self.start}', end='{self.end}', rel='{self.rel}', "
                f"node='{self.node}', other='{self.other}', sources='{self.sources}', "
                f"limit={self.limit}, offset={self.offset})")


class ConceptLookupQuery(BaseModel):
    """
    Query model for looking up a specific concept.
    
    This model defines parameters for retrieving information
    about a specific concept from the ConceptNet API.
    """
    
    term: str = Field(
        description="The concept term to look up"
    )
    language: str = Field(
        default="en",
        description="Language code for the concept (e.g., 'en', 'es', 'fr')"
    )
    limit_results: bool = Field(
        default=False,
        description="Whether to limit results to first page (20 items)"
    )
    target_language: Optional[str] = Field(
        default=None,
        description="Filter results to specific language"
    )
    
    @field_validator('language', 'target_language')
    @classmethod
    def validate_language_codes(cls, v: Optional[str]) -> Optional[str]:
        """Validate language codes are reasonable."""
        if v is not None and (len(v) < 2 or len(v) > 3 or not v.isalpha()):
            raise ValueError("Language code must be 2-3 alphabetic characters")
        return v.lower() if v else v
    
    def to_concept_uri(self) -> str:
        """Convert term and language to ConceptNet URI format."""
        # Replace spaces with underscores and construct URI
        normalized_term = self.term.replace(' ', '_').lower()
        return f"/c/{self.language}/{normalized_term}"
    
    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return f"ConceptLookup('{self.term}' in {self.language})"


class RelatedConceptsQuery(BaseModel):
    """
    Query model for finding related concepts.
    
    This model defines parameters for finding concepts
    related to a given concept through various relation types.
    """
    
    term: str = Field(
        description="The concept term to find relations for"
    )
    language: str = Field(
        default="en",
        description="Language of the input term"
    )
    filter_language: Optional[str] = Field(
        default=None,
        description="Filter results to specific language"
    )
    limit: int = Field(
        default=20,
        description="Maximum number of related concepts to return",
        ge=1,
        le=100
    )
    
    @field_validator('language', 'filter_language')
    @classmethod
    def validate_language_codes(cls, v: Optional[str]) -> Optional[str]:
        """Validate language codes are reasonable."""
        if v is not None and (len(v) < 2 or len(v) > 3 or not v.isalpha()):
            raise ValueError("Language code must be 2-3 alphabetic characters")
        return v.lower() if v else v
    
    def to_concept_uri(self) -> str:
        """Convert term and language to ConceptNet URI format."""
        normalized_term = self.term.replace(' ', '_').lower()
        return f"/c/{self.language}/{normalized_term}"
    
    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return f"RelatedConcepts('{self.term}' in {self.language}, limit={self.limit})"


class RelatednessQuery(BaseModel):
    """
    Query model for calculating concept relatedness.
    
    This model defines parameters for calculating the
    semantic relatedness between two concepts.
    """
    
    concept1: str = Field(
        description="First concept term"
    )
    concept2: str = Field(
        description="Second concept term"
    )
    language1: str = Field(
        default="en",
        description="Language of the first concept"
    )
    language2: str = Field(
        default="en",
        description="Language of the second concept"
    )
    
    @field_validator('language1', 'language2')
    @classmethod
    def validate_language_codes(cls, v: str) -> str:
        """Validate language codes are reasonable."""
        if len(v) < 2 or len(v) > 3 or not v.isalpha():
            raise ValueError("Language code must be 2-3 alphabetic characters")
        return v.lower()
    
    def to_concept_uris(self) -> tuple[str, str]:
        """Convert both terms to ConceptNet URI format."""
        normalized_term1 = self.concept1.replace(' ', '_').lower()
        normalized_term2 = self.concept2.replace(' ', '_').lower()
        uri1 = f"/c/{self.language1}/{normalized_term1}"
        uri2 = f"/c/{self.language2}/{normalized_term2}"
        return uri1, uri2
    
    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return f"Relatedness('{self.concept1}' <-> '{self.concept2}')"