"""
Pydantic models for ConceptNet concepts.

This module defines the data models for representing ConceptNet concepts,
including their URIs, labels, language information, and associated metadata.
"""

from typing import Any, Optional, List, Dict
from pydantic import BaseModel, Field, field_validator
import re


class ConceptNode(BaseModel):
    """
    Represents a concept node in ConceptNet.
    
    A ConceptNode is the basic unit representing a concept in the ConceptNet
    knowledge graph. It contains the unique identifier, human-readable label,
    language information, and optional sense disambiguation.
    """
    
    id: str = Field(
        alias="@id",
        description="The unique ConceptNet URI for this concept (e.g., '/c/en/dog')"
    )
    label: str = Field(
        description="Human-readable label for the concept"
    )
    language: str = Field(
        description="ISO 639-1 language code (e.g., 'en', 'es', 'fr')"
    )
    term: str = Field(
        description="The actual term or phrase representing the concept"
    )
    sense_label: Optional[str] = Field(
        default=None,
        description="Optional disambiguation label for different senses of the same term"
    )
    
    @field_validator('id')
    @classmethod
    def validate_concept_uri(cls, v: str) -> str:
        """Validate that the ID follows ConceptNet URI format."""
        if not v.startswith('/c/'):
            raise ValueError("ConceptNode ID must be a valid ConceptNet URI starting with '/c/'")
        return v
    
    @field_validator('language')
    @classmethod
    def validate_language_code(cls, v: str) -> str:
        """Validate that the language is a reasonable language code."""
        if not re.match(r'^[a-z]{2,3}$', v):
            raise ValueError("Language must be a 2-3 character language code")
        return v
    
    def __str__(self) -> str:
        """Return a human-readable string representation."""
        if self.sense_label:
            return f"{self.label} ({self.sense_label}) [{self.language}]"
        return f"{self.label} [{self.language}]"
    
    def __repr__(self) -> str:
        """Return a detailed string representation for debugging."""
        return f"ConceptNode(id='{self.id}', label='{self.label}', language='{self.language}')"


class Concept(BaseModel):
    """
    Main concept with edges and metadata.
    
    Represents a complete concept response from ConceptNet, including
    the concept's unique identifier and all associated edges (relationships)
    with other concepts.
    """
    
    id: str = Field(
        alias="@id",
        description="The unique ConceptNet URI for this concept"
    )
    edges: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of edges (relationships) connected to this concept"
    )
    view: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Pagination and view metadata from the ConceptNet API"
    )
    
    @field_validator('id')
    @classmethod
    def validate_concept_uri(cls, v: str) -> str:
        """Validate that the ID follows ConceptNet URI format."""
        if not v.startswith('/c/'):
            raise ValueError("Concept ID must be a valid ConceptNet URI starting with '/c/'")
        return v
    
    @property
    def edge_count(self) -> int:
        """Return the number of edges associated with this concept."""
        return len(self.edges)
    
    def filter_edges_by_relation(self, relation: str) -> List[Dict[str, Any]]:
        """
        Filter edges by relation type.
        
        Args:
            relation: The relation type to filter by (e.g., 'RelatedTo', 'IsA')
            
        Returns:
            List of edges matching the specified relation type
        """
        return [
            edge for edge in self.edges 
            if edge.get('rel', {}).get('@id', '').endswith(f'/{relation}')
        ]
    
    def filter_edges_by_language(self, language: str) -> List[Dict[str, Any]]:
        """
        Filter edges to only include those with concepts in the specified language.
        
        Args:
            language: ISO 639-1 language code to filter by
            
        Returns:
            List of edges where both start and end concepts are in the specified language
        """
        filtered_edges = []
        for edge in self.edges:
            start_lang = edge.get('start', {}).get('language', '')
            end_lang = edge.get('end', {}).get('language', '')
            if start_lang == language and end_lang == language:
                filtered_edges.append(edge)
        return filtered_edges
    
    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return f"Concept({self.id}) with {self.edge_count} edges"
    
    def __repr__(self) -> str:
        """Return a detailed string representation for debugging."""
        return f"Concept(id='{self.id}', edges={self.edge_count})"