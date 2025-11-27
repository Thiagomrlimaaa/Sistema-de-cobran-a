from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Cria superusuários jeff e thiago com senha 1'

    def handle(self, *args, **options):
        User = get_user_model()

        # Criar superusuário jeff
        if not User.objects.filter(username='jeff').exists():
            User.objects.create_superuser('jeff', password='1')
            self.stdout.write(self.style.SUCCESS('✅ Superusuário "jeff" criado com sucesso!'))
        else:
            user = User.objects.get(username='jeff')
            user.set_password('1')
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(self.style.SUCCESS('✅ Senha do superusuário "jeff" atualizada!'))

        # Criar superusuário thiago
        if not User.objects.filter(username='thiago').exists():
            User.objects.create_superuser('thiago', password='1')
            self.stdout.write(self.style.SUCCESS('✅ Superusuário "thiago" criado com sucesso!'))
        else:
            user = User.objects.get(username='thiago')
            user.set_password('1')
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(self.style.SUCCESS('✅ Senha do superusuário "thiago" atualizada!'))

        self.stdout.write(self.style.SUCCESS('\n🎉 Processo concluído!'))
        self.stdout.write('Superusuários disponíveis:')
        self.stdout.write('  - jeff / senha: 1')
        self.stdout.write('  - thiago / senha: 1')

