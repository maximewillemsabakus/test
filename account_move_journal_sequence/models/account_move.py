# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = ['account.move']

    name = fields.Char(string='Number', required=True, readonly=True, copy=False, default='/', compute=False)


    def _get_sequence(self):
        ''' Return the sequence to be used during the post of the current move.
        :return: An ir.sequence record or False.
        '''
        self.ensure_one()

        journal = self.journal_id
        if self.move_type in ('entry', 'out_invoice', 'in_invoice', 'out_receipt', 'in_receipt') or not journal.refund_sequence:
            return journal.sequence_id
        if not journal.refund_sequence_id:
            return "/"
        return journal.refund_sequence_id

    def _post(self, soft=True):
        for move in self:
            if move.name == "/":
                # Get the journal's sequence.
                sequence = move._get_sequence()
                if not sequence:
                    raise UserError(_('Please define a sequence on your journal.'))

                # Consume a new number.
                move.write({'name': sequence.with_context(ir_sequence_date=move.date).next_by_id()})
        return super()._post(soft)

class AccountPayment(models.Model):
    _inherit = ['account.payment']
    
    @api.onchange('journal_id')
    @api.depends('journal_id')
    def _onchange_journal_id(self):
        for move in self:
            sequence = move.journal_id.sequence_id
            move.name = sequence.with_context(ir_sequence_date=move.date).next_by_id()
