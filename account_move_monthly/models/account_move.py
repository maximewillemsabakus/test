# -*- coding: utf-8 -*-

from odoo import _, api, fields, models

class AccountMove(models.Model):
    _inherit = 'account.move'

    original_move_ids = fields.One2many('account.move', 'generated_move_id', readonly=True)
    generated_move_id = fields.Many2one('account.move', readonly=True)
    original_moves_count = fields.Integer(compute="_compute_original_moves_count")
    
    @api.depends('original_move_ids')
    def _compute_original_moves_count(self):
        for move in self:
            move.original_moves_count = len(move.original_move_ids)