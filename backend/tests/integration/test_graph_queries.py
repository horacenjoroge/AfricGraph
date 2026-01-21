"""Integration tests for graph queries."""
import pytest
from unittest.mock import Mock, patch


@pytest.mark.integration
@pytest.mark.graph
class TestGraphQueries:
    """Test graph query operations."""

    @patch("src.graph.traversal.neo4j_client")
    def test_extract_subgraph(self, mock_client):
        """Test subgraph extraction."""
        from src.graph.traversal import extract_subgraph
        
        mock_client.execute_cypher.return_value = [
            {
                "nodes": [
                    {"id": "node-1", "labels": ["Business"], "properties": {"name": "Test"}},
                ],
                "relationships": [],
            }
        ]
        
        result = extract_subgraph("node-1", max_hops=2)
        assert len(result.nodes) > 0

    @patch("src.graph.traversal.neo4j_client")
    def test_find_shortest_path(self, mock_client):
        """Test shortest path finding."""
        from src.graph.traversal import find_shortest_path
        
        mock_client.execute_cypher.return_value = [
            {
                "path": {
                    "nodes": [
                        {"id": "node-1"},
                        {"id": "node-2"},
                    ],
                    "relationships": [
                        {"type": "OWNS", "id": "rel-1"},
                    ],
                }
            }
        ]
        
        result = find_shortest_path("node-1", "node-2")
        assert result is not None
        assert len(result.nodes) == 2

    @patch("src.graph.cycles.neo4j_client")
    def test_detect_cycles(self, mock_client):
        """Test cycle detection."""
        from src.graph.cycles import detect_cycles
        
        mock_client.execute_cypher.return_value = [
            {
                "cycle": [
                    {"id": "node-1"},
                    {"id": "node-2"},
                    {"id": "node-3"},
                    {"id": "node-1"},
                ]
            }
        ]
        
        cycles = detect_cycles("node-1")
        assert len(cycles) > 0

    @patch("src.graph.relationship_search.neo4j_client")
    def test_find_connections(self, mock_client):
        """Test finding connections between entities."""
        from src.graph.relationship_search import find_connections
        
        mock_client.execute_cypher.return_value = [
            {
                "path": {
                    "nodes": [
                        {"id": "entity-1"},
                        {"id": "entity-2"},
                    ],
                    "relationships": [
                        {"type": "OWNS", "id": "rel-1"},
                    ],
                },
                "strength": 0.8,
            }
        ]
        
        connections = find_connections("entity-1", "entity-2", max_depth=3)
        assert len(connections) > 0
        assert connections[0].strength > 0
