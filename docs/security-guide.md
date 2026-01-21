# Security Guide

This guide covers security best practices, configuration, and procedures for AfricGraph.

## Security Architecture

### Authentication

- **JWT Tokens**: Stateless authentication with configurable expiration
- **Password Hashing**: bcrypt with appropriate cost factor
- **Session Management**: Redis-based session storage

### Authorization (ABAC)

- **Fine-Grained Access Control**: Based on user attributes, resource attributes, and environment
- **Role-Based Permissions**: Admin, Owner, Analyst, Auditor roles
- **Time-Based Restrictions**: Business hours enforcement
- **IP-Based Restrictions**: Optional IP whitelisting

### Data Protection

- **Encryption at Rest**: Database-level encryption
- **Encryption in Transit**: TLS/SSL for all connections
- **Sensitive Data Masking**: Logs and responses
- **Audit Logging**: All access and modifications logged

## Security Configuration

### Environment Variables

Secure sensitive configuration:

```bash
# Strong passwords
NEO4J_PASSWORD=$(openssl rand -base64 32)
POSTGRES_PASSWORD=$(openssl rand -base64 32)
JWT_SECRET_KEY=$(openssl rand -base64 64)

# Restrict CORS
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### JWT Configuration

```bash
# Strong secret key (minimum 32 characters)
JWT_SECRET_KEY=your_very_long_random_secret_key_here

# Reasonable expiration (24 hours default)
JWT_EXPIRATION_HOURS=24

# Use secure algorithm
JWT_ALGORITHM=HS256
```

### Database Security

#### Neo4j

- Use strong passwords
- Enable authentication
- Restrict network access
- Regular security updates

#### PostgreSQL

- Use strong passwords
- Enable SSL connections
- Restrict network access
- Regular security updates

### Network Security

#### Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (for Let's Encrypt)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

#### Nginx Security Headers

Configured in `deployment/nginx/africgraph.conf`:
- Strict-Transport-Security
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Referrer-Policy

## Security Best Practices

### Password Management

1. **Strong Passwords**
   - Minimum 12 characters
   - Mix of uppercase, lowercase, numbers, symbols
   - No dictionary words

2. **Password Rotation**
   - Rotate passwords regularly
   - Use password manager
   - Never share passwords

3. **Multi-Factor Authentication**
   - Enable MFA when available
   - Use authenticator apps

### Access Control

1. **Principle of Least Privilege**
   - Grant minimum necessary permissions
   - Regular access reviews
   - Remove unused accounts

2. **Role-Based Access**
   - Use appropriate roles
   - Don't grant admin unnecessarily
   - Review permissions regularly

### Data Security

1. **Sensitive Data**
   - Encrypt sensitive data
   - Mask in logs
   - Limit access

2. **Backup Security**
   - Encrypt backups
   - Secure backup storage
   - Test restore procedures

### Application Security

1. **Input Validation**
   - Validate all inputs
   - Sanitize user data
   - Use parameterized queries

2. **Error Handling**
   - Don't expose internal errors
   - Log errors securely
   - Return generic messages

3. **Dependencies**
   - Keep dependencies updated
   - Review security advisories
   - Use trusted sources

## Security Monitoring

### Audit Logging

All security-relevant events are logged:
- Authentication attempts
- Authorization decisions
- Data access
- Configuration changes

### Monitoring

Monitor for:
- Failed login attempts
- Unusual access patterns
- High error rates
- Performance anomalies

### Alerting

Configure alerts for:
- Multiple failed logins
- Unauthorized access attempts
- Security configuration changes
- System vulnerabilities

## Incident Response

### Security Incident Procedure

1. **Identify**
   - Detect security incident
   - Assess severity
   - Preserve evidence

2. **Contain**
   - Isolate affected systems
   - Block malicious access
   - Preserve logs

3. **Eradicate**
   - Remove threat
   - Patch vulnerabilities
   - Rotate credentials

4. **Recover**
   - Restore from clean backup
   - Verify system integrity
   - Resume operations

5. **Review**
   - Post-incident review
   - Update procedures
   - Improve security

### Reporting Security Issues

Report security vulnerabilities:
- Email: security@africgraph.com
- Include: Description, steps to reproduce, impact
- Do not disclose publicly until fixed

## Compliance

### Data Protection

- Follow data protection regulations
- Implement data retention policies
- Provide data export/deletion

### Audit Requirements

- Maintain audit logs
- Regular security audits
- Compliance reporting

## Security Checklist

### Initial Setup

- [ ] Strong passwords set
- [ ] JWT secret key generated
- [ ] SSL certificate installed
- [ ] Firewall configured
- [ ] Fail2ban enabled
- [ ] Security headers configured
- [ ] CORS properly configured
- [ ] Audit logging enabled

### Regular Maintenance

- [ ] Update dependencies
- [ ] Review access logs
- [ ] Rotate credentials
- [ ] Review security advisories
- [ ] Test backup restore
- [ ] Security audit

### Incident Preparedness

- [ ] Incident response plan documented
- [ ] Backup procedures tested
- [ ] Recovery procedures tested
- [ ] Contact information updated

## Security Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
