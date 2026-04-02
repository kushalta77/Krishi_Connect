from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_alter_product_create_order'),
    ]

    operations = [
        # Update Product model
        migrations.AddField(
            model_name='product',
            name='unit',
            field=models.CharField(
                choices=[('kg', 'Kilogram'), ('quintal', 'Quintal'), ('box', 'Box'), ('crate', 'Crate')],
                default='kg',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='min_order_qty',
            field=models.DecimalField(decimal_places=2, default=5, max_digits=10),
        ),
        migrations.AddField(
            model_name='product',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.RenameField(
            model_name='product',
            old_name='price_per_kg',
            new_name='price_per_unit',
        ),
        # Update Order model - add new fields
        migrations.AddField(
            model_name='order',
            name='delivery_address',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='order',
            name='phone_number',
            field=models.CharField(default='', max_length=15),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_mode',
            field=models.CharField(
                choices=[('delivery', 'Home Delivery'), ('pickup', 'Pickup from Farm')],
                default='delivery',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='accepted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='shipped_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='delivered_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='farmer_notes',
            field=models.TextField(blank=True),
        ),
        # Update status choices
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending - Awaiting Farmer Response'),
                    ('accepted', 'Accepted - Order Confirmed'),
                    ('rejected', 'Rejected - Order Cancelled'),
                    ('shipped', 'Shipped - On the way'),
                    ('delivered', 'Delivered - Completed'),
                    ('cancelled', 'Cancelled - By Customer'),
                ],
                default='pending',
                max_length=20
            ),
        ),
    ]
