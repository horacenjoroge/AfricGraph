"""Example integration tests using seed data fixtures."""
import pytest


@pytest.mark.integration
class TestSeedDataFixtures:
    """Example tests demonstrating seed data fixture usage."""

    def test_seeded_business_ids(self, sample_business_ids):
        """Test that seeded business IDs are available."""
        assert len(sample_business_ids) == 20
        assert all(bid.startswith("BIZ") for bid in sample_business_ids)

    def test_seeded_person_ids(self, sample_person_ids):
        """Test that seeded person IDs are available."""
        assert len(sample_person_ids) == 15
        assert all(pid.startswith("PERSON") for pid in sample_person_ids)

    def test_single_business_id(self, sample_business_id):
        """Test accessing a single business ID."""
        assert sample_business_id is not None
        assert sample_business_id.startswith("BIZ")

    def test_seeded_data_structure(self, seeded_test_data):
        """Test the structure of seeded test data."""
        assert "business_ids" in seeded_test_data
        assert "person_ids" in seeded_test_data
        assert len(seeded_test_data["business_ids"]) == 20
        assert len(seeded_test_data["person_ids"]) == 15

    def test_minimal_test_data(self, minimal_test_data):
        """Test minimal test data fixture."""
        assert len(minimal_test_data["business_ids"]) == 3
        assert len(minimal_test_data["person_ids"]) == 2
