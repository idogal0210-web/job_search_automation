"""Shared anti-SSRF guard for outbound HTTP fetches triggered by user-supplied URLs.

Policy:
- Only http/https schemes with a hostname are accepted.
- Every resolved address must be globally routable (``ipaddress.is_global``), for both
  literal IPs and DNS names. This rejects RFC1918, loopback, link-local, CGNAT
  (100.64.0.0/10), reserved, multicast and unspecified ranges.
- Redirects are followed manually; every hop is re-validated.
- After the TCP connection is established, the actual peer address is verified again,
  which closes the DNS-rebinding window between validation and connection.
"""

import ipaddress
import socket
from typing import Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests

MAX_REDIRECTS = 5
_BLOCKED_HOSTNAMES = {"localhost", "localhost.localdomain", "ip6-localhost", "ip6-loopback"}


class UnsafeUrlError(ValueError):
    """Raised when a URL or redirect target resolves to a non-public address."""


def is_public_ip(addr_str: str) -> bool:
    """Return True only for globally routable unicast addresses."""
    try:
        addr = ipaddress.ip_address(addr_str.split("%")[0])
    except ValueError:
        return False
    if isinstance(addr, ipaddress.IPv6Address) and addr.ipv4_mapped is not None:
        addr = addr.ipv4_mapped
    return bool(addr.is_global) and not addr.is_multicast


def validate_public_http_url(url: str) -> Tuple[bool, str]:
    """Validate that URL uses http/https and resolves only to public IP addresses."""
    raw = (url or "").strip()
    if not raw:
        return False, "כתובת URL ריקה."
    parsed = urlparse(raw)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc or not parsed.hostname:
        return False, "נתמכות כתובות http ו-https תקינות בלבד."
    if parsed.username or parsed.password:
        return False, "כתובות הכוללות פרטי התחברות אינן מורשות."
    host = parsed.hostname.strip().lower().rstrip(".")
    if host in _BLOCKED_HOSTNAMES or host.endswith(".localhost"):
        return False, "כתובת פנימית (localhost) אינה מורשית לגריפה."

    try:
        ipaddress.ip_address(host)
        is_literal = True
    except ValueError:
        is_literal = False
    if is_literal:
        if not is_public_ip(host):
            return False, "כתובת IP פנימית או שמורה אינה מורשית לגריפה."
        return True, ""

    try:
        infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except (OSError, UnicodeError):
        return False, "לא ניתן היה לפתור את שם הדומיין (DNS)."
    if not infos:
        return False, "לא ניתן היה לפתור את שם הדומיין (DNS)."
    for info in infos:
        if not is_public_ip(str(info[4][0])):
            return False, "הדומיין מצביע לכתובת רשת פנימית ואינו מורשה לגריפה."
    return True, ""


def _peer_address(resp: requests.Response) -> Optional[str]:
    """Best-effort extraction of the connected peer IP from a streamed response."""
    try:
        conn = getattr(resp.raw, "connection", None)
        sock = getattr(conn, "sock", None) if conn is not None else None
        if sock is None:
            return None
        return str(sock.getpeername()[0])
    except (OSError, AttributeError, IndexError):
        return None


def safe_get(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 20,
    max_redirects: int = MAX_REDIRECTS,
    max_bytes: int = 5 * 1024 * 1024,
) -> requests.Response:
    """GET a public URL, validating every redirect hop and the connected peer address.

    Raises UnsafeUrlError for any non-public target and requests exceptions for transport errors.
    The returned response has its body fully read (bounded by max_bytes).
    """
    current = url
    with requests.Session() as session:
        for _ in range(max_redirects + 1):
            ok, reason = validate_public_http_url(current)
            if not ok:
                raise UnsafeUrlError(reason)
            resp = session.get(current, headers=headers, timeout=timeout, allow_redirects=False, stream=True)
            peer = _peer_address(resp)
            if peer is not None and not is_public_ip(peer):
                resp.close()
                raise UnsafeUrlError("החיבור הופנה לכתובת רשת פנימית ונחסם.")
            if resp.is_redirect or resp.is_permanent_redirect:
                location = resp.headers.get("Location", "")
                resp.close()
                if not location:
                    raise UnsafeUrlError("הפניה ללא יעד.")
                current = urljoin(current, location)
                continue
            chunks = []
            total = 0
            for chunk in resp.iter_content(chunk_size=65536):
                total += len(chunk)
                if total > max_bytes:
                    resp.close()
                    raise UnsafeUrlError("גודל העמוד חורג מן המגבלה.")
                chunks.append(chunk)
            resp._content = b"".join(chunks)  # noqa: SLF001 - materialize bounded body
            resp._content_consumed = True  # noqa: SLF001
            return resp
    raise UnsafeUrlError("מספר ההפניות חורג מן המגבלה.")
