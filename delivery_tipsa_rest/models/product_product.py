from odoo import fields, models
from .TipsaAPI import TipsaAPI


class ProductProduct(models.Model):
    _inherit = 'product.product'

    tipsa_qty_available = fields.Float(
        string='Tipsa stock',
        help='Quantity available for Tipsa',
    )

    reference_in_tipsa = fields.Boolean(
        string='Referencia creada en Tipsa')


    def update_qty_from_tipsa(self):
        self.ensure_one()
        carrier = self.env['delivery.carrier'].search([('delivery_type', '=', 'tipsa')],limit=1)
        if not carrier:
            return False
        url = carrier.tipsa_endpoint_url
        token = carrier.tipsa_token

        tipsa_api = TipsaAPI(url, token)
        response = tipsa_api.get_request('api/v3/stock')
        stock_data = response.json()
        filtered_list = [d for d in stock_data if d['reference'] == self.default_code]
        if filtered_list:
            self.tipsa_qty_available = float(filtered_list[0]['quantity'])

        self.message_post(body=str(response.__dict__))

    def cron_update_qty_from_tipsa(self):
        carrier = self.env['delivery.carrier'].search([
            ('delivery_type', '=', 'tipsa')], limit=1)
        if not carrier:
            return False
        url = carrier.tipsa_endpoint_url
        token = carrier.tipsa_token
        tipsa_api = TipsaAPI(url, token)
        response = tipsa_api.get_request('api/v3/stock')
        stock_data = response.json()
        for stock in stock_data:
            product = self.env['product.product'].search([('default_code', '=', stock['reference'])])
            if product:
                product.tipsa_qty_available = float(stock['quantity'])
                product.reference_in_tipsa = True



    def get_tipsa_references(self):
        # No funciona la respuesta de momento
        carrier = self.env['delivery.carrier'].search([
            ('delivery_type', '=', 'tipsa')], limit=1)
        if not carrier:
            return False
        url = carrier.tipsa_endpoint_url
        token = carrier.tipsa_token
        tipsa_api = TipsaAPI(url, token)
        response = tipsa_api.get_request('api/v3/references')

    def cron_create_tipsa_reference(self):
        products = self.env['product.product'].search([
            ('type', '=', 'product'),
            ('sale_ok', '=', True),
            ('website_published', '=', True),
            ('reference_in_tipsa', '=', False),
            ('default_code', '!=', False),
            ])
        for product in products:
            product.create_tipsa_reference()

    def create_tipsa_reference(self):
        lines = []
        carrier = self.env['delivery.carrier'].search([
            ('delivery_type', '=', 'tipsa')], limit=1)
        if not carrier:
            return False
        url = carrier.tipsa_endpoint_url
        token = carrier.tipsa_token
        tipsa_api = TipsaAPI(url, token)
        line_data = {
            "reference": self.default_code,
            "description": self.name,
            "warehouse": "CHESTE"
        }
        lines.append(line_data)
        response = tipsa_api.send_request('api/v3/references', lines)
        self.message_post(body=str(response.__dict__))
        if response.status_code == 200:
            self.write({'reference_in_tipsa': True})
