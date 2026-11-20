"""Third-domain reuse proof (core task 12, requirement core 10.3).

Receipt-total claim type with zero changes to core modules.
Loaded automatically by the CLI when VK_CLAIM_TYPES is set, or when this
package is installed and its entry-point is registered.
"""
from .receipt import ReceiptClaimType

CLAIM_TYPE = ReceiptClaimType
