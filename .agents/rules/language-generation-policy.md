---
description: Always generate tailored CV in Hebrew only by default. Generate English version only when explicitly requested by the user.
globs: *
---

# Language Generation Policy

- **Default Language: Hebrew Only:**
  - By default, always generate tailored CVs in Hebrew (`CV_<Company>_HE.html` and `CV_<Company>_HE.md`).
  - Do NOT generate English CV versions automatically.
- **English Opt-In:**
  - Only generate English CV (`CV_<Company>_EN.*`) if the user explicitly asks for an English version.
