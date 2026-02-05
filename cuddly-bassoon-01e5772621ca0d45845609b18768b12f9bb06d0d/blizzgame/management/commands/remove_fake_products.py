from django.core.management.base import BaseCommand
from blizzgame.models import Product, ProductVariant

class Command(BaseCommand):
    help = 'Remove fake products from the database'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Removing fake products...'))

        # List of fake products to remove
        fake_products = [
            'Casque Gaming RGB',
            'Power Bank Gaming 20000mAh', 
            'Gants Gaming Pro',
            'Clavier Mécanique RGB'
        ]

        removed_count = 0
        for product_name in fake_products:
            try:
                products = Product.objects.filter(name=product_name)
                if products.exists():
                    # Remove associated variants first
                    for product in products:
                        variants_count = ProductVariant.objects.filter(product=product).count()
                        ProductVariant.objects.filter(product=product).delete()
                        if variants_count > 0:
                            self.stdout.write(f'Removed {variants_count} variants for {product.name}')
                    
                    # Remove the products
                    count = products.count()
                    products.delete()
                    removed_count += count
                    self.stdout.write(f'Removed product: {product_name} ({count} instances)')
                else:
                    self.stdout.write(f'Product not found: {product_name}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error removing {product_name}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully removed {removed_count} fake products!'))
