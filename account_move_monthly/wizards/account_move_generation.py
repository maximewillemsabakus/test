# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)

from datetime import date, timedelta

class AccountMoveGeneration(models.TransientModel):
    _name = 'account.move.generation'
    _description = 'Account Move Generation'
    
    from_journal_id = fields.Many2one('account.journal', required=True)
    to_journal_id = fields.Many2one('account.journal', required=True)
    
    from_date = fields.Date(required=True, default=lambda r: r.get_from_date())
    to_date = fields.Date(required=True, default=lambda r: r.get_to_date())
    
    def get_from_date(self):
        last_day_of_prev_month = date.today().replace(day=1) - timedelta(days=1)
        return date.today().replace(day=1) - timedelta(days=last_day_of_prev_month.day)
    
    def get_to_date(self):
        return date.today().replace(day=1) - timedelta(days=1)
    
    def action_generate_invoices(self):
        AccountMove = self.env["account.move"]
        domain = [('journal_id', '=', self.from_journal_id.id), ('state', '=', 'posted')]
        if self.from_date:
            domain.append(('invoice_date', '>=', fields.Date.to_string(self.from_date)))
        if self.to_date:
            domain.append(('invoice_date', '<=', fields.Date.to_string(self.to_date)))
            
        partner_ids = AccountMove.search(domain).mapped('partner_id')
                
        generated_invoice_ids = []
        
        # We first generate all the invoices for all the partners
        for partner_id in partner_ids:
            partner_domain = domain.copy()
            partner_domain.append(("partner_id", '=', partner_id.id))
            account_move_ids = AccountMove.search(partner_domain)
            if not account_move_ids:
                continue
            account_move_ids = self.remove_already_globalized_moves(account_move_ids)
            if not account_move_ids:
                continue
            new_invoice_id = self.generate_invoice(account_move_ids, partner_id)
            generated_invoice_ids.append(new_invoice_id.id)

        action_id = self.env.ref('account.action_move_out_invoice_type')
        dict = action_id.read()[0]
        dict['domain'] = [('id', 'in', generated_invoice_ids)]

        return dict
        
    def remove_already_globalized_moves(self, move_ids):
        return move_ids.filtered(lambda r: not r.generated_move_id)
    
    def generate_invoice(self, move_ids, partner_id):
        AccountMove = self.env["account.move"]
        AccountMoveLine = self.env["account.move.line"]
        
        if len(move_ids) == 1:
            new_move_id = move_ids.copy()
            new_move_id.write({
                'partner_id': partner_id.id,
                'journal_id': self.to_journal_id.id,
                'original_move_ids': [(6, 0, move_ids.ids)],
                'invoice_date': fields.Date.to_string(self.to_date),
            })
            sale_date = move_ids.invoice_date
            if move_ids.invoice_origin:
                sale_order_id = self.env['sale.order'].search([('name', '=', move_ids.invoice_origin)])
                if sale_order_id:
                    sale_date = fields.Date.to_date(sale_order_id.date_order)
            for move_line_id in new_move_id.invoice_line_ids:
                move_line_id.write({
                    'sale_date': sale_date,
                })
            move_ids.button_draft()
            return new_move_id
        
        fiscal_position_id = partner_id.property_account_position_id
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': partner_id.id,
            'journal_id': self.to_journal_id.id,
            'currency_id': move_ids[0].currency_id.id,
            'invoice_line_ids': [],
            'original_move_ids': [(6, 0, move_ids.ids)],
            'invoice_date': fields.Date.to_string(self.to_date),
            'invoice_origin': '\n, '.join(move_ids.filtered(lambda m: m.invoice_origin).mapped('invoice_origin')) if move_ids else '',
            'fiscal_position_id': fiscal_position_id.id,
        }
            
        out_refund_nbr = 0
        for move_id in move_ids:
            if move_id.move_type == "out_refund":
                out_refund_nbr += 1
        
        out_refund = False
        if out_refund_nbr == len(move_ids):
            invoice_vals['move_type'] = 'out_refund'
            out_refund = True
        
        # Here we get all the maximum invoiceable qty for products of our partner
        invoiceable_product_qty_max = {} # Max qty for each product will decrease based on the invoiced qty
        product_monthly_qty_ids = self.env['res.partner.product.monthly'].search([('partner_id', '=', partner_id.id)])
        for product_monthly_qty_id in product_monthly_qty_ids:
            invoiceable_product_qty_max[product_monthly_qty_id.product_id.id] = product_monthly_qty_id.monthly_max_quantity

        for move_id in move_ids:
            for move_line_id in move_id.invoice_line_ids:
                
                # There, we check the quantity to invoice based on the max allowed qty for the partner
                quantity = move_line_id.quantity
                if move_line_id.product_id.id in invoiceable_product_qty_max:
                    max_qty_to_invoice = invoiceable_product_qty_max[move_line_id.product_id.id]
                    if max_qty_to_invoice == 0:
                        continue
                    elif quantity > max_qty_to_invoice:
                        quantity = max_qty_to_invoice
                
                sale_date = move_line_id.move_id.invoice_date
                if move_line_id.move_id.invoice_origin:
                    sale_order_id = self.env['sale.order'].search([('name', '=', move_line_id.move_id.invoice_origin)])
                    if sale_order_id:
                        sale_date = fields.Date.to_date(sale_order_id.date_order)
                
                tax_ids = move_line_id._get_computed_taxes()
                tax_ids = fiscal_position_id.map_tax(tax_ids._origin)
                
                vals = {
                    'product_id': move_line_id.product_id.id,
                    'quantity': quantity,
                    'product_uom_id': move_line_id.product_uom_id,
                    'price_unit': move_line_id.price_unit,
                    'discount': move_line_id.discount,
                    'account_id': move_line_id.account_id,
                    'tax_ids': [(6, 0, tax_ids.ids)],
                    'name': move_line_id.name,
                    'sale_date': sale_date, 
                }
                if move_id.move_type == "out_refund" and not out_refund:
                    vals['price_unit'] = -(move_line_id.price_unit)
                invoice_vals['invoice_line_ids'].append((0, 0, vals))
                
                # We decrease the max quantity allowed with the quantity invoiced
                if move_line_id.product_id.id in invoiceable_product_qty_max:
                    invoiceable_product_qty_max[move_line_id.product_id.id] = invoiceable_product_qty_max[move_line_id.product_id.id] - quantity
            move_id.button_draft()
        
        new_account_move_id = AccountMove.sudo().create(invoice_vals)

        return new_account_move_id
