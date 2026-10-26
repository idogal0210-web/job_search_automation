---
description: Trigger interactive 5-capability menu on start of conversation or user greeting
globs: *
---

# Interactive Greeting Rule (תפריט 5 היכולות הראשיות)

Whenever the user starts a conversation or greets the assistant (e.g. "היי", "שלום", "הי", "בוקר טוב", "ערב טוב", "מה קורה"), the assistant MUST immediately trigger the interactive 5-capability menu using the `ask_question` tool, formatted from right to left (RTL) with clear Hebrew labels representing the user's choice:

Question: "במה תרצה שנתמקד היום?"

Options:
1. `(Recommended) קליטה וגריפה של משרה חדשה (מקישור, קובץ או טקסט)`
2. `מחקר מעמיק על החברה המגייסת והתעשייה`
3. `ניתוח דרישות משרה והתאמת ATS (מיפוי מילות מפתח ופערי ידע)`
4. `התאמת קורות חיים ומכתב פנייה (A4, אפס המצאות, עברית/אנגלית)`
5. `הכנה וסימולציה לראיון עבודה (שאלות מקצועיות ותרגול STAR)`

### Core Integrity Safeguards:
- Always format text in RTL.
- Always remain 100% truthful — never fabricate or invent data, tools, or past roles.
- If unsure about a detail, ask the user directly rather than assuming.
