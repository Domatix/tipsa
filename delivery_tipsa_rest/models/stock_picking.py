from odoo import fields, models, api
from .TipsaAPI import TipsaAPI
import json
import logging
_logger = logging.getLogger(__name__)

TIPSA_STATUS_TRANSLATIONS = {
    'IN PREPARATION': 'En preparación',
    'SENT': 'Enviado',
}

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    tipsa_last_request = fields.Text(
        string='Last Tipsa request',
        help='Used for issues debugging',
        copy=False,
        readonly=True,
    )
    tipsa_last_response = fields.Text(
        string='Last Tipsa response',
        help='Used for issues debugging',
        copy=False,
        readonly=True,
    )
    tipsa_picking_reference = fields.Char(
        string='Picking number for Tipsa webservices',
        readonly=True,
        copy=False,
    )

    tipsa_status = fields.Char(
        string='Estado Tipsa')

    def get_tipsa_tracking_number(self):
        carrier = self.carrier_id
        if carrier.delivery_type != 'tipsa' or not self.sale_id:
            return False
        url = carrier.tipsa_endpoint_url
        token = carrier.tipsa_token
        tipsa_api = TipsaAPI(url, token)
        endpoint = 'api/v3/deliveryOrder?id=' + self.sale_id.name
        response = tipsa_api.get_request(endpoint)
        if response.status_code != 200:
            # Hubo un error
            self.message_post(body=str(response.__dict__))
            return False

        # self.carrier_tracking_ref = response.get('expeditionNumber')
        data = json.loads(response._content.decode('utf-8'))
        if self.tipsa_status:
            if self.tipsa_status == data.get('status'):
                return True
        self.carrier_tracking_ref = data.get('expeditionNumber')
        self.tipsa_status = data.get('status')
        translated_status = TIPSA_STATUS_TRANSLATIONS.get(self.tipsa_status, self.tipsa_status)
        self.message_post(body=str(response.__dict__))
        if self.sale_id:
            body = f'El pedido ha cambiado al estado "{translated_status}".'
            if self.carrier_tracking_ref:
                body += f' El nº de seguimiento es {self.carrier_tracking_ref}'
            self.sale_id.message_post(body=body)

    @api.model
    def tipsa_tracking_number_cron(self):
        active_ids = self.env['stock.picking'].search([
            ('state', '=', 'done'),
            ('picking_type_id', '=', 2),
            ('tipsa_last_request', '!=', False),
            ('tipsa_status', '!=', 'SENT')])
        if not active_ids:
            return True
        _logger.info(f'Obteniendo estado y tracking de {str(active_ids)}')
        for picking in active_ids:
            picking.get_tipsa_tracking_number()

    def picking_auto_validate_cron(self):
        active_ids = self.env['stock.picking'].search([
            ('state', '=', 'assigned'),
            ('picking_type_id', '=', 2),
            # ('manual_picking_validation', '=', False),
            ('carrier_id.delivery_type', '=', 'tipsa')])
        if not active_ids:
            return True
        for line in active_ids.move_lines:
            line._set_quantity_done(line.product_uom_qty)
        active_ids._action_done()
