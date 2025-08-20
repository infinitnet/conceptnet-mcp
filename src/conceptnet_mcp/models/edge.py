"""
Pydantic models for ConceptNet edges.

This module defines the data models for representing ConceptNet edges (relationships),
including their start/end concepts, relation types, weights, and source information.
"""

from typing import Any, Optional, List, Dict
from pydantic import BaseModel, Field, field_validator
from .concept import ConceptNode


class Relation(BaseModel):
    """
    Represents a relationship type in ConceptNet.
    
    Relations define the semantic relationship between two concepts,
    such as "IsA", "RelatedTo", "UsedFor", etc.
    """
    
    id: str = Field(
        alias="@id",
        description="The unique ConceptNet URI for this relation (e.g., '/r/IsA')"
    )
    label: str = Field(
        description="Human-readable label for the relation type"
    )
    
    @field_validator('id')
    @classmethod
    def validate_relation_uri(cls, v: str) -> str:
        """Validate that the ID follows ConceptNet relation URI format."""
        if not v.startswith('/r/'):
            raise ValueError("Relation ID must be a valid ConceptNet URI starting with '/r/'")
        return v
    
    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return self.label
    
    def __repr__(self) -> str:
        """Return a detailed string representation for debugging."""
        return f"Relation(id='{self.id}', label='{self.label}')"


class Source(BaseModel):
    """
    Represents source information for a ConceptNet edge.
    
    Sources contain information about where an edge's data came from,
    including contributor, activity, and process details.
    """
    
    id: str = Field(
        alias="@id",
        description="The unique ConceptNet URI for this source"
    )
    contributor: Optional[str] = Field(
        default=None,
        description="The contributor or dataset that provided this information"
    )
    process: Optional[str] = Field(
        default=None,
        description="The process or method used to extract this information"
    )
    activity: Optional[str] = Field(
        default=None,
        description="The activity or task that generated this information"
    )
    
    @field_validator('id')
    @classmethod
    def validate_source_uri(cls, v: str) -> str:
        """Validate that the ID follows ConceptNet source URI format."""
        if not v.startswith('/s/'):
            raise ValueError("Source ID must be a valid ConceptNet URI starting with '/s/'")
        return v
    
    def __str__(self) -> str:
        """Return a human-readable string representation."""
        if self.contributor:
            return f"Source: {self.contributor}"
        return f"Source: {self.id}"
    
    def __repr__(self) -> str:
        """Return a detailed string representation for debugging."""
        return f"Source(id='{self.id}', contributor='{self.contributor}')"


class Edge(BaseModel):
    """
    Represents a knowledge edge between concepts in ConceptNet.
    
    An Edge represents a relationship between two concepts, including
    the relationship type, strength (weight), and provenance information.
    """
    
    id: str = Field(
        alias="@id",
        description="The unique ConceptNet URI for this edge"
    )
    start: ConceptNode = Field(
        description="The starting concept of this relationship"
    )
    end: ConceptNode = Field(
        description="The ending concept of this relationship"
    )
    rel: Relation = Field(
        description="The type of relationship between the concepts"
    )
    weight: float = Field(
        description="The confidence score or strength of this relationship (typically 0.0-20.0)",
        ge=0.0
    )
    surface_text: Optional[str] = Field(
        default=None,
        alias="surfaceText",
        description="Natural language text that expresses this relationship"
    )
    sources: List[Source] = Field(
        default_factory=list,
        description="List of sources that contributed to this edge"
    )
    license: str = Field(
        description="License under which this edge is distributed"
    )
    dataset: str = Field(
        description="The dataset this edge belongs to"
    )
    
    @field_validator('id')
    @classmethod
    def validate_edge_uri(cls, v: str) -> str:
        """Validate that the ID follows ConceptNet edge URI format."""
        if not v.startswith('/a/'):
            raise ValueError("Edge ID must be a valid ConceptNet URI starting with '/a/'")
        return v
    
    @field_validator('weight')
    @classmethod
    def validate_weight(cls, v: float) -> float:
        """Ensure weight is a reasonable value."""
        if v < 0.0:
            raise ValueError("Edge weight must be non-negative")
        return v
    
    @property
    def is_strong_relationship(self) -> bool:
        """Return True if this edge represents a strong relationship (weight > 0.5)."""
        return self.weight > 0.5
    
    @property
    def source_count(self) -> int:
        """Return the number of sources supporting this edge."""
        return len(self.sources)
    
    def get_primary_source(self) -> Optional[Source]:
        """
        Get the primary (first) source for this edge.
        
        Returns:
            The first source if available, None otherwise
        """
        return self.sources[0] if self.sources else None
    
    def involves_concept(self, concept_uri: str) -> bool:
        """
        Check if this edge involves a specific concept.
        
        Args:
            concept_uri: The ConceptNet URI to check for
            
        Returns:
            True if the concept is either the start or end of this edge
        """
        return self.start.id == concept_uri or self.end.id == concept_uri
    
    def get_other_concept(self, concept_uri: str) -> Optional[ConceptNode]:
        """
        Get the other concept in this edge relationship.
        
        Args:
            concept_uri: The ConceptNet URI of the known concept
            
        Returns:
            The other concept if the provided URI matches start or end, None otherwise
        """
        if self.start.id == concept_uri:
            return self.end
        elif self.end.id == concept_uri:
            return self.start
        return None
    
    def to_natural_language(self) -> str:
        """
        Convert this edge to a natural language description.
        
        Returns:
            A human-readable description of the relationship
        """
        if self.surface_text:
            return self.surface_text
        
        # Fallback to constructing from components
        return f"{self.start.label} {self.rel.label.lower()} {self.end.label}"
    
    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return f"{self.start.label} --[{self.rel.label}]--> {self.end.label} (weight: {self.weight:.3f})"
    
    def __repr__(self) -> str:
        """Return a detailed string representation for debugging."""
        return (f"Edge(start='{self.start.id}', end='{self.end.id}', "
                f"rel='{self.rel.id}', weight={self.weight})")