import fitz

class PdfAnnotator:
    def __init__(self, file_path):
        """Init Pdf Annotator

        Args:
            filepath (str): path of pdf we want to annotate
        """
        self.file = fitz.open(file_path)
        self.file_path = None

    @staticmethod
    def _combine_quads(quads):
        """Combine quadrilaterals if text we want to highlight is on different lines. Creates one combined quadrilateral given a list of quads

        Args:
            quads (list): list of fitz.Quad

        Returns:
            fitz.Quad: combined quadrilateral where we will be highlighting
        """
        ul = quads[0].ul
        ur = quads[0].ur
        ll = quads[-1].ll
        lr = quads[-1].lr
        return fitz.Quad(ul=ul, ur=ur,ll=ll, lr=lr)
    
    @staticmethod
    def _highlight_quad(page, quad):
        """Helper function to highlight text given a quadrilateral

        Args:
            page (fitz.Page): page where we want to highlight
            quad (fitz.Quad): coordinates on the page where we want to highlight
        """
        highlight_annot = page.add_highlight_annot(quad)
        highlight_annot.set_colors({"stroke": fitz.utils.getColor("yellow")})
        highlight_annot.set_opacity(0.7)

    def get_highlighted_quad(self, page_num, text, question, response, combine_quads=False):
        """Highlights text on a given page of our document

        Args:
            page_num (int): page number we are searching
            text (str): search string we want to highlight
            combine_quads (bool, optional): flag to combine the quadrilaterals found when we search for text. 
            Can be set to True if and only if the x coordinates of every row are equal. 
            Meaning that the text foun all start at the same x coordinate for every row. Defaults to False.

        Returns:
            fitz.Quad: Returns the location where we highlight, in case we want to add text in another step
        """
        p = self.file[page_num]
        point = fitz.Point(25,25)
        r1 = p.search_for(text, quads=True)
        annotation = "Q: " + question + "\n" + "A: " + response
        if response.count(":") > 2:
            annotation = response.split(":",1)[0] + ":"
            # annotation = question # + "\n" + response
        if combine_quads:
            r2 = PdfAnnotator._combine_quads(r1)
            PdfAnnotator._highlight_quad(p, r2)
            if r2:
                p.add_text_annot(point, annotation)

            return r2
        else:
            for quad in r1:
                PdfAnnotator._highlight_quad(p, quad)
                if r1:
                    p.add_text_annot(point, annotation)
            return r1


    @staticmethod
    def _calculate_textbox_loc(r):
        """Given a quadrilateral that has been created based on searched text, creates a new rectangle of equal width shifted to the left for annotation

        Args:
            r (fitz.Quad): location of highlighted text

        Returns:
            fitz.Rect: location of textbook to insert annotation
        """
        #ul = fitz.Point(r.ul.x, r.ul.y)
        #ul.x = ul.x - r.width - 20
        ul = fitz.Point(5, r.ul.y)

        ll = fitz.Point(ul.x, r.ll.y) # Lower Left X-coor = Upper Left X-Coor, Y-Coor = Original Y coor (same line)

        ur = fitz.Point(85, ul.y)
        #lr = fitz.Point(ur.x, ll.y)

        rect = fitz.Rect(x0=ul.x, x1=ur.x, y0=ul.y, y1=ll.y)
        if rect.height < 10:
            rect.y1 += 10
        return rect
    
    def write_message(self, r, page_num, message, font_size=7):
        """Writes a message on a certain page given a set of coordinates where text has been highlighted

        Args:
            r (fitz.Quad): location of highlighted text on the page
            page_num (int): page number we are editing
            message (str): message we want to insert into our annotation
            font_size (int, optional): size of font for message. Defaults to 7.
        """
        page = self.file[page_num]
        if type(r) == list:
            r = r[0]
        txtbox = PdfAnnotator._calculate_textbox_loc(r)
        page.add_freetext_annot(txtbox, message, fontsize=font_size) #, fill_color=fitz.utils.getColor("yellow"))

        
        
    def save_new_pdf(self, filepath):
        """Saves edited document into a new file location

        Args:
            filepath (str): Path for new file
        """
        self.file_path = filepath
        return self.file.save(filepath)

    def highlight(self, parser, question, response):
        pages = parser.get_pages()
        minimum = pages[0]
        maximum = pages[-1]
        pages.insert(0, minimum-1)
        pages.append(maximum+1)
        for page in pages:
            if page < self.file.page_count:
                for value in parser.get_values():
                    words = value.split(' ')
                    if len(words) > 5:
                        n = len(words)
                        for i in range(n-3):
                            start = i
                            end = min(i+4, n)
                            window = words[start:end]
                            search_word = " ".join(window)
                            self.get_highlighted_quad(page, search_word, question, response, combine_quads=False)
                    else:
                        self.get_highlighted_quad(page, value, question, response, combine_quads=False)

