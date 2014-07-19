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
from vjezd.ports.base import BasePort


class PDFPrinterTestError(Exception):
    """ Exception raised when port test fails.
    """
    pass


class PDFPrinter(BasePort):
    """ PDF printer.

        Prints ticket of given size as a PDF to file in specified directory.

        Configuration
        -------------
        Port accepts the following positional arguments:
        #. width - ticket width in milimeters
        #. /path/to/pdf - path to pdf file

        Full configuration line of PDF printer is:
        ``printer=pdf:width,/path/to/pdf
    """

    def __init__(self, *args):
        """ Initialize PDF printer.
        """
        self.width = 72
        self.height = 35
        self.pdf_path = '/tmp/vjezd_ticket.pdf'

        if len(args) >= 1:
            self.width = int(args[0])
        if len(args) >= 2:
            self.pdf_path = args[1]

        logger.info('PDF printer using: {} width={}mm'.format(
            self.pdf_path, self.width))


    def test(self):
        """ Test whether is possible to write PDF file to spool.
        """
        if not os.access(self.pdf_path, os.W_OK):
            raise PDFPrinterTestError('Cannot write PDFs to {}'.format(
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

        # Setup styles
        styles = getSampleStyleSheet()

        doc = SimpleDocTemplate(self.pdf_path,
            pagesize=(self.width*mm, letter[1]),
            topMargin=0,
            rightMargin=0, #(letter[0] - self.width*mm),
            bottomMargin=0,
            leftMargin=0)

        # Build document contents
        story = []

        # Creation and expiration date
        story.append(Paragraph('Vydano: {}'.format(
            ticket.created.strftime('%d.%m.%Y %H:%M')),
            styles['Normal']))
        story.append(Paragraph('Platnost do: {}'.format(
            ticket.expires().strftime('%d.%m.%Y %H:%M')),
            styles['Normal']))

        story.append(Spacer(width=1, height=5*mm))

        # Barcode (Extended39)
        barcode = createBarcodeDrawing('Extended39',
            value=ticket.code,
            checksum=0,
            barHeight=self.height*mm,
            )

        story.append(barcode)

        doc.build(story)


# Export port_class for port_factory()
port_class = PDFPrinter
