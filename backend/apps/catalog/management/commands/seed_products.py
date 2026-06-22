from django.core.management.base import BaseCommand
from apps.tenants.models import Store
from apps.catalog.models import Category, Brand, Product, ProductVariant, ProductImage
from apps.inventory.models import Inventory

# Unsplash hardware product images (stable URLs)
IMAGES = {
    'brass_tap':     'https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=800',
    'pipe_fitting':  'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800',
    'angle_valve':   'https://images.unsplash.com/photo-1504328345606-18bbc8c9d7d1?w=800',
    'shower':        'https://images.unsplash.com/photo-1552321554-5fefe8c9ef14?w=800',
    'basin_mixer':   'https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=800',
    'pvc_pipe':      'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800',
    'cpvc_pipe':     'https://images.unsplash.com/photo-1504328345606-18bbc8c9d7d1?w=800',
    'gate_valve':    'https://images.unsplash.com/photo-1504328345606-18bbc8c9d7d1?w=800',
    'ball_valve':    'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800',
    'wc_seat':       'https://images.unsplash.com/photo-1552321554-5fefe8c9ef14?w=800',
    'wash_basin':    'https://images.unsplash.com/photo-1552321554-5fefe8c9ef14?w=800',
    'exhaust_fan':   'https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=800',
    'pprc_pipe':     'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800',
    'elbow':         'https://images.unsplash.com/photo-1504328345606-18bbc8c9d7d1?w=800',
    'wire':          'https://images.unsplash.com/photo-1504328345606-18bbc8c9d7d1?w=800',
}

SEED = [
    {
        'category': 'Taps & Faucets',
        'brand': 'Jaquar',
        'name': 'Brass Pillar Tap',
        'slug': 'brass-pillar-tap',
        'description': 'Heavy-duty brass pillar tap for wash basins. Chrome-plated finish, quarter-turn ceramic disc.',
        'specifications': {'material': 'Brass', 'finish': 'Chrome', 'connection': '1/2 inch BSP'},
        'image': 'brass_tap',
        'variants': [
            {'name': '15mm', 'sku': 'TAP-BR-15', 'price': 650, 'qty': 24},
            {'name': '20mm', 'sku': 'TAP-BR-20', 'price': 850, 'qty': 16},
        ],
    },
    {
        'category': 'Taps & Faucets',
        'brand': 'Jaquar',
        'name': 'Single Lever Basin Mixer',
        'slug': 'single-lever-basin-mixer',
        'description': 'Single-lever basin mixer with pop-up drain. Ceramic disc cartridge for drip-free operation.',
        'specifications': {'material': 'Brass', 'finish': 'Chrome', 'spout_length': '120mm'},
        'image': 'basin_mixer',
        'variants': [
            {'name': 'Standard', 'sku': 'MIX-BAS-STD', 'price': 2200, 'sale_price': 1899, 'qty': 12},
            {'name': 'With Overhead Shower', 'sku': 'MIX-BAS-SHW', 'price': 3100, 'qty': 8},
        ],
    },
    {
        'category': 'Taps & Faucets',
        'brand': 'Cera',
        'name': 'Rain Shower Set',
        'slug': 'rain-shower-set',
        'description': '8-inch overhead rain shower with arm and flange. Stainless steel with anti-clog nozzles.',
        'specifications': {'size': '8 inch', 'material': 'SS 304', 'nozzles': '64'},
        'image': 'shower',
        'variants': [
            {'name': 'Chrome', 'sku': 'SHW-RAIN-CR', 'price': 1850, 'qty': 20},
            {'name': 'Matt Black', 'sku': 'SHW-RAIN-MB', 'price': 2200, 'sale_price': 1999, 'qty': 10},
        ],
    },
    {
        'category': 'Pipes & Fittings',
        'brand': 'Supreme',
        'name': 'uPVC Pressure Pipe',
        'slug': 'upvc-pressure-pipe',
        'description': 'uPVC pressure pipe for cold water supply. ISI marked, suitable for agricultural and plumbing use.',
        'specifications': {'standard': 'IS 4985', 'pressure_rating': 'Class 4', 'length': '6 metres'},
        'image': 'pvc_pipe',
        'variants': [
            {'name': '1/2 inch (15mm)', 'sku': 'PVC-UP-15', 'price': 180, 'qty': 100},
            {'name': '3/4 inch (20mm)', 'sku': 'PVC-UP-20', 'price': 240, 'qty': 80},
            {'name': '1 inch (25mm)',   'sku': 'PVC-UP-25', 'price': 320, 'qty': 60},
        ],
    },
    {
        'category': 'Pipes & Fittings',
        'brand': 'Ashirvad',
        'name': 'CPVC Hot & Cold Pipe',
        'slug': 'cpvc-hot-cold-pipe',
        'description': 'CPVC pipe for hot and cold water. Rated to 93°C. Suitable for solar and geyser connections.',
        'specifications': {'standard': 'IS 15778', 'temp_rating': '93°C', 'length': '3 metres'},
        'image': 'cpvc_pipe',
        'variants': [
            {'name': '15mm', 'sku': 'CPVC-15', 'price': 145, 'qty': 120},
            {'name': '20mm', 'sku': 'CPVC-20', 'price': 195, 'qty': 90},
            {'name': '25mm', 'sku': 'CPVC-25', 'price': 270, 'qty': 50},
        ],
    },
    {
        'category': 'Pipes & Fittings',
        'brand': 'Finolex',
        'name': 'PPRC Pipe',
        'slug': 'pprc-pipe',
        'description': 'Polypropylene random copolymer pipe. Suitable for hot and cold water, heating systems.',
        'specifications': {'standard': 'IS 15801', 'pressure': 'PN 20', 'length': '4 metres'},
        'image': 'pprc_pipe',
        'variants': [
            {'name': '20mm PN20', 'sku': 'PPRC-20-PN20', 'price': 220, 'qty': 75},
            {'name': '25mm PN20', 'sku': 'PPRC-25-PN20', 'price': 310, 'qty': 60},
            {'name': '32mm PN20', 'sku': 'PPRC-32-PN20', 'price': 420, 'qty': 40},
        ],
    },
    {
        'category': 'Pipes & Fittings',
        'brand': 'Supreme',
        'name': 'uPVC Elbow 90°',
        'slug': 'upvc-elbow-90',
        'description': 'uPVC 90-degree elbow fitting for pressure pipe systems. Solvent cement joint.',
        'specifications': {'angle': '90°', 'joint': 'Solvent cement', 'standard': 'IS 7834'},
        'image': 'elbow',
        'variants': [
            {'name': '15mm', 'sku': 'ELB-90-15', 'price': 18,  'qty': 200},
            {'name': '20mm', 'sku': 'ELB-90-20', 'price': 24,  'qty': 180},
            {'name': '25mm', 'sku': 'ELB-90-25', 'price': 35,  'qty': 150},
        ],
    },
    {
        'category': 'Valves',
        'brand': 'Zoloto',
        'name': 'Gun Metal Gate Valve',
        'slug': 'gunmetal-gate-valve',
        'description': 'ISI-marked gun metal gate valve with screwed ends. Suitable for water, steam, and oil.',
        'specifications': {'material': 'Gun Metal', 'standard': 'IS 778', 'ends': 'Screwed BSP'},
        'image': 'gate_valve',
        'variants': [
            {'name': '15mm (1/2")', 'sku': 'GV-GM-15', 'price': 280,  'qty': 40},
            {'name': '20mm (3/4")', 'sku': 'GV-GM-20', 'price': 380,  'qty': 30},
            {'name': '25mm (1")',   'sku': 'GV-GM-25', 'price': 520,  'qty': 20},
            {'name': '40mm (1.5")', 'sku': 'GV-GM-40', 'price': 980,  'qty': 10},
        ],
    },
    {
        'category': 'Valves',
        'brand': 'Zoloto',
        'name': 'Brass Ball Valve',
        'slug': 'brass-ball-valve',
        'description': 'Full bore brass ball valve with lever handle. Quarter-turn operation. PTFE seat.',
        'specifications': {'material': 'Brass', 'bore': 'Full bore', 'seat': 'PTFE'},
        'image': 'ball_valve',
        'variants': [
            {'name': '15mm', 'sku': 'BV-BR-15', 'price': 220,  'qty': 50},
            {'name': '20mm', 'sku': 'BV-BR-20', 'price': 310,  'qty': 35},
            {'name': '25mm', 'sku': 'BV-BR-25', 'price': 450,  'qty': 25},
        ],
    },
    {
        'category': 'Valves',
        'brand': 'Jaquar',
        'name': 'Angle Valve with Wall Flange',
        'slug': 'angle-valve-wall-flange',
        'description': 'Quarter-turn angle valve for WC and wash basin connections. With escutcheon plate.',
        'specifications': {'material': 'Brass', 'finish': 'Chrome', 'size': '15mm'},
        'image': 'angle_valve',
        'variants': [
            {'name': 'Chrome',    'sku': 'AV-CH-15', 'price': 350,  'qty': 60},
            {'name': 'Gold PVD',  'sku': 'AV-GD-15', 'price': 550,  'qty': 20},
        ],
    },
    {
        'category': 'Sanitary Ware',
        'brand': 'Cera',
        'name': 'Wall-Hung WC with Soft Close Seat',
        'slug': 'wall-hung-wc-soft-close',
        'description': 'Wall-hung ceramic WC with dual-flush cistern and soft-close UF seat. Water saving: 3/6L flush.',
        'specifications': {'flush': 'Dual 3/6L', 'installation': 'Wall-hung', 'material': 'Vitreous China'},
        'image': 'wc_seat',
        'variants': [
            {'name': 'White', 'sku': 'WC-WH-WHT', 'price': 14500, 'sale_price': 12999, 'qty': 8},
        ],
    },
    {
        'category': 'Sanitary Ware',
        'brand': 'Hindware',
        'name': 'Pedestal Wash Basin',
        'slug': 'pedestal-wash-basin',
        'description': 'Full pedestal wash basin in vitreous china. Single tap hole. Includes mounting hardware.',
        'specifications': {'material': 'Vitreous China', 'tap_holes': 1, 'size': '495×390mm'},
        'image': 'wash_basin',
        'variants': [
            {'name': 'White', 'sku': 'WB-PED-WHT', 'price': 5200,  'qty': 12},
            {'name': 'Ivory', 'sku': 'WB-PED-IVR', 'price': 5400,  'qty': 6},
        ],
    },
    {
        'category': 'Electrical',
        'brand': 'Polycab',
        'name': 'FR House Wire',
        'slug': 'fr-house-wire',
        'description': 'Flame retardant PVC insulated single-core copper wire. ISI marked. 90m coil.',
        'specifications': {'insulation': 'FR PVC', 'conductor': 'Copper', 'standard': 'IS 694', 'length': '90m'},
        'image': 'wire',
        'variants': [
            {'name': '1.5 sq mm Red',   'sku': 'WIRE-15-R',  'price': 1350, 'qty': 40},
            {'name': '1.5 sq mm Black', 'sku': 'WIRE-15-B',  'price': 1350, 'qty': 40},
            {'name': '2.5 sq mm Red',   'sku': 'WIRE-25-R',  'price': 2100, 'sale_price': 1949, 'qty': 30},
            {'name': '2.5 sq mm Black', 'sku': 'WIRE-25-B',  'price': 2100, 'sale_price': 1949, 'qty': 30},
            {'name': '4 sq mm Red',     'sku': 'WIRE-40-R',  'price': 3200, 'qty': 20},
        ],
    },
    {
        'category': 'Electrical',
        'brand': 'Havells',
        'name': 'Exhaust Fan 6"',
        'slug': 'exhaust-fan-6-inch',
        'description': 'Ventilation exhaust fan for bathrooms and kitchens. Rust-proof ABS body, low noise motor.',
        'specifications': {'size': '6 inch', 'power': '18W', 'airflow': '170 m³/hr', 'noise': '35 dB'},
        'image': 'exhaust_fan',
        'variants': [
            {'name': 'White', 'sku': 'EXF-6-WHT', 'price': 780,  'qty': 25},
            {'name': 'Ivory', 'sku': 'EXF-6-IVR', 'price': 780,  'qty': 15},
        ],
    },
    {
        'category': 'Pipes & Fittings',
        'brand': 'Ashirvad',
        'name': 'CPVC Elbow 90°',
        'slug': 'cpvc-elbow-90',
        'description': 'CPVC 90-degree elbow for hot and cold water systems. Solvent cement socket joint.',
        'specifications': {'angle': '90°', 'joint': 'Solvent cement', 'temp_rating': '93°C'},
        'image': 'elbow',
        'variants': [
            {'name': '15mm', 'sku': 'CELB-15', 'price': 22,  'qty': 300},
            {'name': '20mm', 'sku': 'CELB-20', 'price': 30,  'qty': 250},
            {'name': '25mm', 'sku': 'CELB-25', 'price': 42,  'qty': 180},
        ],
    },
]

CATEGORIES = ['Taps & Faucets', 'Pipes & Fittings', 'Valves', 'Sanitary Ware', 'Electrical']
BRANDS = ['Jaquar', 'Cera', 'Supreme', 'Ashirvad', 'Finolex', 'Zoloto', 'Hindware', 'Polycab', 'Havells']


class Command(BaseCommand):
    help = 'Seed sample hardware & sanitary products'

    def handle(self, *args, **options):
        store = Store.objects.filter(is_active=True).first()
        if not store:
            self.stderr.write('No active store found. Run: python manage.py create_store first.')
            return

        self.stdout.write(f'Seeding into store: {store.name}')

        # Categories
        cats = {}
        for name in CATEGORIES:
            from django.utils.text import slugify
            obj, created = Category.objects.get_or_create(
                tenant=store, slug=slugify(name),
                defaults={'name': name, 'is_active': True}
            )
            cats[name] = obj
            if created:
                self.stdout.write(f'  + category: {name}')

        # Brands
        brands = {}
        for name in BRANDS:
            from django.utils.text import slugify
            obj, created = Brand.objects.get_or_create(
                tenant=store, slug=slugify(name),
                defaults={'name': name, 'is_active': True}
            )
            brands[name] = obj
            if created:
                self.stdout.write(f'  + brand: {name}')

        # Products
        for p in SEED:
            product, created = Product.objects.get_or_create(
                tenant=store, slug=p['slug'],
                defaults={
                    'name': p['name'],
                    'category': cats[p['category']],
                    'brand': brands[p['brand']],
                    'description': p['description'],
                    'specifications': p['specifications'],
                    'is_active': True,
                }
            )
            if not created:
                self.stdout.write(f'  ~ skip (exists): {p["name"]}')
                continue

            self.stdout.write(f'  + product: {p["name"]}')

            # Image
            image_url = IMAGES.get(p['image'], '')
            if image_url:
                ProductImage.objects.create(product=product, image_url=image_url, sort_order=0)

            # Variants + Inventory
            for v in p['variants']:
                variant = ProductVariant.objects.create(
                    product=product,
                    name=v['name'],
                    sku=v['sku'],
                    price=v['price'],
                    sale_price=v.get('sale_price'),
                    is_active=True,
                )
                Inventory.objects.create(
                    tenant=store,
                    variant=variant,
                    available_qty=v['qty'],
                )

        self.stdout.write(self.style.SUCCESS('Done.'))
