from django.db import migrations


class Migration(migrations.Migration):
    """
    products_product is already fully altered to new schema.
    This migration only creates the missing products_order table.
    """

    dependencies = [
        ('products', '0002_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE TABLE IF NOT EXISTS products_order (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    quantity DECIMAL(10,2) NOT NULL,
                    total_price DECIMAL(10,2) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    ordered_at DATETIME(6) NOT NULL,
                    customer_id INT NOT NULL,
                    product_id BIGINT NOT NULL,
                    CONSTRAINT fk_order_customer FOREIGN KEY (customer_id) REFERENCES auth_user(id),
                    CONSTRAINT fk_order_product FOREIGN KEY (product_id) REFERENCES products_product(id)
                ) ENGINE=InnoDB;
            """,
            reverse_sql="DROP TABLE IF EXISTS products_order;",
        ),
    ]
