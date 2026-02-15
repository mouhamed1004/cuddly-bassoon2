from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Liste tous les comptes admin (superutilisateurs et staff)'

    def handle(self, *args, **options):
        admins = User.objects.filter(is_superuser=True) | User.objects.filter(is_staff=True)
        admins = admins.distinct().order_by('username')

        if not admins.exists():
            self.stdout.write(self.style.WARNING('Aucun admin trouvé.'))
            return

        self.stdout.write(self.style.SUCCESS(f'\n=== {admins.count()} admin(s) trouvé(s) ===\n'))

        for u in admins:
            roles = []
            if u.is_superuser:
                roles.append('superuser')
            if u.is_staff:
                roles.append('staff')
            roles_str = ', '.join(roles)
            self.stdout.write(
                f"  • {u.username}\n"
                f"    Email: {u.email or '(vide)'}\n"
                f"    Rôles: {roles_str}\n"
                f"    Créé le: {u.date_joined.strftime('%Y-%m-%d %H:%M')}\n"
            )

        self.stdout.write(self.style.WARNING(
            '\nNote: Les mots de passe sont hachés et ne peuvent pas être récupérés. '
            'Pour réinitialiser un mot de passe: python manage.py changepassword <username>\n'
        ))
