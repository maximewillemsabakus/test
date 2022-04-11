# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class AccountJournal(models.Model):
    _inherit = ['account.journal']

    sequence_id = fields.Many2one('ir.sequence', string='Entry Sequence', help="This field contains the information related to the numbering of the journal entries of this journal.", required=True, copy=False)
    refund_sequence_id = fields.Many2one('ir.sequence', string='Credit Note Entry Sequence', help="This field contains the information related to the numbering of the credit note entries of this journal.", copy=False)
    refund_sequence = fields.Boolean(string='Dedicated Credit Note Sequence', help="Check this box if you don't want to share the same sequence for invoices and credit notes made from this journal", default=False)
