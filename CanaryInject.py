import argparse
import mimetypes
import os
import shutil
import smtplib
import ssl
import zipfile
from email.message import EmailMessage
from pathlib import Path


DEFAULT_INPUT_DOCX = "TempDocument.docx"
DEFAULT_OUTPUT_DOCX = "canary_document.docx"
DEFAULT_EXTRACT_DIR = "doc_temp_extract"
DEFAULT_WEBHOOK = "CHANGEME"


def inject_canary(docx_file, webhook, output_path, extract_dir=DEFAULT_EXTRACT_DIR):
    docx_path = Path(docx_file)
    output_docx = Path(output_path)
    temp_dir = Path(extract_dir)

    if not docx_path.exists():
        raise FileNotFoundError(f"Input document not found: {docx_path}")

    if webhook == DEFAULT_WEBHOOK:
        print("Warning: webhook URL is still set to CHANGEME.")

    if temp_dir.exists():
        shutil.rmtree(temp_dir)

    try:
        with zipfile.ZipFile(docx_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        footer_path = temp_dir / "word" / "footer1.xml"
        footer_path.parent.mkdir(parents=True, exist_ok=True)

        footer_content = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" xmlns:w15="http://schemas.microsoft.com/office/word/2012/wordml" xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" mc:Ignorable="w14 w15 wp14"><w:bookmarkStart w:id="0" w:name="_GoBack"/><w:bookmarkEnd w:id="0"/><w:p w:rsidR="009E0DC7" w:rsidRDefault="009E0DC7"><w:pPr><w:pStyle w:val="Footer"/></w:pPr><w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> INCLUDEPICTURE  "{webhook}" \\d  \\* MERGEFORMAT </w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:pict><v:shapetype id="_x0000_t75" coordsize="21600,21600" o:spt="75" o:preferrelative="t" path="m@4@5l@4@11@9@11@9@5xe" filled="f" stroked="f"><v:stroke joinstyle="miter"/><v:formulas><v:f eqn="if lineDrawn pixelLineWidth 0"/><v:f eqn="sum @0 1 0"/><v:f eqn="sum 0 0 @1"/><v:f eqn="prod @2 1 2"/><v:f eqn="prod @3 21600 pixelWidth"/><v:f eqn="prod @3 21600 pixelHeight"/><v:f eqn="sum @0 0 1"/><v:f eqn="prod @6 1 2"/><v:f eqn="prod @7 21600 pixelWidth"/><v:f eqn="sum @8 21600 0"/><v:f eqn="prod @7 21600 pixelHeight"/><v:f eqn="sum @10 21600 0"/></v:formulas><v:path o:extrusionok="f" gradientshapeok="t" o:connecttype="rect"/><o:lock v:ext="edit" aspectratio="t"/></v:shapetype><v:shape id="_x0000_i1025" type="#_x0000_t75" style="width:.75pt;height:.75pt"><v:imagedata r:id="rId1"/></v:shape></w:pict></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p><w:p w:rsidR="009E0DC7" w:rsidRDefault="009E0DC7"><w:pPr><w:pStyle w:val="Footer"/></w:pPr></w:p></w:ftr>"""

        footer_path.write_text(footer_content, encoding="utf-8")
        print(f"Successfully injected token into {footer_path}")

        rels_dir = temp_dir / "word" / "_rels"
        rels_dir.mkdir(parents=True, exist_ok=True)

        patch = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="{webhook}" TargetMode="External"/></Relationships>"""

        rels_file = rels_dir / "footer1.xml.rels"
        rels_file.write_text(patch, encoding="utf-8")

        zip_base = output_docx.with_suffix("")
        zip_file = zip_base.with_suffix(".zip")
        if output_docx.exists():
            output_docx.unlink()
        if zip_file.exists():
            zip_file.unlink()

        shutil.make_archive(str(zip_base), "zip", temp_dir)
        zip_file.rename(output_docx)

        print(f"\nCanary token document created: {output_docx}")
        print(f"Webhook URL: {webhook}")
        return output_docx
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


def send_email_with_attachment(
    smtp_host,
    smtp_port,
    smtp_user,
    password_env,
    sender,
    recipient,
    subject,
    body,
    attachment_path,
    use_starttls=False,
):
    password = os.environ.get(password_env)
    if not password:
        raise RuntimeError(
            f"Set the {password_env} environment variable before sending email."
        )

    attachment = Path(attachment_path)
    if not attachment.exists():
        raise FileNotFoundError(f"Attachment not found: {attachment}")

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)

    content_type, _ = mimetypes.guess_type(attachment)
    if content_type is None:
        maintype, subtype = "application", "octet-stream"
    else:
        maintype, subtype = content_type.split("/", 1)

    with attachment.open("rb") as file:
        msg.add_attachment(
            file.read(),
            maintype=maintype,
            subtype=subtype,
            filename=attachment.name,
        )

    context = ssl.create_default_context()
    if use_starttls:
        with smtplib.SMTP(smtp_host, smtp_port) as smtp:
            smtp.ehlo()
            smtp.starttls(context=context)
            smtp.ehlo()
            smtp.login(smtp_user, password)
            smtp.send_message(msg)
    else:
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as smtp:
            smtp.login(smtp_user, password)
            smtp.send_message(msg)

    print(f"Email sent to {recipient} with attachment: {attachment}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Inject a canary URL into a Word document and optionally email it for an authorized lab test."
    )
    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT_DOCX,
        help=f"Source .docx file. Default: {DEFAULT_INPUT_DOCX}",
    )
    parser.add_argument(
        "--webhook",
        default=DEFAULT_WEBHOOK,
        help="Webhook URL to embed in the document.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_DOCX,
        help=f"Generated .docx file. Default: {DEFAULT_OUTPUT_DOCX}",
    )
    parser.add_argument(
        "--send-email",
        action="store_true",
        help="Send the generated document as a single email attachment.",
    )
    parser.add_argument(
        "--smtp-host",
        default="smtp.gmail.com",
        help="SMTP server hostname. Default: smtp.gmail.com",
    )
    parser.add_argument(
        "--smtp-port",
        type=int,
        default=465,
        help="SMTP server port. Default: 465",
    )
    parser.add_argument(
        "--smtp-starttls",
        action="store_true",
        help="Use STARTTLS instead of SMTP over SSL.",
    )
    parser.add_argument(
        "--smtp-user",
        help="SMTP username/login. Often this is the sender email address.",
    )
    parser.add_argument(
        "--smtp-password-env",
        default="EMAIL_PASSWORD",
        help="Environment variable containing the SMTP password or app password. Default: EMAIL_PASSWORD",
    )
    parser.add_argument(
        "--sender",
        help="Sender address. Defaults to --smtp-user when omitted.",
    )
    parser.add_argument(
        "--recipient",
        help="Single authorized recipient email address.",
    )
    parser.add_argument(
        "--subject",
        default="Authorized school lab test document",
        help="Email subject line.",
    )
    parser.add_argument(
        "--body",
        default="Please see the attached document for the approved school lab test.",
        help="Plain-text email body.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        output_docx = inject_canary(args.input, args.webhook, args.output)

        if args.send_email:
            if not args.smtp_user:
                raise ValueError("--smtp-user is required when --send-email is used.")
            if not args.recipient:
                raise ValueError("--recipient is required when --send-email is used.")

            sender = args.sender or args.smtp_user
            send_email_with_attachment(
                smtp_host=args.smtp_host,
                smtp_port=args.smtp_port,
                smtp_user=args.smtp_user,
                password_env=args.smtp_password_env,
                sender=sender,
                recipient=args.recipient,
                subject=args.subject,
                body=args.body,
                attachment_path=output_docx,
                use_starttls=args.smtp_starttls,
            )

        return True
    except Exception as error:
        print(f"Error: {error}")
        return False


if __name__ == "__main__":
    main()
