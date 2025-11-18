# Islands Analysis

This file documents all sections that are "islands" - sections that exist but have no incoming links from other sections. These sections are unreachable through normal gameplay.

**What this means:**
- These sections cannot be reached by following choices from other sections
- They need to either be connected to the story (by adding a choice that points to them) or terminated
- Sections with choices need partial termination (remove or modify choices)
- Sections without choices are already terminated but may need story connection

---

## Islands with Choices (Need Partial Termination)

These sections have choices but are unreachable. They need to either:
- Have their choices removed/modified to terminate the branch, or
- Be connected to the story by adding a choice from another section that points to them

### section-24.md - "Gathering Clues"

**Section ID:** `section-24`

**Choices:**
- Choice 1: "Re-interview Marcus about his alibi" → `section-41.md`
- Choice 2: "Interview Velma about what she saw" → `section-42.md`
- Choice 3: "Talk to Officer Martinez about the investigation" → `section-43.md`

### section-25.md - "Red Herrings"

**Section ID:** `section-25`

**Choices:**
- Choice 1: "Reconstruct the timeline of what happened" → `section-44.md`
- Choice 2: "Investigate the motives of each suspect" → `section-45.md`
- Choice 3: "Search for connections between the suspects" → `section-46.md`

### section-254.md - "Suppressed Magic"

**Section ID:** `section-254`

**Choices:**
- Choice 1: "Accept this as the solution" → `section-255.md`
- Choice 2: "Investigate further - something feels wrong" → `section-256.md`

### section-260.md - "Kvothe's Suppression"

**Section ID:** `section-260`

**Choices:**
- Choice 1: "Accept that Kvothe is fine" → `section-261.md`
- Choice 2: "Notice that something seems off" → `section-262.md`

### section-27.md - "The Truth Emerges"

**Section ID:** `section-27`

**Choices:**
- Choice 1: "Confront Marcus with the evidence" → `section-50.md`
- Choice 2: "Gather final proof before confronting anyone" → `section-51.md`
- Choice 3: "Present everything to Officer Martinez" → `section-52.md`

### section-270.md - "False Balance"

**Section ID:** `section-270`

**Choices:**
- Choice 1: "Accept that the magic is flowing correctly" → `section-271.md`
- Choice 2: "Investigate - something feels off" → `section-272.md`

### section-280.md - "Surface Mastery"

**Section ID:** `section-280`

**Choices:**
- Choice 1: "Accept that you've mastered the magic" → `section-281.md`
- Choice 2: "Realize there's more to learn" → `section-282.md`

### section-290.md - "Shallow Understanding"

**Section ID:** `section-290`

**Choices:**
- Choice 1: "Accept that everyone understands" → `section-291.md`
- Choice 2: "Notice that the understanding seems shallow" → `section-292.md`

### section-295.md - "Perfect Celebration"

**Section ID:** `section-295`

**Choices:**
- Choice 1: "Accept that the celebration is perfect" → `section-296.md`
- Choice 2: "Notice that underlying issues are being ignored" → `section-297.md`

### section-351.md - "Kvothe's True Transformation"

**Section ID:** `section-351`

**Choices:**
- Choice 1: "Continue to the ultimate resolution" → `section-391.md`

### section-352.md - "Perfect Flow"

**Section ID:** `section-352`

**Choices:**
- Choice 1: "Continue to the ultimate resolution" → `section-391.md`

### section-353.md - "True Mastery"

**Section ID:** `section-353`

**Choices:**
- Choice 1: "Continue to the ultimate resolution" → `section-391.md`

### section-354.md - "Full Understanding"

**Section ID:** `section-354`

**Choices:**
- Choice 1: "Continue to the ultimate resolution" → `section-391.md`

### section-355.md - "Perfect Celebration"

**Section ID:** `section-355`

**Choices:**
- Choice 1: "Continue to the ultimate resolution" → `section-391.md`

### section-89.md - "False Ending: Accusing Velma"

**Section ID:** `section-89`

**Choices:**
- Choice 1: "Realize your mistake and rethink the investigation" → `section-26.md`
- Choice 2: "Accept this conclusion" → `section-90.md`

### section-91.md - "False Ending: Accusing Alistair"

**Section ID:** `section-91`

**Choices:**
- Choice 1: "Realize your mistake and rethink the investigation" → `section-26.md`
- Choice 2: "Accept this conclusion" → `section-92.md`

### section-93.md - "False Ending: Incomplete Investigation"

**Section ID:** `section-93`

**Choices:**
- Choice 1: "Go back and gather more evidence" → `section-26.md`
- Choice 2: "Accept this conclusion" → `section-94.md`

---

## Unknown Starts

These sections have incoming links but are only reachable through unreachable (island) sections. They appear to have connections, but those connections come from sections that cannot be reached from the start.

**What this means:**
- These sections have choices pointing to them, but those choices are in unreachable sections
- They are effectively unreachable even though they appear to have incoming links
- They need to either be connected to the story from a reachable section, or the unreachable sections pointing to them need to be connected

### section-256.md - "Finding the Real Solution"

**Section ID:** `section-256`

**Referenced by unreachable sections:**
- `section-254.md` (choice: "Investigate further - something feels wrong")

**Choices:**
- Choice 1: "Work to truly balance the magic, not suppress it" → `section-300.md`

### section-26.md - "Narrowing the Field"

**Section ID:** `section-26`

**Referenced by unreachable sections:**
- `section-89.md` (choice: "Realize your mistake and rethink the investigation")
- `section-91.md` (choice: "Realize your mistake and rethink the investigation")
- `section-93.md` (choice: "Go back and gather more evidence")

**Choices:**
- Choice 1: "Confront Marcus about the inconsistencies in his story" → `section-47.md`
- Choice 2: "Search for where the silver button came from" → `section-48.md`
- Choice 3: "Investigate Alistair Finch's connection to the case" → `section-49.md`

### section-262.md - "Helping Kvothe Truly Transform"

**Section ID:** `section-262`

**Referenced by unreachable sections:**
- `section-260.md` (choice: "Notice that something seems off")

**Choices:**
- Choice 1: "Help Kvothe face their true self and truly transform" → `section-301.md`

### section-272.md - "True Balance"

**Section ID:** `section-272`

**Referenced by unreachable sections:**
- `section-270.md` (choice: "Investigate - something feels off")

**Choices:**
- Choice 1: "Work to truly balance the magic flow" → `section-302.md`

### section-282.md - "True Mastery"

**Section ID:** `section-282`

**Referenced by unreachable sections:**
- `section-280.md` (choice: "Realize there's more to learn")

**Choices:**
- Choice 1: "Go deeper and truly master the magic" → `section-303.md`

### section-292.md - "Deep Understanding"

**Section ID:** `section-292`

**Referenced by unreachable sections:**
- `section-290.md` (choice: "Notice that the understanding seems shallow")

**Choices:**
- Choice 1: "Help everyone go deeper and truly understand" → `section-304.md`

### section-297.md - "Addressing the Issues"

**Section ID:** `section-297`

**Referenced by unreachable sections:**
- `section-295.md` (choice: "Notice that underlying issues are being ignored")

**Choices:**
- Choice 1: "Address the underlying issues while celebrating" → `section-305.md`

### section-255.md - "The Explosion"

**Section ID:** `section-255`

**Referenced by unreachable sections:**
- `section-254.md` (choice: "Accept this as the solution")

*This section has no choices and is already terminated.*

### section-261.md - "Kvothe's Breaking Point"

**Section ID:** `section-261`

**Referenced by unreachable sections:**
- `section-260.md` (choice: "Accept that Kvothe is fine")

*This section has no choices and is already terminated.*

### section-271.md - "The Collapse"

**Section ID:** `section-271`

**Referenced by unreachable sections:**
- `section-270.md` (choice: "Accept that the magic is flowing correctly")

*This section has no choices and is already terminated.*

### section-281.md - "Shallow Understanding"

**Section ID:** `section-281`

**Referenced by unreachable sections:**
- `section-280.md` (choice: "Accept that you've mastered the magic")

*This section has no choices and is already terminated.*

### section-291.md - "The Crumble"

**Section ID:** `section-291`

**Referenced by unreachable sections:**
- `section-290.md` (choice: "Accept that everyone understands")

*This section has no choices and is already terminated.*

### section-296.md - "Problems Emerge"

**Section ID:** `section-296`

**Referenced by unreachable sections:**
- `section-295.md` (choice: "Accept that the celebration is perfect")

*This section has no choices and is already terminated.*

### section-90.md - "The Wrong Conclusion"

**Section ID:** `section-90`

**Referenced by unreachable sections:**
- `section-89.md` (choice: "Accept this conclusion")

*This section has no choices and is already terminated.*

### section-92.md - "The Red Herring"

**Section ID:** `section-92`

**Referenced by unreachable sections:**
- `section-91.md` (choice: "Accept this conclusion")

*This section has no choices and is already terminated.*

### section-94.md - "Rushing to Judgment"

**Section ID:** `section-94`

**Referenced by unreachable sections:**
- `section-93.md` (choice: "Accept this conclusion")

*This section has no choices and is already terminated.*

---

## Summary

Total island sections: **17**

- Islands with choices (need partial termination): **17**
- Islands without choices (already terminated): **0**

Total unknown start sections: **16**

- Unknown starts with choices: **7**
- Unknown starts without choices (already terminated): **9**
