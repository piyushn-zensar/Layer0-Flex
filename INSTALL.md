# Install and run Layer 0 on a Windows laptop

This runs the Layer 0 proof of concept on your own laptop with the demonstration opportunity, which is the public Syracuse switchgear RFP. It is read by the real pipeline from its frozen model answers (about 810 line items grouped into about 350 requirements). You don't need an OCR engine, an API key or a network connection to a model.

## Before you start (once)

1. **Python 3.12.** Download it from https://www.python.org/downloads/. In the installer, tick "Add python.exe to PATH".
2. **Node.js 20.9 or later** (the LTS version). Download it from https://nodejs.org.
3. **The Layer 0 folder:** clone the repository, or unzip the package you were given.

## Set up (once, about 5 minutes)

Double-click **`setup.cmd`** in the Layer 0 folder. It will:
- install the Python packages;
- build the web application;
- load the demonstration data.

It ends with "Setup complete".

## Run

1. Double-click **`start.cmd`**. Two small "Layer 0" windows open. After a few seconds the browser opens on the Traceability view of the demonstration opportunity.
2. To stop Layer 0, close the two "Layer 0" windows.
3. To start the demonstration again from a clean state, close the two windows, double-click **`reset-demo.cmd`**, then double-click **`start.cmd`**.

The address is http://localhost:3000. Use the **Acting as** drop-down at the top right to switch between the bid manager and each business unit's product manager or design engineer.

## What works offline, and what doesn't

| Works on the laptop | Needs the project's model connection or OCR machine |
|---|---|
| The demonstration opportunity: requirements, traceability, bid decision, work packages, final response, compliance matrix | Reading a **new** RFP with the reader agent. The Syracuse RFP has frozen answers, so it can be re-read offline |
| Uploading the Syracuse RFP again and re-reading it (about 810 line items from the frozen answers) | OCR of scanned pages in a new RFP |
| Requirement review: edit, split, merge, add, history | Model-based product matching for new line items. Keyword matching is used instead and labelled as such |

## If something goes wrong

| Message | What to do |
|---|---|
| "Python 3.12 is required" or "Node.js … is required" | Install it (see above), open a new window, then run `setup.cmd` again |
| "Layer 0 did not start within a minute" | Another program uses port 3000 or 8000. Close it, or restart the laptop, then run `start.cmd` |
| "close the Layer 0 windows first" | Layer 0 is still running. Close its two windows, then retry |

## For the project team: make a package without Git

From the repository root, run:

```bash
git archive --format=zip -o ../Layer0-demo.zip HEAD
```

The zip holds the committed code and data, including the frozen layouts and model answers. It contains no secrets: `.env` is not committed.
