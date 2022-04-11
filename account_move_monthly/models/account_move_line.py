# -*- coding: utf-8 -*-

from odoo import _, api, fields, models

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    sale_date = fields.Date(string="Sale Date", readonly=1)