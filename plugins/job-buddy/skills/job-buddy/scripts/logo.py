"""The Buddy Social wordmark as a transparency mask for the dashboard header and footer.

Source: the logo supplied by Aditya Bhatnagar (The Buddy Social), 500x500 PNG, forest green on
cream. Converted to an alpha-only PNG (ink coverage measured against the cream ground, cropped,
200px tall) so the page can colour it from the theme with CSS mask-image. Not generated.
The image ships as logo-mask.png next to this file; this reads it and base64-encodes it.
"""

import base64
from pathlib import Path

LOGO_MASK_PNG_B64 = base64.b64encode(
    (Path(__file__).resolve().parent / "logo-mask.png").read_bytes()).decode("ascii")
