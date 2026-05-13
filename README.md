# Document-based Phishing Canary (GroupProject-442)

## Overview

This repository contains a demonstration tool that injects an external reference into a Microsoft Word document (.docx) so that opening the document triggers an external request (a "canary" webhook). The demonstration shows how document-based phishing or reconnaissance techniques can silently signal when a file is opened. The purpose of this project is academic and defensive: to help researchers and security teams understand the risks, detection challenges, and mitigation strategies related to document-based callbacks.

## Motivation

Phishing exploits human behavior and trusted communication channels. Traditional metrics like training completion or simple click rates do not fully capture human risk. Document-based techniques (external references, images, macros, etc.) can be used to track interaction silently and highlight weaknesses in reporting and verification processes. This project demonstrates one such technique to support human risk analysis and awareness training in controlled, ethical settings.

## What this project does

- Unzips a `.docx` file (a Word document is a ZIP archive of XML parts).
- Replaces the footer XML (`word/footer1.xml`) to include an `INCLUDEPICTURE` field that references an external URL.
- Writes a relationships file (`word/_rels/footer1.xml.rels`) pointing to the external webhook URL as an external image target.
- Repackages the files into a new `.docx` document that will attempt the external request when opened in Word.

The provided script is `CanaryInject.py` and implements the steps above.

## Important safety & ethics notice

This tool is dual-use. It can be used for legitimate security research, red-team exercises, and awareness testing, but it can also be misused. Do not use this repository to target systems, organizations, or individuals without explicit, written authorization. Always follow applicable laws, institutional policies, and ethical guidelines. If you intend to use these techniques for testing, obtain written consent from the owner of the systems and accounts involved.

This project exists to inform defenders and researchers about modern phishing techniques and to help design better human-risk assessments.

## How it works (technical summary)

1. A `.docx` file is unpacked into a temporary folder.
2. `word/footer1.xml` is overwritten (or created) with an XML footer containing a Word field using `INCLUDEPICTURE "<webhook_url>" \d` so Word will load the external resource.
3. `word/_rels/footer1.xml.rels` is written to reference the external target via a relationship entry with `TargetMode="External"` and `Type` set to an image relationship.
4. The folder is re-zipped and renamed to produce the final `.docx` file.

Because the external reference is loaded by Word when the document is opened or when the field is updated, the webhook receives a request that can be used as a signal the document was opened.

## Files

- `CanaryInject.py` — Python script that performs the injection and produces `canary_document.docx` by default.

## Usage

Prerequisites:

- Python 3.7+ (no external packages required; uses the standard library)
- A Word `.docx` file to use as the base (the script defaults to `TempDocument.docx`)
- A webhook listener to observe the callback (for testing use https://webhook.site/ or your own endpoint)

Basic steps:

1. Place the source document you want to test as `TempDocument.docx` in the repository directory (or edit the script to point to a different filename).
2. Provide your webhook URL with the `--webhook` option.
3. Run the script:

```bash
python CanaryInject.py --webhook "https://example-webhook-url"
```

4. The script will create `canary_document.docx` in the same directory. When that document is opened in Microsoft Word, the external reference will trigger a request to the webhook URL (visible in your webhook listener).

Optional file arguments:

```bash
python CanaryInject.py --input TempDocument.docx --output canary_document.docx --webhook "https://example-webhook-url"
```

### Optional authorized email delivery

The script can send the generated document as a single email attachment for a controlled lab test. This is opt-in and only runs when `--send-email` is included.

Do not hard-code your email password in the script. Store an SMTP password or app password in an environment variable first.

PowerShell example:

```powershell
$env:EMAIL_PASSWORD = "your-app-password"
python CanaryInject.py --webhook "https://example-webhook-url" --send-email --smtp-user "your_email@gmail.com" --recipient "authorized_recipient@example.com"
```

By default, email delivery uses Gmail's SMTP server on port 465 with SSL. For a different SMTP server:

```bash
python CanaryInject.py --webhook "https://example-webhook-url" --send-email --smtp-host "smtp.example.com" --smtp-port 587 --smtp-starttls --smtp-user "sender@example.com" --recipient "authorized_recipient@example.com"
```

Useful email options:

- `--sender` sets the visible sender address. If omitted, it defaults to `--smtp-user`.
- `--subject` sets the email subject.
- `--body` sets the plain-text email body.
- `--smtp-password-env` changes which environment variable contains the SMTP password. The default is `EMAIL_PASSWORD`.

Notes:

- Email delivery should only be used with explicit authorization and a single approved recipient for the lab.
- Some versions of Microsoft Word may not automatically load external images or may prompt the user, depending on security settings. Behavior can differ between Office versions and platform configurations.

## Example / Demo

1. Create a test `.docx` (e.g., an empty Word file) and save it as `TempDocument.docx` in this folder.
2. Use https://webhook.site/ to get a unique testing URL and paste it into the `webhook` variable in `CanaryInject.py`.
3. Run the script and then open the produced `canary_document.docx` on a test machine or VM.
4. Observe the incoming request on webhook.site — this indicates Word attempted to load the external resource.

## Limitations & detection

- Not all Word configurations will silently load external resources. Many environments block or prompt for external content.
- Modern endpoint detection solutions and network monitoring can detect requests to unusual external URLs.
- This technique is only one of many document-based tracking methods (macros, OLE objects, remote templates, etc.). Each has different trade-offs.

## Defense considerations

- Disable automatic external content loading in Office deployment policies.
- Disable or restrict macros and untrusted add-ins.
- Use network monitoring and egress filtering to block or log requests to unknown external endpoints.
- Teach users to verify unexpected attachments and to report suspicious messages quickly.

## Improvements you might make

- Add templating to insert visible, context-specific content into the document body.
- Add safer file handling, validation of webhook URLs, and a dry-run mode.
- Integrate with a controlled red-team test framework and reporting pipeline.

## Legal / Responsible Use

Use only in environments where you have explicit authorization. Misuse of these techniques may be unlawful and unethical. If in doubt, consult legal counsel or your organization's security governance team before proceeding.

## Credits

Author: Tarron Montegomery | Darryl Lomax Jr. | Babajide Teru (GroupProject-442) 

Professor: Dr. Trivedi
