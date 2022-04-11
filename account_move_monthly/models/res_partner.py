# -*- coding: utf-8 -*-

from odoo import _, api, fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'

    res_partner_product_monthly_ids = fields.One2many('res.partner.product.monthly', 'partner_id')