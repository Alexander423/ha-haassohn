# Security policy

## Supported versions

Only the latest development release and the current default branch receive fixes.
Physical hardware validation is still outstanding.

## Reporting a vulnerability

Use GitHub's **Security → Report a vulnerability** in this repository for private
reports. Do not disclose vulnerabilities or sensitive appliance data in public
issues. Include the affected version, impact and a minimal sanitized reproduction.
Never send your PIN, nonce, serial number, network address or full status capture.

## Network boundary

Legacy stove modules use unencrypted local HTTP. Keep the module on a trusted
local network; do not expose it to the Internet. The integration cannot add TLS
to the appliance. Command signatures do not provide transport encryption.

The stove's built-in safety controls remain authoritative. See
[the safety design](docs/safety.md) for command and retry restrictions.
