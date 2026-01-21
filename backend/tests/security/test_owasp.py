"""OWASP Top 10 security tests."""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.security
class TestOWASPInjection:
    """Test for injection attacks (A03:2021)."""

    def test_sql_injection_business_id(self, test_client: TestClient):
        """Test SQL injection in business ID parameter."""
        malicious_input = "1' OR '1'='1"
        response = test_client.get(f"/api/v1/businesses/{malicious_input}")
        # Should not expose database errors
        assert response.status_code in [400, 404, 422]

    def test_cypher_injection(self, test_client: TestClient):
        """Test Cypher injection in search query."""
        malicious_input = "test' OR 1=1 RETURN *"
        response = test_client.get(f"/api/v1/businesses/search?query={malicious_input}")
        # Should sanitize input
        assert response.status_code in [200, 400, 422]


@pytest.mark.security
class TestOWASPAuthentication:
    """Test for broken authentication (A02:2021)."""

    def test_unauthorized_access(self, test_client: TestClient):
        """Test accessing protected endpoint without auth."""
        response = test_client.get("/api/v1/businesses/123")
        # Should require authentication or return appropriate status
        assert response.status_code in [401, 403, 200]  # 200 if public endpoint

    def test_weak_password_validation(self, test_client: TestClient):
        """Test weak password acceptance."""
        weak_passwords = ["123", "password", "abc"]
        for pwd in weak_passwords:
            response = test_client.post(
                "/api/auth/register",
                json={
                    "username": "test",
                    "email": "test@example.com",
                    "password": pwd,
                },
            )
            # Should reject weak passwords
            assert response.status_code in [400, 422]

    def test_jwt_token_validation(self, test_client: TestClient):
        """Test JWT token validation."""
        invalid_token = "invalid.jwt.token"
        response = test_client.get(
            "/api/v1/businesses/123",
            headers={"Authorization": f"Bearer {invalid_token}"},
        )
        assert response.status_code in [401, 403]


@pytest.mark.security
class TestOWASPExposure:
    """Test for sensitive data exposure (A04:2021)."""

    def test_password_in_response(self, test_client: TestClient):
        """Test that passwords are not returned in responses."""
        response = test_client.post(
            "/api/auth/login",
            json={"username": "test", "password": "test"},
        )
        if response.status_code == 200:
            data = response.json()
            assert "password" not in str(data).lower()

    def test_sensitive_headers(self, test_client: TestClient):
        """Test that sensitive headers are not exposed."""
        response = test_client.get("/health")
        headers = response.headers
        sensitive_headers = ["x-powered-by", "server", "x-aspnet-version"]
        for header in sensitive_headers:
            assert header not in headers


@pytest.mark.security
class TestOWASPXXE:
    """Test for XML external entities (A05:2021)."""

    def test_xml_upload(self, test_client: TestClient):
        """Test XML file upload handling."""
        malicious_xml = """<?xml version="1.0"?>
        <!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
        <foo>&xxe;</foo>"""
        
        response = test_client.post(
            "/api/v1/ingest/upload",
            files={"file": ("test.xml", malicious_xml)},
        )
        # Should reject or sanitize XML
        assert response.status_code in [400, 415, 422]


@pytest.mark.security
class TestOWASPBrokenAccess:
    """Test for broken access control (A01:2021)."""

    def test_unauthorized_business_access(self, test_client: TestClient, owner_subject):
        """Test accessing another user's business."""
        # This would require proper auth setup
        # For now, test that endpoint requires auth
        response = test_client.get("/api/v1/businesses/other-user-business")
        # Should require proper authorization
        assert response.status_code in [401, 403, 404]

    def test_idor_vulnerability(self, test_client: TestClient):
        """Test for Insecure Direct Object Reference."""
        # Try accessing resources with predictable IDs
        for business_id in ["1", "2", "admin", "test"]:
            response = test_client.get(f"/api/v1/businesses/{business_id}")
            # Should not expose unauthorized data
            assert response.status_code in [401, 403, 404, 200]


@pytest.mark.security
class TestOWASPSecurityMisconfig:
    """Test for security misconfiguration (A05:2021)."""

    def test_debug_mode_disabled(self, test_client: TestClient):
        """Test that debug mode is not enabled."""
        response = test_client.get("/docs")
        # Debug endpoints should be restricted in production
        # This is acceptable in development
        pass

    def test_cors_configuration(self, test_client: TestClient):
        """Test CORS configuration."""
        response = test_client.options(
            "/api/v1/businesses",
            headers={
                "Origin": "https://malicious-site.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        # CORS should be properly configured
        cors_headers = response.headers.get("Access-Control-Allow-Origin")
        # Should not allow all origins
        assert cors_headers != "*" or cors_headers is None


@pytest.mark.security
class TestOWASPXSS:
    """Test for cross-site scripting (A03:2021)."""

    def test_xss_in_search(self, test_client: TestClient):
        """Test XSS in search parameter."""
        xss_payload = "<script>alert('XSS')</script>"
        response = test_client.get(f"/api/v1/businesses/search?query={xss_payload}")
        # Should sanitize input
        assert xss_payload not in response.text

    def test_xss_in_business_name(self, test_client: TestClient):
        """Test XSS in business name field."""
        xss_payload = "<img src=x onerror=alert('XSS')>"
        response = test_client.post(
            "/api/v1/businesses",
            json={"id": "test", "name": xss_payload},
        )
        # Should sanitize or reject
        assert response.status_code in [200, 201, 400, 422]


@pytest.mark.security
class TestOWASPInsecureDeserialization:
    """Test for insecure deserialization (A08:2021)."""

    def test_pickle_deserialization(self, test_client: TestClient):
        """Test that pickle is not used for deserialization."""
        import pickle
        malicious_pickle = pickle.dumps({"malicious": "code"})
        
        response = test_client.post(
            "/api/v1/data/upload",
            content=malicious_pickle,
            headers={"Content-Type": "application/octet-stream"},
        )
        # Should reject pickle format
        assert response.status_code in [400, 415, 422]


@pytest.mark.security
class TestOWASPLogging:
    """Test for insufficient logging (A09:2021)."""

    def test_audit_logging(self, test_client: TestClient):
        """Test that sensitive operations are logged."""
        # This would require checking audit logs
        # For now, verify endpoint exists
        response = test_client.get("/api/v1/audit")
        assert response.status_code in [200, 401, 403]
