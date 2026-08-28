handoffs/ -- handoff packets go here

At the end of each round of work, the AI leaves a packet here describing
what that round did. The format is defined in policy/HANDOFF.md.

Why this exists:
Whoever picks up the next round -- person or AI -- will not remember what
happened in the last one. Work with no handoff packet is work that may as
well not have happened, because nobody can check what it did or what it missed.

⛔ This folder is append-only. Do not go back and edit a packet already handed over.
   To correct one, write a new packet that says what it corrects.

⚠️ This note is deliberately a .txt, not a .md:
   every .md in this folder is checked as a handoff packet (author field and
   model identifier included). A note would fail those checks -- and it should,
   because it is not a packet.
