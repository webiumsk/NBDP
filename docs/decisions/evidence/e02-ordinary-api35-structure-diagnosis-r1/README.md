# API35 v2 structural guard diagnosis

The added v2 fingerprint was overstrict: its only differing datum was the eye
button sibling index3->2 after the placeholder TextView disappeared. Field and
eye roles, package/class/resource IDs and shown state remained unchanged.
The whole public synthetic NSEC is exact in actual ui010 XML and visibly shown
across three lines in PNG. Bounds reflowed; bounds were not compared by this
fingerprint. v2 remains FAILED_UNQUALIFIED with successful four-container cleanup.

`diagnosis.json` separates raw observations, pinned source inspection and
inference, and records the precise synthetic-control coverage gap. `inputs/`
preserves exact source/UI/command/result bytes. No old source or result changed.
No test, project import, Android, SDK, service or lease was executed.

Recommended correction requires separate authorization/review: exclude mutable
positional indices from semantic shape comparison, retain all current closed
recognition/whole-value/shown-state/budget gates, and never claim object identity
from empty resource IDs and accessibility tree positions. Add the actual
ui009->ui010 disappearing-placeholder regression and retain meaningful negatives.
