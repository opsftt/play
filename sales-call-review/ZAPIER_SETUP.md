# Freedom Team Trading — Post-Call Review Bot (Zapier)

**What it does:** When a Fathom recording link lands on a Close lead, the Zap
pulls the call transcript from Fathom, sends it to Claude for a sales-coaching
review (summary, the lead's objections, how the closer handled them, what they
could have done better, and the next steps presented to the client), and posts
the review **as a threaded reply under the call's message in Slack** so the
sales manager can review it.

```
Close (Fathom link added) ─▶ Fathom (transcript) ─▶ Claude (review)
        │                                                  │
        └────────────▶ Slack: parent "call recorded" message
                                  └─▶ Slack: threaded reply with Claude's review
```

---

## Before you start — accounts you need

| Account | What it's for | Where to get it |
|---------|--------------|-----------------|
| Zapier (Professional plan) | Runs the automation. Multi-step + paths need a paid plan | zapier.com |
| Anthropic | Claude writes the review | console.anthropic.com → API Keys |
| Close | The CRM the Fathom link is added to | Already have this ✅ |
| Fathom | Records the call + holds the transcript | Already have this ✅ |
| Slack | Where the review is posted for the manager | Already have this ✅ |

> **Which model:** use **`claude-opus-4-8`** in the Anthropic step. Sales-coaching
> review is judgment-heavy (reading objections, evaluating how they were handled),
> and Opus is the strongest model for that. If you run a high volume of calls and
> want to cut cost, **`claude-sonnet-4-6`** is the cheaper fallback — switch the
> model in the dropdown, nothing else changes. Don't append a date to the model
> name; use the ID exactly as written.

---

## One design decision up front: how the Slack thread is created

You asked for the review to go to "the thread of the call on Slack." There are two
ways to get a thread, and they change how you build the Zap:

- **Option A — the Zap owns the thread (recommended).** The Zap posts a short
  parent message ("📞 New call recorded: …"), captures that message's timestamp,
  then posts Claude's review as a *threaded reply* under it. This is reliable —
  the Zap always knows exactly which message to thread under. The steps below use
  Option A.

- **Option B — reply under Fathom's existing Slack post.** If you already have
  Fathom's native Slack integration auto-posting recordings to a channel, you can
  instead find that message and reply in its thread. This is less reliable because
  the Zap has to *search* for the right message by call title/lead name. See
  [Appendix: Option B](#appendix-option-b--thread-under-fathoms-existing-post) at
  the end if you want this.

---

## Step 1 — Connect the apps to Zapier

1. **Anthropic** — in Zapier add an Anthropic step; paste your API key from
   console.anthropic.com → API Keys.
2. **Close** — Settings → Developer/API in Close to get your API key, then
   connect it when Zapier asks.
3. **Fathom** — in Fathom, **Settings → Integrations → Zapier**, click Connect,
   copy the key, and paste it when Zapier asks.
4. **Slack** — connect the Slack workspace; allow Zapier to post messages.
   Decide which channel the manager reviews in (e.g. `#sales-call-reviews`).

---

## Step 2 — Make sure the Fathom link reliably lands on Close

The Zap triggers off Close, so the Fathom link has to arrive there in a
**consistent, detectable** spot. Pick one and use it every time:

- **Best:** add a custom field on the Close lead/opportunity called
  **`Fathom Recording URL`** and have reps (or Fathom's Close integration) put
  the link there. A dedicated field is the cleanest thing to trigger on.
- **Also fine:** reps paste the Fathom link into a **Note** on the lead.

The guide below assumes the **custom field** approach. (If you use Notes instead,
swap the trigger event in Step 3 to "Note Created" and read the link from the
note body.)

---

## Step 3 — Build the Zap

In Zapier click **Create Zap**.

### 🔵 Step 1 — Trigger: Close "Lead Updated"

- **App:** Close
- **Event:** **Lead Updated** (fires when the lead changes, e.g. when the Fathom
  field gets filled in)
- **Test:** pick a lead that already has a Fathom URL in the custom field so you
  have real data to map.

> If you went with Notes instead of a custom field, use event **Note Created**.

### 🟡 Step 2 — Filter: only continue when there's a Fathom link

- **App:** Filter by Zapier
- **Condition:** `Fathom Recording URL` (the custom field from Step 1)
  **(Text) Contains** `fathom.video`
- This stops the Zap from running on every unrelated lead edit — it only proceeds
  when an actual Fathom link is present.

> **Avoid re-processing the same call.** "Lead Updated" can fire many times. Add a
> second condition or a second checkbox field (e.g. `Review Sent` = empty) and set
> that field to checked in the last step (Step 8) so a given call is only reviewed
> once.

### 🟠 Step 3 — Fathom: "Find Recording"

- **App:** Fathom
- **Event:** Find Recording
- **Recording URL:** map the `Fathom Recording URL` field from Step 1
- **What you get back:** the full **transcript**, the call **title**, the
  **date**, **attendees/participants**, and the recording link. You'll use the
  transcript in Step 5 and the title/lead name in Step 4.

### 🟣 Step 4 — Slack: post the parent "call recorded" message

This is the message the review will be threaded under.

- **App:** Slack
- **Event:** **Send Channel Message**
- **Channel:** `#sales-call-reviews` (or wherever the manager reviews)
- **Message text:**
  ```
  📞 New sales call recorded — review below in thread
  *Lead:* {{Close Lead Name}}
  *Closer:* {{Close Lead Owner / Rep}}
  *Call:* {{Fathom Title}} ({{Fathom Date}})
  *Recording:* {{Fathom Recording URL}}
  ```
- **Important:** after adding this step, in the step's options find and turn ON
  the field that exposes the message timestamp (Slack returns a **`ts`** /
  **Message Timestamp** value). You need it in Step 7 to reply in-thread. (In
  Zapier's Slack action this surfaces automatically in the step's output once you
  test it — look for `ts` or "Message Ts".)

### 🟤 Step 5 — Anthropic: "Send Message" (Claude writes the review)

- **App:** Anthropic
- **Event:** Send Message
- **Model:** `claude-opus-4-8`  *(or `claude-sonnet-4-6` for lower cost)*
- **Max tokens:** `2000`
- **System / Instructions** (if the step has a separate system field, put this
  there; otherwise paste it at the top of the message):
  ```
  You are a sales coach reviewing a recorded sales call for Freedom Team Trading,
  a forex and futures trading education brand. Your audience is the SALES MANAGER,
  not the rep. Be specific, direct, and useful — quote the call when it helps.
  Do not invent anything that is not supported by the transcript. If the
  transcript is missing or too short to assess, say so plainly instead of guessing.
  Never coach the rep to make guaranteed-profit or income claims.
  ```
- **Message (user):** paste the prompt below, then use Zapier's field picker to
  insert the dynamic values where marked:
  ```
  CALL TITLE: [insert Fathom Title from Step 3]
  DATE: [insert Fathom Date from Step 3]
  LEAD: [insert Close Lead Name from Step 1]
  CLOSER / REP: [insert Close Lead Owner from Step 1]

  TRANSCRIPT:
  [insert Transcript from Step 3 - Fathom]

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

### 🔵 Step 6 — (optional) Formatter: tidy the output

Usually not needed. If Claude ever wraps the reply in stray characters, add a
**Formatter by Zapier → Text → Replace** step to clean it. Skip otherwise.

### 🟢 Step 7 — Slack: post the review **in the thread**

- **App:** Slack
- **Event:** **Send Channel Message**
- **Channel:** same channel as Step 4
- **Message text:** map the **Claude response** from Step 5
- **Thread:** this is the key field — set **"Thread"** / **"Thread Timestamp
  (ts)"** to the **`ts`** value from **Step 4** (the parent message). That makes
  this post a reply *inside* the call's thread instead of a new top-level message.
- **Send as a bot / Send as Zapier:** either is fine; pick what your team prefers.
- **(Optional) Notify the manager:** start the message with `<@MANAGER_SLACK_ID>`
  or `<!subteam^SALES_MANAGERS_ID>` so the manager gets pinged on the thread.

### ⚪ Step 8 — Close: mark the call as reviewed

- **App:** Close
- **Event:** **Update Lead**
- **Lead:** the lead from Step 1
- Set your `Review Sent` checkbox (from Step 2's note) to **checked**, or write
  the Slack thread link into a field. This prevents the Zap from re-reviewing the
  same call on the next lead edit.

---

## Step 4 — Test end to end

1. Pick a real, **short** completed call and put its Fathom link in the Close
   custom field.
2. In Zapier, test each step top to bottom. Confirm:
   - Step 3 returns a real transcript (not empty).
   - Step 4 posts the parent message and exposes a `ts`.
   - Step 5 returns the five-section review.
   - Step 7's reply lands **inside the thread** of Step 4's message (not as a
     separate message).
3. Turn the Zap **on**.

---

## How the sales manager uses it

1. A closer finishes a call → the Fathom link gets added to the Close lead.
2. Within a few minutes, `#sales-call-reviews` shows a `📞 New sales call`
   message, with Claude's full coaching review threaded right under it.
3. The manager opens the thread, reads the review, and can reply in the same
   thread with feedback for the rep — keeping the call, the review, and the
   coaching conversation in one place.

---

## Quick-start checklist

- [ ] Connect Anthropic, Close, Fathom, and Slack to Zapier
- [ ] Add a `Fathom Recording URL` custom field on Close leads (+ a `Review Sent` checkbox)
- [ ] Decide the Slack review channel (e.g. `#sales-call-reviews`)
- [ ] Build the 8-step Zap — test each step before turning it on
- [ ] Confirm the review posts **in-thread** under the parent message
- [ ] Do one full end-to-end test with a short real call
- [ ] Turn the Zap on 🚀

---

## Appendix: Option B — thread under Fathom's existing post

Use this only if Fathom's native Slack integration already auto-posts each
recording to a channel and you want the review threaded under *that* message
instead of one the Zap creates.

Replace Step 4 and Step 7 above with:

1. **Slack: "Find Message"** — search the Fathom channel for the message matching
   this call. Search by the **call title** or **lead name** (map from Step 1/3).
   This returns the message's `ts`.
2. **Filter** — only continue if a message was found (the search can miss if
   Fathom hasn't posted yet; you may need a Delay step before this so Fathom posts
   first).
3. **Slack: "Send Channel Message"** — set **Thread (ts)** to the `ts` from the
   Find Message step, and map Claude's review as the text.

**Why it's less reliable:** the match depends on the title/name being unique and
on Fathom having already posted. If two calls share a lead name, or Fathom is
slow, the reply can land on the wrong message or fail to find one. Option A avoids
both problems by creating and threading under its own message. Prefer Option A
unless you specifically need everything under Fathom's post.
