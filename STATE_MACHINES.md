# State machines

`index.html` has three explicit state machines. Each one has a single state
value, a transition table, and a `render()` that writes the state to a data
attribute. CSS and ARIA read from that attribute. An event that is not listed
for the current state is ignored (this is what prevents double submits).

All three are built with `createMachine()` in the page script and exposed on
`window.lsb` for debugging and for agents:

```js
lsb.gate.state            // "locked" | "submitting" | "unlocked"
lsb.inquiry.state         // "idle" | "invalid" | "sending" | "sent" | "error"
lsb.lightbox.state        // "closed" | "open"
lsb.lightbox.context      // { index, opener }
lsb.lightbox.send('NEXT') // returns false if the event is illegal right now
```

To change behaviour: edit the `states` table (what can happen), `enter` (side
effects such as fetch and focus) or `render` (DOM). Do not set styles, classes
or `disabled` anywhere else.

## 1. Email gate

Where to read it: `<html data-gate="...">`

| State | Event | Next | Notes |
|---|---|---|---|
| `locked` | `SUBMIT(email)` invalid | `locked` | error text in `#gate-error` (role=alert), input `aria-invalid`, focus returns to input |
| `locked` | `SUBMIT(email)` valid | `submitting` | saves `localStorage.lsb_gate_email`, POSTs the visitor log |
| `locked` | `EDIT` | `locked` | clears the error |
| `submitting` | `DONE` | `unlocked` | fired when the log POST resolves, fails, or 4s pass, whichever is first |
| `unlocked` | (none) | | terminal for the page load |

- Initial state is `unlocked` if `localStorage.lsb_gate_email` exists. A tiny
  script in `<head>` sets `data-gate="unlocked"` before first paint so returning
  visitors never see the gate flash.
- The visitor log is best effort and fails open: a blocked or slow endpoint
  never keeps a visitor out. If localStorage is unavailable the gate still
  opens, it is just not remembered.
- While not `unlocked`: `#page` is `inert` and body scroll is locked.
- On entering `unlocked`: the inquiry email field is prefilled if empty.
- This is a soft gate (lead capture), not access control. The content is in
  the HTML.

## 2. Inquiry form

Where to read it: `#inquiry[data-state="..."]`

| State | Event | Next | Notes |
|---|---|---|---|
| `idle` / `invalid` / `error` | `SUBMIT(fields)` invalid | `invalid` | message in `#inq-status`, bad field gets `aria-invalid` and focus |
| `idle` / `invalid` / `error` | `SUBMIT(fields)` valid | `sending` | button disabled + `aria-busy`, fields read-only |
| `invalid` / `error` | `EDIT` | `idle` | clears the message |
| `sending` | `SENT` | `sent` | form hidden, thank-you shown and focused |
| `sending` | `FAILED` | `error` | network failure or 20s timeout. Form contents kept, button reads "Try again" |
| `sent` | (none) | | terminal for the page load |

- Required: name, valid email, dates. Validation is done by the machine
  (`novalidate` on the form) so messages are consistent across browsers.
- Known limit: the POST uses `mode: 'no-cors'`, so the response is opaque.
  `sent` means "the request left the browser", not "Apps Script returned 200".
  Only network failures and timeouts reach `error`. Fixing that needs CORS
  headers on the Apps Script side.
- `#inq-website` is a honeypot. If it is filled, the machine goes to `sent`
  without posting.

## 3. Lightbox

Where to read it: `#lightbox[data-state="..."][data-index="n"]`, mirrored on
`<html data-lightbox="...">`

| State | Event | Next | Notes |
|---|---|---|---|
| `closed` | `OPEN({index, opener})` | `open` | focus moves to the close button |
| `open` | `NEXT` / `PREV` | `open` | index wraps around |
| `open` | `CLOSE` | `closed` | focus returns to the photo that opened it |

- Inputs mapped to events: photo click, arrow buttons, Left/Right keys,
  Escape, backdrop click, horizontal swipe (50px or more).
- While `open`: `#page` is `inert`, Tab cycles inside the lightbox, body scroll
  is locked, neighbouring photos are preloaded.
- `#lb-wrap[aria-busy]` is true while the full-size photo loads.
- Photos come from the DOM: every `#gallery [data-idx]` button carries
  `data-full` (large file) and `data-caption`. To add a photo, add a button.

## Derived state (not machines)

- Scroll lock: pure CSS from `html[data-gate]` and `html[data-lightbox]`.
- `#page.inert`: `renderShell()`, true when the gate is not unlocked or the
  lightbox is open.

## Contract with the Apps Script (do not change without updating the script)

Both POSTs go to `GATE_ENDPOINT`, form-encoded, with exactly these fields:
`name`, `email`, `company`, `inquiry_type`, `message`, `page`.

## Photos

Run `python3 tools/optimize-photos.py` after adding files to `photos/`. It
caps size at 2000px, converts to sRGB, strips metadata (including GPS), and
writes `photos/thumbs/` for the grid plus `photos/og.jpg` for link previews.
