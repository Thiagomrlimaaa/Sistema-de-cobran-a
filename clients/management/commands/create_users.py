from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Cria usuários jeff e thiago com senha 1'

    def handle(self, *args, **options):
        User = get_user_model()

        # Criar usuário jeff
        if not User.objects.filter(username='jeff').exists():
            User.objects.create_user('jeff', password='1')
            self.stdout.write(self.style.SUCCESS('✅ Usuário "jeff" criado com sucesso!'))
        else:
            user = User.objects.get(username='jeff')
            user.set_password('1')
            user.save()
            self.stdout.write(self.style.SUCCESS('✅ Senha do usuário "jeff" atualizada!'))

        # Criar usuário thiago
        if not User.objects.filter(username='thiago').exists():
            User.objects.create_user('thiago', password='1')
            self.stdout.write(self.style.SUCCESS('✅ Usuário "thiago" criado com sucesso!'))
        else:
            user = User.objects.get(username='thiago')
            user.set_password('1')
            user.save()
            self.stdout.write(self.style.SUCCESS('✅ Senha do usuário "thiago" atualizada!'))

        self.stdout.write(self.style.SUCCESS('\n🎉 Processo concluído!'))
        self.stdout.write('Usuários disponíveis:')
        self.stdout.write('  - jeff / senha: 1')
        self.stdout.write('  - thiago / senha: 1')

