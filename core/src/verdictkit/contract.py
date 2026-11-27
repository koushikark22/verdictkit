"""The HTTP/MCP contract version, defined once (design D5.8 lockstep rule).

1.2.0 changes only the ``authenticity`` object: it now carries the signature results of
design D5. Every field of 1.1.0 is preserved. Other candidate changes of the design's joint
1.2.0 event (health ``commitSha``, owner cookie, new 429 routes) are not part of this version.
"""
CONTRACT_VERSION = "1.2.0"
