# Generated manually for Click payment sessions

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0022_article_doi'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArticlePaymentSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(db_index=True, max_length=64, unique=True, verbose_name='Token')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name="To'lov miqdori")),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Kutilmoqda'),
                        ('paid', "To'langan"),
                        ('expired', 'Muddati tugagan'),
                        ('cancelled', 'Bekor qilindi'),
                    ],
                    default='pending',
                    max_length=20,
                    verbose_name='Holat',
                )),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan')),
                ('paid_at', models.DateTimeField(blank=True, null=True, verbose_name="To'langan vaqt")),
                ('transaction_id', models.CharField(blank=True, max_length=200, verbose_name='Tranzaksiya ID')),
                ('click_payment_id', models.CharField(blank=True, max_length=200, verbose_name='Click payment ID')),
                ('article', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='payment_sessions',
                    to='pages.article',
                    verbose_name='Maqola',
                )),
            ],
            options={
                'verbose_name': "To'lov sessiyasi",
                'verbose_name_plural': "To'lov sessiyalari",
                'ordering': ['-created_at'],
            },
        ),
    ]
