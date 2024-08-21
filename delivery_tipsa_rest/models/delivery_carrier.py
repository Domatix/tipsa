import base64
from datetime import datetime, timedelta
from unicodedata import normalize
from odoo import _, exceptions, fields, models
from .TipsaAPI import TipsaAPI
import logging
_logger = logging.getLogger(__name__)


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(
        selection_add=[('tipsa', 'Tipsa')],
        ondelete={"tipsa": "set default"}
    )

    tipsa_agency_code = fields.Char(
        string='Agency code',
    )
    tipsa_token = fields.Char(
        string='Access token',
    )

    tipsa_service_code = fields.Selection(
        selection=[
            ('48', '48'),
            ('92', '92'),
        ],
        default='48',
        string='Tipsa service code',
    )

    tipsa_endpoint_url = fields.Char(
        string='URL webservice',
        default='http://asmensga.tlsi.es:8088',
    )

    def tipsa_send_shipping(self, pickings):
        return [self.tipsa_create_shipping(p) for p in pickings]

    def tipsa_create_shipping(self, picking):
        self.ensure_one()
        if self.env.context.get('delivery_sent'):
            return {
                'tracking_number': False,
                'exact_price': 0,
            }
        data = self.prepare_data(picking)
        url = self.tipsa_endpoint_url
        token = self.tipsa_token
        tipsa_api = TipsaAPI(url, token)
        response = tipsa_api.send_request('api/v3/deliveryOrder', data)
        res = {
            'tracking_number': picking.carrier_tracking_ref,
            'exact_price': 0,
        }
        picking.write({
            'tipsa_last_request': fields.Datetime.now(),
            'tipsa_last_response': fields.Datetime.now(),
            # 'tracking_number': response.get('tracking_number')
        })

        if response.status_code != 200:
            # Hubo un error
            error_response = str(response.__dict__)
            _logger.info(f'{data}')
            _logger.info(f'{error_response}')
            self.message_post(body='Error al enviar el envío a Tipsa.')
        return res

    def prepare_data(self, picking):
        data = {
            "id": picking.sale_id.name,
            "address": self.prepare_address(picking),
            "invoicingAddress": self.prepare_invoicing_address(picking),
            "customer": self.prepare_customer(picking),
            # "type": 'normal',
            "order": picking.sale_id.name,
            "customerOrder": picking.sale_id.name,
            "agency": "Tipsa",
            # "priority": "",
            "preparationDate": datetime.today().date().strftime('%d-%m-%Y'),
            "remarks": picking.note if picking.note else "",
            "lines": self.prepare_lines(picking),
            # "extra1": "...",
            # "extra2": "...",
            # "extraShow": "...",
            # "extra": self.prepare_extra(),
        }
        return data

    def prepare_address(self, picking):
        return {
            "address": picking.partner_id.street or "",
            "cp": picking.partner_id.zip or "",
            "city": picking.partner_id.city or "",
            "country": picking.partner_id.country_id.name or "",
            # "attention_of": "...",
            # "code": "...",
        }

    def prepare_invoicing_address(self, picking):
        return {
            "address": picking.partner_id.street or "",
            "cp": picking.partner_id.zip or "",
            "city": picking.partner_id.city or "",
            "country": picking.partner_id.country_id.name or "",
            # "attention_of": "...",
            # "code": "...",
        }

    def prepare_customer(self, picking):
        return {
            "name": picking.partner_id.name or "",
            # "code": "...",
            "email": picking.partner_id.email or "",
            "phone": picking.partner_id.phone or picking.partner_id.mobile or "",
        }

    def prepare_lines(self, picking):
        lines = []
        for line in picking.move_line_ids:
            line_data = {
                "id": str(line.id),
                "reference": line.product_id.default_code,
                "description": line.product_id.name,
                "quantity": str(line.qty_done),
                "weight": str(line.product_id.weight * line.qty_done),
                # "customerReference": "",
                # "customerDescription": "",
                # "batchNumber": "",
                # "statusCode": ""
            }
            lines.append(line_data)
        return lines

    def prepare_extra(self):
        extra = []
        extra_data = {
            "field": "",  # Este valor deberá ser reemplazado por el campo correspondiente en tu modelo
            "value": ""  # Este valor deberá ser reemplazado por el campo correspondiente en tu modelo
        }
        extra.append(extra_data)
        return extra
