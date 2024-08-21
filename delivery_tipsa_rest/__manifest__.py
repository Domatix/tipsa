{
    'name': 'Delivery Tipsa Rest',
    'summary': 'Integrate Tipsa API Rest webservice',
    'category': 'Delivery',
    'version': '15.0.1.0.0',
    'author': 'Domatix',
    'website': 'https://domatix.com',
    'license': 'AGPL-3',
    'depends': [
        'delivery',
        'delivery_price_method',
    ],
    'data': [
        'views/delivery_carrier_views.xml',
        'views/stock_picking_views.xml',
        'views/product_product.xml',
        'data/ir_cron.xml'
    ],
}
