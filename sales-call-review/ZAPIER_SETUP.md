# Freedom Team Trading — Post-Call Review Bot (Zapier)

**What it does:** When Fathom finishes processing a sales call, the Zap takes the
transcript, sends it to Claude for a sales-coaching review (summary, the lead's
objections, how the closer handled them, what they could have done better, and
the next steps presented to the client), and posts the review **as a threaded
reply under the call's message in Slack** so the sales manager can review it.

```
Fathom (New Transcript) ─▶ [filter: sales calls only] ─▶ Claude (review)
        │                                                      │
        └──────────────▶ Slack: parent "call recorded" message
                                   └─▶ Slack: threaded reply with Claude's review
```

> **Why Fathom is the trigger (and not Close):** Fathom's Zapier app only offers
> *triggers* — there is **no "Find Recording" action**, so a Zap that starts in
> Close has no way to pull the transcript back out of Fathom. Triggering on
> Fathom's "New Transcript" event hands you the transcript directly in the
> trigger output, which is simpler and more reliable. If you specifically need
> Close to be the starting point (e.g. reps hand-pick which calls get reviewed by
> adding the Fathom link to a lead), see
> [Appendix B](#appendix-b--keep-close-as-the-trigger-fathom-api) — it uses the
> Fathom API instead.

---

## Before you start — accounts you need

| Account | What it's for | Where to get it |
|---------|--------------|-----------------|
| Zapier (Professional plan) | Runs the automation; multi-step Zaps need a paid plan | zapier.com |
| Anthropic | Claude writes the review | console.anthropic.com → API Keys |
| Fathom (**Team plan**) | Records the call + provides the transcript (the trigger) | Already have this ✅ |
| Slack | Where the review is posted for the manager | Already have this ✅ |
| Close *(optional)* | Pull lead/closer context to enrich the review | Already have this ✅ |

> **Which model:** use **`claude-opus-4-8`** in the Anthropic step. Sales-coaching
> review is judgment-heavy (reading objections, evaluating how they were handled),
> and Opus is the strongest model for it. For high call volume on a tighter
> budget, **`claude-sonnet-4-6`** is a drop-in cheaper option — just change the
> model in the dropdown. Use the model ID exactly as written; don't add a date.

---

## One design decision up front: how the Slack thread is created

You asked for the review to go to "the thread of the call on Slack." There are two
ways to get a thread, and they change how you build the Zap:

- **Option A — the Zap owns the thread (recommended).** The Zap posts a short
  parent message ("📞 New call recorded: …"), captures that message's timestamp,
  then posts Claude's review as a *threaded reply* under it. Reliable — the Zap
  always knows which message to thread under. The steps below use Option A.

- **Option B — reply under Fathom's existing Slack post.** If Fathom's native
  Slack integration already auto-posts recordings to a channel, you can reply in
  *that* message's thread instead. Less reliable (the Zap has to *search* for the
  right message). See [Appendix A](#appendix-a--thread-under-fathoms-existing-post).

---

## Covering the whole team

You do **not** connect each rep's Fathom account. Fathom's Zapier trigger can fire
on *"any meetings from team members visible to you,"* so **one** connection from
an account that can see everyone's calls covers the entire team. Requirements:

- **Fathom Team plan.** Team-wide visibility (and some trigger/webhook events) are
  Team-plan features.
- **Connect an admin/owner account** to Zapier — one that can see all reps' sales
  calls.
- **Reps' calls must be visible to that account.** In Fathom's **org settings**,
  make sure recording visibility is set so reps' sales calls are shared with the
  team/admin (not kept private). The trigger only fires for calls the connected
  account can actually see — if a rep's calls are private, they won't flow through.
- On the trigger (Step 1 below), choose the **team members' meetings** scope, not
  "only my meetings."

> Edge cases: a brand-new rep, or one who keeps calls private, won't be covered
> until their visibility is fixed in Fathom. There's nothing to change in Zapier
> per rep — it's all controlled by Fathom visibility + the trigger scope.

---

## Step 1 — Connect the apps to Zapier

1. **Fathom** — connect with an **admin/owner** account that can see the whole
   team's calls (not a single rep's personal account). In Fathom: **Settings →
   Integrations → Zapier**, click Connect, copy the key, and paste it when Zapier
   asks. See [Covering the whole team](#covering-the-whole-team) below — this one
   connection covers every rep, you do **not** connect each person's Fathom.
2. **Anthropic** — add an Anthropic step; paste your API key from
   console.anthropic.com → API Keys.
3. **Slack** — connect the workspace; allow Zapier to post messages. Decide which
   channel the manager reviews in (e.g. `#sales-call-reviews`).
4. **Close** *(optional)* — connect with your Close API key (Settings →
   Developer/API) only if you want to enrich the review with lead/closer info.

---

## Step 2 — Build the Zap

In Zapier click **Create Zap**.

### 🔵 Step 1 — Trigger: Fathom "New Transcript"

- **App:** Fathom
- **Account:** the **admin/owner** Fathom account (from Step 1) — so the trigger
  can see every rep's calls.
- **Event:** **New Transcript** (fires when a call's transcript is ready).
  *("New Meeting Recording" also works, but "New Transcript" guarantees the
  transcript text is present.)*
- **Scope:** when Zapier asks whether to trigger on *only your meetings* or
  *meetings from team members visible to you*, choose **team members' meetings**.
  This is what makes the Zap cover the whole team from one connection.
- **Test:** load a recent call so you have a real transcript to map.
- **What you get:** `Transcript` / `Transcript Plaintext`, meeting **Title**,
  **Date**, **Share URL**, and **attendees** (often with emails).

### 🟡 Step 2 — Filter: only review actual sales calls

Because this now fires on *every* Fathom recording, filter down to sales calls so
internal/team meetings don't get reviewed.

- **App:** Filter by Zapier
- **Use whichever signal fits your setup:**
  - Meeting **Title** *contains* a keyword you use (e.g. `Discovery`, `Sales`,
    `Strategy Call`), **or**
  - An **attendee email domain** is *not* `freedomteamtrading.com` (i.e. an
    external prospect is on the call), **or**
  - The call came from a specific Fathom **team/folder** if you route sales calls
    there.

> If reps already curate calls some other way, adapt the condition to match. The
> goal is simply: continue only for calls worth coaching.

### 🟠 Step 3 *(optional)* — Close: "Find Lead" for context

Skip this if you don't need CRM context in the review.

- **App:** Close
- **Event:** **Find Lead**
- **Search by:** the prospect's email or name from the Fathom attendees (Step 1)
- **What it gives you:** the lead name and **Lead Owner** (the closer), to label
  the Slack message and the review.

> Matching can miss if the prospect's email isn't on the Fathom invite or isn't in
> Close. If it's unreliable for you, drop this step — the review still works from
> the transcript alone.

### 🟣 Step 4 — Slack: post the parent "call recorded" message

This is the message the review threads under.

- **App:** Slack
- **Event:** **Send Channel Message**
- **Channel:** `#sales-call-reviews`
- **Message text:**
  ```
  📞 New sales call recorded — review below in thread
  *Lead:* {{Close Lead Name — or Fathom attendee}}
  *Closer:* {{Close Lead Owner — or Fathom host}}
  *Call:* {{Fathom Title}} ({{Fathom Date}})
  *Recording:* {{Fathom Share URL}}
  ```
- **Important:** Slack's action returns a **`ts`** (Message Timestamp) in its
  output after you test it. You need that in Step 6 to reply in-thread — note
  where it appears.

### 🟤 Step 5 — Anthropic: "Send Message" (Claude writes the review)

- **App:** Anthropic
- **Event:** Send Message
- **Model:** `claude-opus-4-8`  *(or `claude-sonnet-4-6` for lower cost)*
- **Max tokens:** `2000`
- **System / Instructions** (use the system field if present, else put it at the
  top of the message):
  ```
  You are a sales coach reviewing a recorded sales call for Freedom Team Trading,
  a forex and futures trading education brand. Your audience is the SALES MANAGER,
  not the rep. Be specific, direct, and useful — quote the call when it helps.
  Do not invent anything that is not supported by the transcript. If the
  transcript is missing or too short to assess, say so plainly instead of guessing.
  Never coach the rep to make guaranteed-profit or income claims.
  ```
- **Message (user):** paste this, then use the field picker to insert the dynamic
  values where marked:
  ```
  CALL TITLE: [insert Fathom Title from Step 1]
  DATE: [insert Fathom Date from Step 1]
  LEAD: [insert Close Lead Name from Step 3, or Fathom attendee from Step 1]
  CLOSER / REP: [insert Close Lead Owner from Step 3, or Fathom host from Step 1]

  TRANSCRIPT:
  [insert Transcript / Transcript Plaintext from Step 1 - Fathom]

  Write a post-call review for the sales manager. Format it as Slack mrkdwn
  (use *bold* for headers, "- " for bullets, no markdown # headings, no tables).
  Use exactly these five sections, in this order:

  *Summary*
  3-5 sentences: what the call was about, where the lead is in their journey,
  and how the call ended (booked, follow-up, ghosted, closed, lost).

  *Lead's Objections*
  Bullet every objection or hesitation the lead raised (price, timing, trust,
  spouse/partner, "need to think about it", risk, prior bad experience, etc.).
  Quote the lead briefly where it's revealing.

  *How the Closer Handled Them*
  For each objection above, one bullet on how the rep responded and whether it
  landed. Note strong moves and weak or missed responses.

  *What Could Have Been Better*
  3-5 concrete, coachable bullets — specific techniques or moments, not generic
  advice. Tie each to something that actually happened on the call.

  *Next Steps Presented to the Client*
  Bullet the actual next steps / commitments the rep gave the lead (follow-up
  call, deadline, payment plan, materials to send). If none were clearly set,
  say that explicitly — that itself is a coaching point.
  ```

### 🟢 Step 6 — Slack: post the review **in the thread**

- **App:** Slack
- **Event:** **Send Channel Message**
- **Channel:** same channel as Step 4
- **Message text:** map the **Claude response** from Step 5
- **Thread:** set the **"Thread" / "Thread Timestamp (ts)"** field to the **`ts`**
  from **Step 4** (the parent message). That makes this a reply *inside* the
  call's thread instead of a new top-level message.
- **(Optional) Notify the manager:** start the message with `<@MANAGER_SLACK_ID>`
  or `<!subteam^SALES_MANAGERS_ID>` so the manager gets pinged.

### ⚪ Step 7 *(optional)* — Close: log that it was reviewed

If you used Close in Step 3, add a **Close → Update Lead** step to write the Slack
thread link onto the lead, so the review is discoverable from the CRM.

---

## Step 3 — Test end to end

1. Pick a recent **short** sales call in Fathom.
2. In Zapier, test each step top to bottom. Confirm:
   - Step 1 returns a real transcript (not empty).
   - Step 2 passes for a sales call (and would block an internal meeting).
   - Step 4 posts the parent message and exposes a `ts`.
   - Step 5 returns the five-section review.
   - Step 6's reply lands **inside the thread** of Step 4's message.
3. Turn the Zap **on**.

---

## How the sales manager uses it

1. A closer finishes a call → Fathom processes the transcript.
2. Within a few minutes, `#sales-call-reviews` shows a `📞 New sales call`
   message with Claude's full coaching review threaded right under it.
3. The manager opens the thread, reads the review, and replies in the same thread
   with feedback for the rep — call, review, and coaching all in one place.

---

## Quick-start checklist

- [ ] Connect Fathom, Anthropic, and Slack to Zapier (Close optional)
- [ ] Decide the Slack review channel (e.g. `#sales-call-reviews`)
- [ ] Build the Zap: Fathom trigger → filter → (Close find) → Slack parent →
      Claude → Slack thread reply
- [ ] Confirm the review posts **in-thread** under the parent message
- [ ] Do one full end-to-end test with a short real call
- [ ] Turn the Zap on 🚀

---

## Appendix A — thread under Fathom's existing post

Use this only if Fathom's native Slack integration already auto-posts each
recording to a channel and you want the review threaded under *that* message.

Replace Step 4 and Step 6 above with:

1. **Slack: "Find Message"** — search the Fathom channel for the message matching
   this call (by **Title** or lead name from Step 1). Returns the message `ts`.
2. **Filter** — only continue if a message was found. You may need a **Delay**
   step before this so Fathom posts first.
3. **Slack: "Send Channel Message"** — set **Thread (ts)** to the `ts` from Find
   Message, and map Claude's review as the text.

**Why it's less reliable:** the match depends on the title/name being unique and
on Fathom having already posted. Option A avoids both by creating and threading
under its own message.

---

## Appendix B — keep Close as the trigger (Fathom API)

Only do this if you specifically need reps to hand-pick calls by adding the Fathom
link to a Close lead. Because Fathom has **no Zapier action** to fetch a
transcript, you call the **Fathom API** directly with a Webhooks step
(requires Zapier's "Webhooks by Zapier" Premium app + a Fathom API key).

1. **Trigger:** Close **Lead Updated** (fire when a `Fathom Recording URL` custom
   field is filled in).
2. **Filter:** continue only when that field *contains* `fathom.video`.
3. **Webhooks by Zapier → GET:** call the Fathom API for that recording's
   transcript. Set the request URL to the Fathom API transcript endpoint and add
   your Fathom API key as the `Authorization` header. (Get the API key and the
   exact endpoint from Fathom → Settings → API, or their API docs — the endpoint
   takes the recording ID/URL and returns the transcript JSON.)
4. **Anthropic → Send Message:** same prompt as Step 5 above, mapping the
   transcript from the Webhooks GET response.
5. **Slack:** parent message + threaded reply, exactly as Steps 4 and 6 above.
6. **Close → Update Lead:** mark a `Review Sent` checkbox so the same call isn't
   reviewed twice on the next lead edit.

This keeps your original "link on Close kicks it off" flow at the cost of one
extra (Premium) Webhooks step and managing a Fathom API key. For most teams,
triggering on Fathom directly (the main guide) is simpler.
