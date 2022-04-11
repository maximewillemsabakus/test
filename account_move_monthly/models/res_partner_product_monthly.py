# -*- coding: utf-8 -*-

from odoo import _, api, fields, models

class ResPartnerProductMonthly(models.Model):
    _name = 'res.partner.product.monthly'
    _description = "Settings for monthly invoicing"

    product_id = fields.Many2one('product.product', string="Product")
    monthly_max_quantity = fields.Integer(string="Monthly Max Quantity", help="This product will be invoiced max the specified quantity monthly.")
    partner_id = fields.Many2one('res.partner')