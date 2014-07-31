# encoding: utf-8

# Copyright (c) 2014, Ondrej Balaz. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * Neither the name of the original author nor the names of contributors
#   may be used to endorse or promote products derived from this software
#   without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

""" PDF Printer Port
    ================
"""

import os
import logging
logger = logging.getLogger(__name__)

from reportlab.platypus import SimpleDocTemplate, Spacer
from reportlab.platypus.paragraph import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.graphics.barcode import createBarcodeDrawing

from vjezd.models import Ticket
from vjezd.models import Config
from vjezd.ports.base import BasePort


class PDFPrinterTestError(Exception):
    """ Exception raised when port test fails.
    """
    pass


class PDFPrinter(BasePort):
    """ PDF printer.

        Prints ticket of given size as a PDF to file in specified path.

        Configuration
        -------------
        Port accepts the following positional arguments:
        #. width - ticket width in milimeters
        #. /path/to/pdf - path to pdf file

        Full configuration line of PDF printer is:
        ``printer=pdf:width,/path/to/pdf``
    """

    def __init__(self, *args):
        """ Initialize PDF printer.
        """
        self.width = 72
        self.pdf_path = '/tmp/vjezd_ticket.pdf'

        if len(args) >= 1:
            self.width = int(args[0])
        if len(args) >= 2:
            self.pdf_path = args[1]

        logger.info('PDF printer using: {} size={}mm'.format(
            self.pdf_path, self.width))


    def test(self):
        """ Test whether is possible to write PDF file to spool.
        """
        if not os.access(os.path.dirname(self.pdf_path), os.W_OK) or
            not os.access(os.path(self.pdf_path, os.W_OK):
            raise PDFPrinterTestError('Cannot write PDF to {}'.format(
                self.pdf_path))


    def write(self, data):
        """ Write PDF file with bar code and information about validity.
        """
        if not isinstance(data, Ticket):
            raise TypeError('Not a Ticket object')

        self.generate_pdf(data)


    def generate_pdf(self, ticket):
        """ Generate PDF file.

            :param ticket Ticket:   ticket object
            :return:                path to output PDF
        """

        # Get configurable text
        title_text = _(Config.get('ticket_title', None))

        # Setup styles
        styles = getSampleStyleSheet()

        doc = SimpleDocTemplate(self.pdf_path,
            pagesize=letter,
            topMargin=5*mm,
            # NOTE We don't want to offend some printers by setting too small
            # pagesize.
            rightMargin=(letter[0] - self.width*mm - 2*mm),
            bottomMargin=5*mm,
            leftMargin=2*mm)

        # Build document contents
        story = []

        if title_text:
            story.append(Paragraph('{}'.format(title_text), styles['Title']))

        # Creation and expiration date
        story.append(Paragraph('{}: {}<br/>{}: {}'.format(
            _('Cas vydani'),
            ticket.created.strftime('%d.%m.%Y %H:%M'),
            _('Platnost do'),
            ticket.expires().strftime('%d.%m.%Y %H:%M')),
            styles['Normal']))

        story.append(Spacer(width=1, height=10*mm))

        # Barcode (Standard39)
        barcode = createBarcodeDrawing('Standard39',
            value=ticket.code,
            checksum=0,
            quiet=False,        # don't use quiet zones on left and right
            barWidth=0.25*mm,
            barHeight=30*mm,
            humanReadable = True)

        # Scale barcode down to fit the page
        s = float(self.width*mm - 8*mm)  / float(barcode.width)
        barcode.scale(s, s)
        story.append(barcode)

        # Save the PDF
        doc.build(story)


# Export port_class for port_factory()
port_class = PDFPrinter
