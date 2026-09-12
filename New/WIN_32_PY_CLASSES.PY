import win32com.client as win32
from pathlib import Path


class ExcelWin32:

    def __init__(self, visible=False):
        self.excel = win32.Dispatch("Excel.Application")
        self.excel.Visible = visible
        self.excel.DisplayAlerts = False

        self.workbook = None
        self.worksheet = None

    # --------------------------------------------------
    # Workbook
    # --------------------------------------------------

    def open(self, file_path):
        self.workbook = self.excel.Workbooks.Open(
            str(Path(file_path).absolute())
        )
        return self.workbook

    def create(self):
        self.workbook = self.excel.Workbooks.Add()
        return self.workbook

    def save(self, file_path=None):
        if file_path:
            self.workbook.SaveAs(str(Path(file_path).absolute()))
        else:
            self.workbook.Save()

    def close(self, save=True):
        if self.workbook:
            self.workbook.Close(SaveChanges=save)

        self.workbook = None
        self.worksheet = None

    def quit(self):
        self.excel.Quit()

    # --------------------------------------------------
    # Worksheets
    # --------------------------------------------------

    def select_sheet(self, sheet_name):
        self.worksheet = self.workbook.Worksheets(sheet_name)
        return self.worksheet

    def add_sheet(self, sheet_name):
        sheet = self.workbook.Worksheets.Add()
        sheet.Name = sheet_name
        self.worksheet = sheet
        return sheet

    def get_sheet_names(self):
        return [
            self.workbook.Worksheets(i).Name
            for i in range(1, self.workbook.Worksheets.Count + 1)
        ]

    def delete_sheet(self, sheet_name):
        self.workbook.Worksheets(sheet_name).Delete()

    # --------------------------------------------------
    # READ
    # --------------------------------------------------

    def read_cell(self, row, column):
        return self.worksheet.Cells(row, column).Value

    def read_range(self, range_address):
        return self.worksheet.Range(range_address).Value

    def read_row(self, row, start_col=1, end_col=None):

        if end_col is None:
            end_col = self.get_last_column()

        values = self.worksheet.Range(
            self.worksheet.Cells(row, start_col),
            self.worksheet.Cells(row, end_col)
        ).Value

        return list(values[0])

    def read_column(self, column, start_row=1, end_row=None):

        if end_row is None:
            end_row = self.get_last_row()

        values = self.worksheet.Range(
            self.worksheet.Cells(start_row, column),
            self.worksheet.Cells(end_row, column)
        ).Value

        return [row[0] for row in values]

    def read_used_range(self):

        used = self.worksheet.UsedRange
        return used.Value

    # --------------------------------------------------
    # WRITE
    # --------------------------------------------------

    def write_cell(self, row, column, value):
        self.worksheet.Cells(row, column).Value = value

    def write_range(self, range_address, values):
        self.worksheet.Range(range_address).Value = values

    def write_row(self, row, values, start_col=1):

        end_col = start_col + len(values) - 1

        self.worksheet.Range(
            self.worksheet.Cells(row, start_col),
            self.worksheet.Cells(row, end_col)
        ).Value = [values]

    def write_column(self, column, values, start_row=1):

        end_row = start_row + len(values) - 1

        data = [[value] for value in values]

        self.worksheet.Range(
            self.worksheet.Cells(start_row, column),
            self.worksheet.Cells(end_row, column)
        ).Value = data

    # --------------------------------------------------
    # FIND
    # --------------------------------------------------

    def find(self, text):

        result = self.worksheet.Cells.Find(What=text)

        if result:
            return {
                "row": result.Row,
                "column": result.Column,
                "address": result.Address,
                "value": result.Value
            }

        return None

    # --------------------------------------------------
    # LAST ROW / COLUMN
    # --------------------------------------------------

    def get_last_row(self, column=1):

        return self.worksheet.Cells(
            self.worksheet.Rows.Count,
            column
        ).End(-4162).Row # xlUp

    def get_last_column(self, row=1):

        return self.worksheet.Cells(
            row,
            self.worksheet.Columns.Count
        ).End(-4159).Column # xlToLeft

    # --------------------------------------------------
    # FORMULA
    # --------------------------------------------------

    def write_formula(self, cell, formula):
        self.worksheet.Range(cell).Formula = formula

    def read_formula(self, cell):
        return self.worksheet.Range(cell).Formula

    # --------------------------------------------------
    # FORMAT
    # --------------------------------------------------

    def set_bold(self, range_address, value=True):
        self.worksheet.Range(range_address).Font.Bold = value

    def set_number_format(self, range_address, format_string):
        self.worksheet.Range(range_address).NumberFormat = format_string

    def autofit(self, range_address=None):

        if range_address:
            self.worksheet.Range(range_address).Columns.AutoFit()
        else:
            self.worksheet.UsedRange.Columns.AutoFit()

    # --------------------------------------------------
    # TABLE
    # --------------------------------------------------

    def create_table(self, range_address, table_name):

        table = self.worksheet.ListObjects.Add(
            1,
            self.worksheet.Range(range_address),
            None,
            1
        )

        table.Name = table_name

        return table

Get Outlook for Android
________________________________________
From: Rahul MAHAJAN <rahul.mahajan@alten-india.com>
Sent: Saturday, 12 September 2026 03:16:06
To: Rahul MAHAJAN <rahul.mahajan@alten-india.com>
Subject: Ai gen 
 
import os
import win32com.client
from pathlib import Path


class WordDocumentReader:
    """
    Read/extract content from Microsoft Word documents using pywin32.

    Extracts:
        - Paragraphs
        - Headings
        - Sections
        - Tables
        - Images
        - Headers
        - Footers
        - Hyperlinks
        - Bookmarks
        - Fields
        - Lists
        - Document properties
        - Text from shapes/text boxes
    """

    # Word constants
    WD_MAIN_TEXT_STORY = 1
    WD_HEADER_STORY = 9
    WD_FOOTER_STORY = 10

    def __init__(self, file_path):
        self.file_path = str(Path(file_path).resolve())

        if not os.path.exists(self.file_path):
            raise FileNotFoundError(
                f"Word document not found: {self.file_path}"
            )

        self.word = None
        self.document = None

    # ---------------------------------------------------------
    # OPEN / CLOSE
    # ---------------------------------------------------------

    def open(self):
        """Open Word document."""

        self.word = win32com.client.Dispatch("Word.Application")

        self.word.Visible = False

        self.document = self.word.Documents.Open(
            self.file_path,
            ReadOnly=True
        )

        return self

    def close(self):
        """Close Word and release COM objects."""

        try:
            if self.document:
                self.document.Close(False)
        except Exception:
            pass

        try:
            if self.word:
                self.word.Quit()
        except Exception:
            pass

        self.document = None
        self.word = None

    # ---------------------------------------------------------
    # DOCUMENT INFORMATION
    # ---------------------------------------------------------

    def get_document_info(self):
        """Return basic document information."""

        return {
            "name": self.document.Name,
            "full_path": self.document.FullName,
            "author": self.document.BuiltInDocumentProperties("Author").Value,
            "title": self.document.BuiltInDocumentProperties("Title").Value,
            "subject": self.document.BuiltInDocumentProperties("Subject").Value,
            "keywords": self.document.BuiltInDocumentProperties("Keywords").Value,
            "comments": self.document.BuiltInDocumentProperties("Comments").Value,
            "creation_date": self.document.BuiltInDocumentProperties(
                "Creation Date"
            ).Value,
            "last_saved": self.document.BuiltInDocumentProperties(
                "Last Save Time"
            ).Value,
            "page_count": self.document.ComputeStatistics(2), # pages
            "word_count": self.document.ComputeStatistics(0),
            "character_count": self.document.ComputeStatistics(3),
        }

    # ---------------------------------------------------------
    # PARAGRAPHS
    # ---------------------------------------------------------

    def get_paragraphs(self):
        """Extract all paragraphs."""

        paragraphs = []

        for index, paragraph in enumerate(
            self.document.Paragraphs,
            start=1
        ):

            text = paragraph.Range.Text

            # Remove Word paragraph mark
            text = text.rstrip("\r\a")

            if not text.strip():
                continue

            style = ""

            try:
                style = paragraph.Style.NameLocal
            except Exception:
                pass

            paragraphs.append({
                "index": index,
                "text": text,
                "style": style,
                "outline_level": paragraph.OutlineLevel,
            })

        return paragraphs

    # ---------------------------------------------------------
    # HEADINGS
    # ---------------------------------------------------------

    def get_headings(self):
        """Extract headings such as Heading 1, Heading 2, etc."""

        headings = []

        for index, paragraph in enumerate(
            self.document.Paragraphs,
            start=1
        ):

            try:
                outline_level = paragraph.OutlineLevel

                if 1 <= outline_level <= 9:

                    text = paragraph.Range.Text.rstrip("\r\a")

                    headings.append({
                        "paragraph_index": index,
                        "text": text,
                        "level": outline_level,
                    })

            except Exception:
                pass

        return headings

    # ---------------------------------------------------------
    # SECTIONS
    # ---------------------------------------------------------

    def get_sections(self):
        """Extract Word sections."""

        sections = []

        for index, section in enumerate(
            self.document.Sections,
            start=1
        ):

            sections.append({
                "section_number": index,

                "start_page": section.Range.Information(1),

                "header_text": self._get_header_text(section),

                "footer_text": self._get_footer_text(section),

                "page_width": section.PageSetup.PageWidth,

                "page_height": section.PageSetup.PageHeight,

                "left_margin": section.PageSetup.LeftMargin,

                "right_margin": section.PageSetup.RightMargin,

                "top_margin": section.PageSetup.TopMargin,

                "bottom_margin": section.PageSetup.BottomMargin,
            })

        return sections

    def _get_header_text(self, section):

        try:
            header = section.Headers(1)

            return header.Range.Text.rstrip("\r\a")

        except Exception:
            return ""

    def _get_footer_text(self, section):

        try:
            footer = section.Footers(1)

            return footer.Range.Text.rstrip("\r\a")

        except Exception:
            return ""

    # ---------------------------------------------------------
    # TABLES
    # ---------------------------------------------------------

    def get_tables(self):
        """Extract all tables."""

        tables = []

        for table_index, table in enumerate(
            self.document.Tables,
            start=1
        ):

            rows = []

            for row_index in range(1, table.Rows.Count + 1):

                row_data = []

                for column_index in range(
                    1,
                    table.Columns.Count + 1
                ):

                    try:
                        cell = table.Cell(
                            row_index,
                            column_index
                        )

                        text = cell.Range.Text

                        # Remove cell markers
                        text = text.rstrip("\r\a")

                    except Exception:
                        text = ""

                    row_data.append(text)

                rows.append(row_data)

            tables.append({
                "table_index": table_index,
                "rows": rows,
                "row_count": table.Rows.Count,
                "column_count": table.Columns.Count,
            })

        return tables

    # ---------------------------------------------------------
    # IMAGES
    # ---------------------------------------------------------

    def get_images(self, output_folder=None):
        """
        Extract inline images and floating shapes.

        Images are saved if output_folder is supplied.
        """

        images = []

        if output_folder:
            output_folder = Path(output_folder)
            output_folder.mkdir(
                parents=True,
                exist_ok=True
            )

        # Inline images
        for index, image in enumerate(
            self.document.InlineShapes,
            start=1
        ):

            image_info = {
                "index": index,
                "type": "inline",
                "width": image.Width,
                "height": image.Height,
            }

            if output_folder:

                output_file = (
                    output_folder /
                    f"inline_image_{index}.png"
                )

                try:
                    image.Select()
                    self.word.Selection.CopyAsPicture()

                    temp_chart = self.document.Shapes.AddPicture

                    # Word COM does not reliably provide direct
                    # image export for every image type.
                    image_info["exported"] = False

                except Exception:
                    image_info["exported"] = False

            images.append(image_info)

        # Floating images / shapes
        for index, shape in enumerate(
            self.document.Shapes,
            start=1
        ):

            shape_info = {
                "index": index,
                "type": "shape",
                "name": shape.Name,
                "width": shape.Width,
                "height": shape.Height,
                "left": shape.Left,
                "top": shape.Top,
            }

            try:
                shape_type = shape.Type
                shape_info["shape_type"] = shape_type
            except Exception:
                pass

            try:
                shape_info["text"] = shape.TextFrame.TextRange.Text
            except Exception:
                shape_info["text"] = ""

            images.append(shape_info)

        return images

    # ---------------------------------------------------------
    # HYPERLINKS
    # ---------------------------------------------------------

    def get_hyperlinks(self):
        """Extract hyperlinks."""

        hyperlinks = []

        for index, link in enumerate(
            self.document.Hyperlinks,
            start=1
        ):

            try:
                hyperlinks.append({
                    "index": index,
                    "text": link.Range.Text,
                    "address": link.Address,
                    "sub_address": link.SubAddress,
                })

            except Exception:
                pass

        return hyperlinks

    # ---------------------------------------------------------
    # BOOKMARKS
    # ---------------------------------------------------------

    def get_bookmarks(self):
        """Extract bookmarks."""

        bookmarks = []

        for index, bookmark in enumerate(
            self.document.Bookmarks,
            start=1
        ):

            try:

                bookmarks.append({
                    "index": index,
                    "name": bookmark.Name,
                    "text": bookmark.Range.Text,
                    "start": bookmark.Range.Start,
                    "end": bookmark.Range.End,
                })

            except Exception:
                pass

        return bookmarks

    # ---------------------------------------------------------
    # FIELDS
    # ---------------------------------------------------------

    def get_fields(self):
        """Extract Word fields."""

        fields = []

        for index, field in enumerate(
            self.document.Fields,
            start=1
        ):

            try:

                fields.append({
                    "index": index,
                    "code": field.Code.Text,
                    "result": field.Result.Text,
                    "type": field.Type,
                })

            except Exception:
                pass

        return fields

    # ---------------------------------------------------------
    # LISTS
    # ---------------------------------------------------------

    def get_lists(self):
        """Extract numbered/bulleted lists."""

        lists = []

        for index, paragraph in enumerate(
            self.document.Paragraphs,
            start=1
        ):

            try:

                if paragraph.Range.ListFormat.ListType != 0:

                    lists.append({
                        "paragraph_index": index,
                        "text": paragraph.Range.Text.rstrip(
                            "\r\a"
                        ),
                        "list_type": paragraph.Range.ListFormat.ListType,
                        "level": paragraph.Range.ListFormat.ListLevelNumber,
                    })

            except Exception:
                pass

        return lists

    # ---------------------------------------------------------
    # COMMENTS
    # ---------------------------------------------------------

    def get_comments(self):
        """Extract document comments."""

        comments = []

        try:

            for index, comment in enumerate(
                self.document.Comments,
                start=1
            ):

                comments.append({
                    "index": index,
                    "text": comment.Range.Text,
                    "author": comment.Author,
                    "initials": comment.Initial,
                })

        except Exception:
            pass

        return comments

    # ---------------------------------------------------------
    # TEXT BOXES / SHAPES
    # ---------------------------------------------------------

    def get_text_boxes(self):
        """Extract text from Word shapes/text boxes."""

        text_boxes = []

        for index, shape in enumerate(
            self.document.Shapes,
            start=1
        ):

            try:

                if shape.TextFrame.HasText:

                    text_boxes.append({
                        "index": index,
                        "name": shape.Name,
                        "text": shape.TextFrame.TextRange.Text,
                    })

            except Exception:
                pass

        return text_boxes

    # ---------------------------------------------------------
    # HEADER / FOOTER
    # ---------------------------------------------------------

    def get_headers_footers(self):

        result = []

        for section_index, section in enumerate(
            self.document.Sections,
            start=1
        ):

            section_data = {
                "section": section_index,
                "headers": [],
                "footers": [],
            }

            # Headers
            for header_index in range(
                1,
                section.Headers.Count + 1
            ):

                try:

                    header = section.Headers(header_index)

                    section_data["headers"].append({
                        "index": header_index,
                        "text": header.Range.Text.rstrip(
                            "\r\a"
                        ),
                    })

                except Exception:
                    pass

            # Footers
            for footer_index in range(
                1,
                section.Footers.Count + 1
            ):

                try:

                    footer = section.Footers(footer_index)

                    section_data["footers"].append({
                        "index": footer_index,
                        "text": footer.Range.Text.rstrip(
                            "\r\a"
                        ),
                    })

                except Exception:
                    pass

            result.append(section_data)

        return result

    # ---------------------------------------------------------
    # ALL TEXT
    # ---------------------------------------------------------

    def get_all_text(self):
        """Get complete document text."""

        return self.document.Content.Text

    # ---------------------------------------------------------
    # COMPLETE EXTRACTION
    # ---------------------------------------------------------

    def extract_all(self, image_folder=None):

        return {

            "document_info":
                self.get_document_info(),

            "all_text":
                self.get_all_text(),

            "paragraphs":
                self.get_paragraphs(),

            "headings":
                self.get_headings(),

            "sections":
                self.get_sections(),

            "tables":
                self.get_tables(),

            "images":
                self.get_images(image_folder),

            "hyperlinks":
                self.get_hyperlinks(),

            "bookmarks":
                self.get_bookmarks(),

            "fields":
                self.get_fields(),

            "lists":
                self.get_lists(),

            "comments":
                self.get_comments(),

            "text_boxes":
                self.get_text_boxes(),

            "headers_footers":
                self.get_headers_footers(),
        }

    # ---------------------------------------------------------
    # CONTEXT MANAGER
    # ---------------------------------------------------------

    def __enter__(self):

        self.open()

        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback
    ):

        self.close()

Usage

from pprint import pprint

file_path = r"C:\Documents\MyDocument.docx"

with WordDocumentReader(file_path) as reader:

    data = reader.extract_all(
        image_folder=r"C:\Documents\ExtractedImages"
    )

    print("DOCUMENT")
    pprint(data["document_info"])

    print("\nHEADINGS")
    pprint(data["headings"])

    print("\nPARAGRAPHS")
    pprint(data["paragraphs"])

    print("\nTABLES")
    pprint(data["tables"])

    print("\nHYPERLINKS")
    pprint(data["hyperlinks"])

    print("\nBOOKMARKS")
    pprint(data["bookmarks"])

    print("\nFIELDS")
    pprint(data["fields"])

    print("\nCOMMENTS")
    pprint(data["comments"])

    print("\nTEXT BOXES")
    pprint(data["text_boxes"])

What this class can extract

Word content| Supported
Normal text| ✅
Paragraphs| ✅
Heading 1–9| ✅
Sections| ✅
Tables| ✅
Table rows/cells| ✅
Headers| ✅
Footers| ✅
Images| ⚠️ metadata/basic handling
Text boxes| ✅
Shapes| ✅
Hyperlinks| ✅
Bookmarks| ✅
Fields| ✅
Lists/bullets| ✅
Comments| ✅
Document properties| ✅
Page count| ✅
Word count| ✅
Character count| ✅
Formatting| Extendable
Track Changes| Extendable
Footnotes| Extendable
Endnotes| Extendable
Equations| Extendable
Embedded/OLE objects| Extendable

Important: "pywin32" controls the actual Microsoft Word application, so this approach requires Windows + Microsoft Word installed. It is particularly useful when you need Word's actual document structure rather than just extracting plain text.

If your goal is your Django traceability-analysis tool, I would recommend taking this one step further: build a "WordReader" that produces a single normalized JSON structure such as "Document → Section → Paragraph/Table/Image → content + metadata". That will make it much easier to feed Word requirements/design/test documents into your traceability processing pipeline
