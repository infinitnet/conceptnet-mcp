"""
Response processing utilities for ConceptNet API data.

This module provides utilities for processing and transforming raw API responses
into structured data models and performing common data operations like language
filtering, text normalization, and response processing.
"""

import re
from typing import Any, Optional, List, Dict, Union, Set
from ..models.concept import Concept, ConceptNode
from ..models.edge import Edge
from ..models.response import ConceptResponse, EdgeListResponse, RelatedConceptsResponse
from ..utils.text_utils import (
    normalize_text_for_display,
    normalize_uri_to_text,
    normalize_relation_text,
    extract_language_from_uri
)
from ..utils.logging import get_logger


class ResponseProcessor:
    """
    Processor for transforming and normalizing ConceptNet API responses.
    
    This class handles the conversion of raw API responses into structured,
    normalized data with improved readability and language filtering capabilities.
    """
    
    def __init__(self, default_language: str = "en"):
        """
        Initialize the response processor.
        
        Args:
            default_language: Default language code for processing
        """
        self.default_language = default_language
        self.logger = get_logger(__name__)
        
    def normalize_text(self, text: str) -> str:
        """
        Convert underscores to spaces and normalize text for display.
        
        This is the core text normalization function that converts ConceptNet's
        underscore-separated terms into human-readable space-separated text.
        
        Args:
            text: Input text to normalize
            
        Returns:
            Normalized text with underscores converted to spaces
        """
        return normalize_text_for_display(text)
    
    def extract_language_from_concept(self, concept: Dict[str, Any]) -> Optional[str]:
        """
        Extract language code from a concept dictionary.
        
        Args:
            concept: Concept dictionary with potential language information
            
        Returns:
            Language code if found, None otherwise
        """
        # Try direct language field first
        if "language" in concept:
            return concept["language"]
        
        # Try to extract from @id URI
        concept_id = concept.get("@id", "")
        if concept_id:
            return extract_language_from_uri(concept_id)
        
        # Try to extract from label if it follows pattern
        label = concept.get("label", "")
        if label and "/" in label:
            parts = label.split("/")
            if len(parts) >= 3 and parts[1] == "c":
                return parts[2]
        
        return None
    
    def filter_by_language(
        self,
        edges: List[Dict[str, Any]],
        target_language: str,
        require_both: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Filter edges by target language.
        
        By default, includes edges where BOTH start and end concepts match the target language.
        This removes cross-language edges to provide clean same-language results.
        
        Args:
            edges: List of edge dictionaries to filter
            target_language: Language code to filter by
            require_both: If True, both concepts must match target language.
                         If False, either concept can match (legacy behavior).
            
        Returns:
            Filtered list of edges
        """
        if not target_language:
            return edges
        
        filtered = []
        for edge in edges:
            start_concept = edge.get("start", {})
            end_concept = edge.get("end", {})
            
            start_lang = self.extract_language_from_concept(start_concept)
            end_lang = self.extract_language_from_concept(end_concept)
            
            if require_both:
                # Include edge only if BOTH start and end match target language
                if start_lang == target_language and end_lang == target_language:
                    filtered.append(edge)
            else:
                # Legacy behavior: include edge if either start or end matches target language
                if start_lang == target_language or end_lang == target_language:
                    filtered.append(edge)
        
        return filtered
    
    def normalize_concept_node(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a concept node for better readability.
        
        Args:
            node: Concept node dictionary
            
        Returns:
            Normalized concept node with readable text
        """
        if not node:
            return node
        
        normalized = node.copy()
        
        # Add normalized label from URI
        node_id = normalized.get("@id", "")
        if node_id:
            normalized["normalized_label"] = normalize_uri_to_text(node_id)
            normalized["_original_id"] = node_id
        
        # Normalize existing label if present
        if "label" in normalized:
            original_label = normalized["label"]
            normalized["label"] = self.normalize_text(original_label)
            if original_label != normalized["label"]:
                normalized["_original_label"] = original_label
        
        # Extract and add language information
        language = self.extract_language_from_concept(normalized)
        if language:
            normalized["language"] = language
        
        return normalized
    
    def normalize_edge(self, edge: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a single edge for better readability.
        
        Args:
            edge: Edge dictionary to normalize
            
        Returns:
            Normalized edge with readable text and preserved original data
        """
        if not edge:
            return edge
        
        normalized = edge.copy()
        
        # Normalize start and end concepts
        if "start" in normalized:
            normalized["start"] = self.normalize_concept_node(normalized["start"])
        
        if "end" in normalized:
            normalized["end"] = self.normalize_concept_node(normalized["end"])
        
        # Normalize relation
        if "rel" in normalized:
            rel = normalized["rel"]
            if isinstance(rel, dict):
                rel_copy = rel.copy()
                rel_id = rel_copy.get("@id", "")
                if rel_id:
                    rel_copy["normalized_label"] = normalize_relation_text(rel_id)
                    rel_copy["_original_id"] = rel_id
                
                # Normalize existing label
                if "label" in rel_copy:
                    original_label = rel_copy["label"]
                    rel_copy["label"] = self.normalize_text(original_label)
                    if original_label != rel_copy["label"]:
                        rel_copy["_original_label"] = original_label
                
                normalized["rel"] = rel_copy
        
        # Normalize surface text
        if "surfaceText" in normalized:
            original_surface = normalized["surfaceText"]
            normalized["surfaceText"] = self.normalize_text(original_surface)
            if original_surface != normalized["surfaceText"]:
                normalized["_original_surface_text"] = original_surface
        
        # Add human-readable summary
        normalized["readable_summary"] = self._create_edge_summary(normalized)
        
        return normalized
    
    def _clean_concept_label(self, label: str) -> str:
        """
        Clean concept labels by removing part-of-speech annotations and WordNet tags.
        
        Removes technical annotations like /N, /V, /A, /ADJ, /ADV, etc. and
        WordNet-derived annotations like /Wn/Food, /Wn/Substance, etc.
        that are used internally by ConceptNet but should not appear
        in user-facing readable summaries.
        
        Args:
            label: Original concept label that may contain POS tags
            
        Returns:
            Cleaned label without part-of-speech annotations or WordNet tags
        """
        if not label or not isinstance(label, str):
            return label
        
        # Remove WordNet-derived tags like /Wn/Food, /Wn/Substance, etc.
        # Pattern matches: /Wn/ followed by any word characters
        wn_pattern = r'/Wn/[\w]*'
        cleaned = re.sub(wn_pattern, '', label)
        
        # Remove part-of-speech tags like /N, /V, /A, /ADJ, /ADV, etc.
        # Pattern matches: slash followed by uppercase letters/common POS tags
        pos_pattern = r'/[A-Z][A-Z]*\b'
        cleaned = re.sub(pos_pattern, '', cleaned)
        
        # Remove trailing slashes (edge case)
        cleaned = re.sub(r'/$', '', cleaned)
        
        # Clean up any remaining whitespace
        cleaned = cleaned.strip()
        
        return cleaned if cleaned else label
    
    def _create_edge_summary(self, edge: Dict[str, Any]) -> str:
        """
        Create a human-readable summary of an edge relationship.
        
        Args:
            edge: Normalized edge dictionary
            
        Returns:
            Human-readable relationship summary
        """
        try:
            start = edge.get("start", {})
            end = edge.get("end", {})
            rel = edge.get("rel", {})
            
            start_label = (
                start.get("normalized_label") or
                start.get("label") or
                start.get("@id", "unknown")
            )
            
            end_label = (
                end.get("normalized_label") or
                end.get("label") or
                end.get("@id", "unknown")
            )
            
            # Clean part-of-speech annotations from labels
            start_label = self._clean_concept_label(start_label)
            end_label = self._clean_concept_label(end_label)
            
            rel_label = (
                rel.get("normalized_label") or
                rel.get("label") or
                "related to"
            )
            
            # Use surface text if available and more natural
            surface_text = edge.get("surfaceText")
            if surface_text and len(surface_text) > 10:  # Use surface text if substantial
                return surface_text
            
            return f"{start_label} {rel_label} {end_label}"
            
        except Exception as e:
            self.logger.warning(f"Failed to create edge summary: {e}")
            return "relationship"
    
    def process_concept_response(
        self, 
        response: Dict[str, Any],
        target_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process and normalize a complete concept response.
        
        Args:
            response: Raw concept response from the ConceptNet API
            target_language: Optional language to filter edges by
            
        Returns:
            Processed concept response with normalized data
        """
        if not response:
            return response
        
        processed = response.copy()
        
        # Normalize the main concept information
        if "@id" in processed:
            processed["normalized_id"] = normalize_uri_to_text(processed["@id"])
            processed["_original_id"] = processed["@id"]
        
        # Process and filter edges
        if "edges" in processed:
            edges = processed["edges"]
            
            # Filter by language if specified
            if target_language:
                edges = self.filter_by_language(edges, target_language)
                processed["_filtered_by_language"] = target_language
                processed["_original_edge_count"] = len(processed["edges"])
            
            # Normalize all edges
            processed["edges"] = [self.normalize_edge(edge) for edge in edges]
            processed["edge_count"] = len(processed["edges"])
        
        # Add relation summary
        if "edges" in processed:
            processed["relation_summary"] = self.extract_readable_relations(processed["edges"])
        
        return processed
    
    def process_edge_list(
        self, 
        edges: List[Dict[str, Any]], 
        target_language: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Process a list of edges with optional language filtering.
        
        Args:
            edges: List of edge dictionaries
            target_language: Optional language to filter by
            
        Returns:
            Processed and normalized list of edges
        """
        if not edges:
            return edges
        
        # Filter by language if specified
        if target_language:
            edges = self.filter_by_language(edges, target_language)
        
        # Normalize all edges
        return [self.normalize_edge(edge) for edge in edges]
    
    def process_related_response(
        self, 
        response: Dict[str, Any],
        target_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process related concepts response.
        
        Args:
            response: Raw related concepts response
            target_language: Optional language to filter by
            
        Returns:
            Processed related concepts response
        """
        if not response:
            return response
        
        processed = response.copy()
        
        # Process related concepts list
        if "related" in processed:
            related = processed["related"]
            
            # Filter by language if specified
            if target_language:
                filtered_related = []
                for concept in related:
                    concept_id = concept.get("@id", "")
                    if concept_id:
                        concept_lang = extract_language_from_uri(concept_id)
                        if concept_lang == target_language:
                            filtered_related.append(concept)
                related = filtered_related
                processed["_filtered_by_language"] = target_language
                processed["_original_related_count"] = len(processed["related"])
            
            # Normalize related concepts
            normalized_related = []
            for concept in related:
                normalized_concept = self.normalize_concept_node(concept)
                
                # Add similarity description if weight is present
                weight = concept.get("weight", 0)
                if weight:
                    normalized_concept["similarity_description"] = self._describe_similarity(weight)
                
                normalized_related.append(normalized_concept)
            
            processed["related"] = normalized_related
            processed["related_count"] = len(processed["related"])
        
        return processed
    
    def _describe_similarity(self, weight: float) -> str:
        """
        Convert similarity weight to human-readable description.
        
        Args:
            weight: Similarity weight (0.0 to 1.0)
            
        Returns:
            Human-readable similarity description
        """
        if weight >= 0.8:
            return "very similar"
        elif weight >= 0.6:
            return "similar"
        elif weight >= 0.4:
            return "somewhat similar"
        elif weight >= 0.2:
            return "loosely related"
        else:
            return "weakly related"
    
    def extract_readable_relations(self, edges: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Extract human-readable relation summaries from edges.
        
        Groups edges by relation type and provides readable summaries.
        
        Args:
            edges: List of edge dictionaries
            
        Returns:
            Dictionary mapping relation types to lists of readable relationships
        """
        relations = {}
        
        for edge in edges:
            try:
                rel = edge.get("rel", {})
                rel_id = rel.get("@id", "unknown")
                rel_name = rel.get("normalized_label") or rel.get("label") or "related to"
                
                if rel_name not in relations:
                    relations[rel_name] = []
                
                # Get readable summary
                summary = edge.get("readable_summary", "")
                if summary:
                    relations[rel_name].append(summary)
                
            except Exception as e:
                self.logger.warning(f"Failed to extract relation from edge: {e}")
                continue
        
        # Sort and limit for readability
        for rel_type in relations:
            relations[rel_type] = list(set(relations[rel_type]))[:10]  # Unique, limit to 10
        
        return relations
    
    def get_concept_languages(self, edges: List[Dict[str, Any]]) -> Set[str]:
        """
        Get all unique languages present in a list of edges.
        
        Args:
            edges: List of edge dictionaries
            
        Returns:
            Set of language codes found in the edges
        """
        languages = set()
        
        for edge in edges:
            start_lang = self.extract_language_from_concept(edge.get("start", {}))
            end_lang = self.extract_language_from_concept(edge.get("end", {}))
            
            if start_lang:
                languages.add(start_lang)
            if end_lang:
                languages.add(end_lang)
        
        return languages
    
    def filter_edges_by_relation(
        self, 
        edges: List[Dict[str, Any]], 
        relation_types: Union[str, List[str]]
    ) -> List[Dict[str, Any]]:
        """
        Filter edges by relation type(s).
        
        Args:
            edges: List of edge dictionaries
            relation_types: Single relation type or list of relation types to include
            
        Returns:
            Filtered list of edges
        """
        if isinstance(relation_types, str):
            relation_types = [relation_types]
        
        relation_types = [rel.lower() for rel in relation_types]
        filtered = []
        
        for edge in edges:
            rel = edge.get("rel", {})
            rel_id = rel.get("@id", "").lower()
            rel_label = rel.get("label", "").lower()
            rel_normalized = rel.get("normalized_label", "").lower()
            
            # Check if any of the relation identifiers match
            for target_rel in relation_types:
                if (target_rel in rel_id or 
                    target_rel in rel_label or 
                    target_rel in rel_normalized):
                    filtered.append(edge)
                    break
        
        return filtered
    
    def sort_edges_by_weight(
        self, 
        edges: List[Dict[str, Any]], 
        descending: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Sort edges by their confidence weight.
        
        Args:
            edges: List of edges to sort
            descending: Whether to sort in descending order (highest weight first)
            
        Returns:
            Sorted list of edges
        """
        return sorted(
            edges,
            key=lambda edge: edge.get("weight", 0),
            reverse=descending
        )
    
    def get_edge_statistics(self, edges: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get statistical information about a list of edges.
        
        Args:
            edges: List of edge dictionaries
            
        Returns:
            Dictionary with statistical information
        """
        if not edges:
            return {
                "total_edges": 0,
                "languages": set(),
                "relations": {},
                "avg_weight": 0.0,
                "weight_range": (0.0, 0.0)
            }
        
        weights = [edge.get("weight", 0) for edge in edges]
        relations = {}
        
        for edge in edges:
            rel = edge.get("rel", {})
            rel_name = rel.get("normalized_label") or rel.get("label") or "unknown"
            relations[rel_name] = relations.get(rel_name, 0) + 1
        
        return {
            "total_edges": len(edges),
            "languages": self.get_concept_languages(edges),
            "relations": relations,
            "avg_weight": sum(weights) / len(weights) if weights else 0.0,
            "weight_range": (min(weights), max(weights)) if weights else (0.0, 0.0),
            "most_common_relation": max(relations, key=relations.get) if relations else None
        }
    
    # ===== MINIMAL FORMAT METHODS =====
    
    def create_minimal_concept_response(
        self,
        processed_response: Dict[str, Any],
        concept_term: str
    ) -> Dict[str, Any]:
        """
        Create minimal format response for concept_lookup and concept_query tools.
        
        Args:
            processed_response: Processed response with normalized edges
            concept_term: The main concept term being queried
            
        Returns:
            Minimal format response optimized for LLM consumption
        """
        edges = processed_response.get("edges", [])
        
        # Extract relationships grouped by type
        relationships = self._extract_relationships_by_type(edges)
        
        # Calculate summary statistics
        summary = self._calculate_minimal_summary(
            {"edges": edges, "relationships": relationships},
            "concept"
        )
        
        return {
            "concept": concept_term,
            "relationships": relationships,
            "summary": summary
        }
    
    def create_minimal_related_response(
        self,
        processed_response: Dict[str, Any],
        concept_term: str
    ) -> Dict[str, Any]:
        """
        Create minimal format response for related_concepts tool.
        
        Args:
            processed_response: Processed response with related concepts
            concept_term: The main concept term being queried
            
        Returns:
            Minimal format response optimized for LLM consumption
        """
        related_concepts_raw = processed_response.get("related_concepts", [])
        
        # Extract clean concept list with weights
        related_concepts = []
        weights = []
        
        for concept_data in related_concepts_raw:
            concept_info = concept_data.get("concept", {})
            similarity = concept_data.get("similarity", {})
            
            term = concept_info.get("normalized_display") or concept_info.get("term", "")
            weight = similarity.get("score", 0.0)
            
            if term:
                related_concepts.append({
                    "term": term,
                    "weight": round(weight, 4)
                })
                weights.append(weight)
        
        # Calculate summary statistics
        summary = self._calculate_minimal_summary(
            {"related_concepts": related_concepts, "weights": weights},
            "related"
        )
        
        return {
            "concept": concept_term,
            "related_concepts": related_concepts,
            "summary": summary
        }
    
    def create_minimal_relatedness_response(
        self,
        score: float,
        concept1: str,
        concept2: str
    ) -> Dict[str, Any]:
        """
        Create minimal format response for concept_relatedness tool.
        
        Args:
            score: Relatedness score (0.0-1.0)
            concept1: First concept term
            concept2: Second concept term
            
        Returns:
            Minimal format response optimized for LLM consumption
        """
        # Determine strength category
        if score >= 0.7:
            strength = "strong"
        elif score >= 0.4:
            strength = "moderate"
        else:
            strength = "weak"
        
        return {
            "concept1": concept1,
            "concept2": concept2,
            "relatedness": round(score, 4),
            "strength": strength
        }
    
    def _extract_relationships_by_type(self, edges: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract and group relationships by semantic type.
        
        Args:
            edges: List of processed edge dictionaries
            
        Returns:
            Dictionary mapping relation types to lists of related concepts with weights
        """
        relationships = {}
        
        for edge in edges:
            try:
                # Extract relation type
                rel = edge.get("rel", {})
                rel_name = (
                    rel.get("normalized_label") or
                    rel.get("label") or
                    "related_to"
                ).lower().replace(" ", "_")
                
                # Extract target concept and weight
                start = edge.get("start", {})
                end = edge.get("end", {})
                weight = edge.get("weight", 0.0)
                
                # Determine which concept is the target (not the main concept)
                start_label = (
                    start.get("normalized_label") or
                    start.get("label") or
                    ""
                )
                end_label = (
                    end.get("normalized_label") or
                    end.get("label") or
                    ""
                )
                
                # Clean labels (remove POS tags)
                start_label = self._clean_concept_label(start_label)
                end_label = self._clean_concept_label(end_label)
                
                # Add both directions (start->end and end->start relationships)
                for target_label in [start_label, end_label]:
                    if target_label:
                        if rel_name not in relationships:
                            relationships[rel_name] = []
                        
                        # Check for duplicates
                        existing_terms = [item["term"] for item in relationships[rel_name]]
                        if target_label not in existing_terms:
                            relationships[rel_name].append({
                                "term": target_label,
                                "weight": round(weight, 4)
                            })
                
            except Exception as e:
                self.logger.warning(f"Failed to extract relationship from edge: {e}")
                continue
        
        # Sort each relationship type by weight (highest first)
        for rel_type in relationships:
            relationships[rel_type] = sorted(
                relationships[rel_type],
                key=lambda x: x["weight"],
                reverse=True
            )
        
        return relationships
    
    def _calculate_minimal_summary(
        self,
        data: Dict[str, Any],
        summary_type: str
    ) -> Dict[str, Any]:
        """
        Calculate summary statistics for minimal format responses.
        
        Args:
            data: Data dictionary containing edges, relationships, or related concepts
            summary_type: Type of summary ("concept", "related", "relatedness")
            
        Returns:
            Summary statistics dictionary
        """
        if summary_type == "concept":
            # Summary for concept_lookup/concept_query
            edges = data.get("edges", [])
            relationships = data.get("relationships", {})
            
            weights = [edge.get("weight", 0.0) for edge in edges if edge.get("weight")]
            high_confidence_count = len([w for w in weights if w >= 0.7])
            
            return {
                "total_relationships": len(edges),
                "relationship_types": len(relationships),
                "avg_confidence": round(sum(weights) / len(weights), 3) if weights else 0.0,
                "high_confidence_count": high_confidence_count
            }
            
        elif summary_type == "related":
            # Summary for related_concepts
            related_concepts = data.get("related_concepts", [])
            weights = data.get("weights", [])
            
            return {
                "total_found": len(related_concepts),
                "avg_similarity": round(sum(weights) / len(weights), 3) if weights else 0.0,
                "top_similarity": round(max(weights), 3) if weights else 0.0,
                "similarity_range": [round(min(weights), 3), round(max(weights), 3)] if weights else [0.0, 0.0]
            }
            
        else:
            # Default empty summary
            return {}