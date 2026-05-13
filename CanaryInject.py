import zipfile
import os
import shutil
from pathlib import Path
from protonmail import ProtonMail
from dotenv import load_dotenv



def main():
    docx_file = "TempDocument.docx"
    webhook = "CHANGEME"
    output_path = f"canary_document.docx"
    extract_dir = "doc_temp_extract"
    load_dotenv(override=True)

    USERNAME = os.getenv('USERNAME')
    PASSWORD = os.getenv('PASSWORD')
    proton = ProtonMail()
    proton.login(USERNAME, PASSWORD)
    try:
        webhook = input("[+] Give the webhook here: ")
        with zipfile.ZipFile(docx_file, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        footer_path = os.path.join(extract_dir, 'word', 'footer1.xml')
    
        footer_content = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" xmlns:w15="http://schemas.microsoft.com/office/word/2012/wordml" xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" mc:Ignorable="w14 w15 wp14"><w:bookmarkStart w:id="0" w:name="_GoBack"/><w:bookmarkEnd w:id="0"/><w:p w:rsidR="009E0DC7" w:rsidRDefault="009E0DC7"><w:pPr><w:pStyle w:val="Footer"/></w:pPr><w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> INCLUDEPICTURE  "{webhook}" \\d  \\* MERGEFORMAT </w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:pict><v:shapetype id="_x0000_t75" coordsize="21600,21600" o:spt="75" o:preferrelative="t" path="m@4@5l@4@11@9@11@9@5xe" filled="f" stroked="f"><v:stroke joinstyle="miter"/><v:formulas><v:f eqn="if lineDrawn pixelLineWidth 0"/><v:f eqn="sum @0 1 0"/><v:f eqn="sum 0 0 @1"/><v:f eqn="prod @2 1 2"/><v:f eqn="prod @3 21600 pixelWidth"/><v:f eqn="prod @3 21600 pixelHeight"/><v:f eqn="sum @0 0 1"/><v:f eqn="prod @6 1 2"/><v:f eqn="prod @7 21600 pixelWidth"/><v:f eqn="sum @8 21600 0"/><v:f eqn="prod @7 21600 pixelHeight"/><v:f eqn="sum @10 21600 0"/></v:formulas><v:path o:extrusionok="f" gradientshapeok="t" o:connecttype="rect"/><o:lock v:ext="edit" aspectratio="t"/></v:shapetype><v:shape id="_x0000_i1025" type="#_x0000_t75" style="width:.75pt;height:.75pt"><v:imagedata r:id="rId1"/></v:shape></w:pict></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p><w:p w:rsidR="009E0DC7" w:rsidRDefault="009E0DC7"><w:pPr><w:pStyle w:val="Footer"/></w:pPr></w:p></w:ftr>"""
        
        with open(footer_path, 'w', encoding='utf-8') as f:
            f.write(footer_content)
        
        print(f"Successfully injected token into {footer_path}")

        rels_dir = os.path.join(extract_dir, 'word', '_rels')
        os.makedirs(rels_dir, exist_ok=True)

        patch = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="{webhook}" TargetMode="External"/></Relationships>"""

        rels_file = os.path.join(extract_dir, 'word', '_rels', 'footer1.xml.rels')
        with open(rels_file, 'w', encoding='utf-8') as f:
            f.write(patch)
        
        #rezip the document
        shutil.make_archive(output_path.replace('.docx', ''), 'zip', extract_dir)
        
        #rename zip to docx
        os.rename(output_path.replace('.docx', '') + '.zip', output_path)
        
        print(f"\nCanary token document created: {output_path}")
        print(f"Webhook URL: {webhook}")

        with open('canary_document.docx','rb') as f: doc = f.read()
        document_attach = proton.create_attachment(content=doc, name="canary_document.docx")

        body = f"""
        <html>
            <body>
                <h2>Hello Professor,</h2>
                <br/>
                Please check out my new resume, it is attached to the email.
            </body>
        </html>
        """
        print(f"\nSending email")
        new_message = proton.create_message(
        recipients=["collapsedmold41@gmail.com"],
        subject="My first message",
        body=body,  # html or just text
        attachments=[document_attach],
        )

        sent_message = proton.send_message(new_message)
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    finally:
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)


    
main()
