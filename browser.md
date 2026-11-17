# griselda's browser rules (browser.md)

Read this before any read_url or browsing task. These are your own rules, not Kyle's orders.

1. Pace yourself. Wait 3-5 seconds between loads on the same site. Never more than about 10 fetches per hour per domain.
2. Cheapest route first. For reddit use the .json endpoint (append .json to the url) or old.reddit.com. Try plain html before rendering JavaScript; render only when the data needs it.
3. Rotate user agents between loads. Never fire the same UA twice in a burst.
4. Wait for the content you actually need (the element or text), not a fixed long sleep.
5. If a page blocks you (403, 429, captcha, blank wall): stop. Write the domain and time to brain_notes.txt, leave the task with a note, and move to the next one. Retry that domain after about a day. Never retry the same url in a burst.
6. Log what you fetched. A page you couldn't read is a task to reschedule, not a failure loop.
