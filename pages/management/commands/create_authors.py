from django.core.management.base import BaseCommand
from pages.models import Article, Author


class Command(BaseCommand):
    help = 'Mavjud maqolalar uchun Author profillarini yaratish'

    def handle(self, *args, **options):
        articles = Article.objects.filter(author__isnull=True)
        created_count = 0
        updated_count = 0
        
        for article in articles:
            # Author topish yoki yaratish
            author, created = Author.objects.get_or_create(
                full_name=article.author_name,
                email=article.author_email,
                phone=article.author_phone,
                defaults={
                    'workplace': article.author_workplace,
                    'academic_degree': article.author_degree
                }
            )
            
            # Article ga author bog'lash
            article.author = author
            article.save()
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✅ Yangi muallif yaratildi: {author.full_name}'))
            else:
                updated_count += 1
            
            # Statistikani yangilash
            author.update_statistics()
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Bajarildi!'))
        self.stdout.write(f'   Yangi mualliflar: {created_count}')
        self.stdout.write(f'   Yangilangan maqolalar: {len(articles)}')
