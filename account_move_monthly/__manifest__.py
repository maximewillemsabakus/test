# -*- coding: utf-8 -*-
{
    'name': "Generate Monthly Invoices",
    "author" : "ABAKUS IT-SOLUTIONS",
    'website': "http://www.abakusitsolutions.eu",
    'category': 'Account',
    'version': '15.0.0',
    'license': 'LGPL-3',
    'application': True,
    'depends': [
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        
        'views/account_move_views.xml',
        'views/res_partner_views.xml',
        
        'wizards/account_move_generation_views.xml',
        
        'reports/account_move_report.xml',
    ],
    'installable': True
}
